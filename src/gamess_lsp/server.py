"""GAMESS Language Server Protocol implementation."""

import logging
import os
import re
from collections import OrderedDict
from difflib import get_close_matches
from typing import Any, List, Optional
from urllib.parse import urlparse

from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    DefinitionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentFormattingParams,
    DocumentSymbolParams,
    Hover,
    HoverParams,
    InsertTextFormat,
    Location,
    OptionalVersionedTextDocumentIdentifier,
    Position,
    Range,
    ReferenceParams,
    RenameParams,
    SymbolInformation,
    SymbolKind,
    TextDocumentEdit,
    TextEdit,
    WorkspaceEdit,
    WorkspaceSymbolParams,
)
from pygls.server import LanguageServer
from pygls.workspace import Document

from .features.diagnostic import DiagnosticProvider
from .features.lint import LintProvider
from .keywords import GAMESS_GROUPS, GAMESS_KEYWORDS
from .parser import GAMESSParser
from .tokenizer import tokenize_line
from .validator import validate_semantics

# Security: Use WARNING as default log level to prevent information disclosure
LOG_LEVEL = os.getenv("GAMESS_LSP_LOG_LEVEL", "WARNING")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

server = LanguageServer("gamess-lsp", "0.1.0")

# Resource limits for DoS protection
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LINES = 100000
MAX_CACHE_SIZE = 100
MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB


class DocumentCache:
    """LRU cache with URI validation and size limits."""

    def __init__(self, max_size: int = MAX_CACHE_SIZE, max_content_size: int = MAX_CONTENT_SIZE):
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._max_size = max_size
        self._max_content_size = max_content_size

    def _is_valid_uri(self, uri: str) -> bool:
        """Validate that URI is a legitimate document URI."""
        try:
            parsed = urlparse(uri)
            # Only accept file:// or untitled:// schemes, prevent path traversal
            return parsed.scheme in ("file", "untitled") and ".." not in parsed.path
        except Exception:
            return False

    def get(self, uri: str) -> Optional[str]:
        """Get content from cache."""
        return self._cache.get(uri)

    def set(self, uri: str, content: str) -> None:
        """Set content in cache with validation."""
        if not self._is_valid_uri(uri):
            logger.warning(f"Invalid URI rejected: {uri}")
            return
        if len(content) > self._max_content_size:
            logger.warning(f"Content too large for {uri}: {len(content)} bytes")
            return
        self._cache[uri] = content
        self._cache.move_to_end(uri)
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()

    def items(self):
        """Return cache items."""
        return self._cache.items()


# Create document cache instance
document_cache = DocumentCache()

# Create diagnostic provider instance
diagnostic_provider = DiagnosticProvider(server)
lint_provider = LintProvider(server)


def _is_valid_document_uri(uri: str) -> bool:
    """Validate that URI is a legitimate document URI."""
    try:
        parsed = urlparse(uri)
        return parsed.scheme in ("file", "untitled") and ".." not in parsed.path
    except Exception:
        return False


def _check_content_size(content: str, uri: str) -> Optional[List[Diagnostic]]:
    """Check content size and return error diagnostic if too large."""
    if len(content) > MAX_FILE_SIZE:
        logger.warning(f"File too large: {len(content)} bytes")
        return [
            Diagnostic(
                range=Range(
                    start=Position(line=0, character=0), end=Position(line=0, character=100)
                ),
                message=f"File exceeds maximum size of {MAX_FILE_SIZE} bytes",
                severity=DiagnosticSeverity.Error,
            )
        ]
    lines = content.split("\n")
    if len(lines) > MAX_LINES:
        logger.warning(f"File has too many lines: {len(lines)}")
        return [
            Diagnostic(
                range=Range(
                    start=Position(line=0, character=0), end=Position(line=0, character=100)
                ),
                message=f"File exceeds maximum line count of {MAX_LINES}",
                severity=DiagnosticSeverity.Error,
            )
        ]
    return None


def log_document_action(action: str, uri: str, content: Optional[str] = None) -> None:
    """Safely log document actions without exposing content."""
    # Only log the filename, not full path
    safe_uri = os.path.basename(uri) if uri else "unknown"
    logger.info(f"{action}: {safe_uri}")
    # Never log content at INFO level, only DEBUG and truncate
    if content and logger.isEnabledFor(logging.DEBUG):
        preview = content[:100].replace("\n", " ") + "..." if len(content) > 100 else content
        logger.debug(f"Content preview: {preview}")


# GAMESS snippet templates
GAMESS_SNIPPETS = {
    "water": {
        "label": "Water molecule",
        "documentation": "Water molecule geometry with DFT optimization",
        "insertText": r"""! Water molecule DFT calculation
 \$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$STATPT OPTTOL=0.0001 NSTEP=50 \$END
 \$DATA
Water molecule
Cnv 2

O     8.0   0.000000   0.000000   0.117489
H     1.0   0.000000   0.757210  -0.469957
 \$END""",
    },
    "dft-opt": {
        "label": "DFT optimization",
        "documentation": "Standard DFT geometry optimization template",
        "insertText": r"""! DFT geometry optimization
 \$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$STATPT OPTTOL=0.0001 NSTEP=50 \$END
 \$DATA
\${1:Molecule title}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
    "hf-sp": {
        "label": "Hartree-Fock single point",
        "documentation": "Hartree-Fock single point energy calculation",
        "insertText": r"""! HF single point energy
 \$CONTRL SCFTYP=RHF RUNTYP=ENERGY \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=STO NGAUSS=3 \$END
 \$DATA
\${1:Molecule title}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
    "mp2": {
        "label": "MP2 calculation",
        "documentation": "MP2 correlation energy calculation",
        "insertText": r"""! MP2 calculation
 \$CONTRL SCFTYP=RHF RUNTYP=ENERGY MPLEVL=2 \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$MP2 METHOD=2 \$END
 \$DATA
\${1:Molecule title}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
    "freq": {
        "label": "Frequency calculation",
        "documentation": "Vibrational frequency calculation",
        "insertText": r"""! Frequency calculation
 \$CONTRL SCFTYP=RHF RUNTYP=HESSIAN \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$FORCE METHOD=ANALYTIC \$END
 \$DATA
\${1:Molecule title}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
    "tddft": {
        "label": "TD-DFT calculation",
        "documentation": "Time-dependent DFT excited states calculation",
        "insertText": r"""! TD-DFT excited states
 \$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=ENERGY \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$TDDFT NSTATE=5 MULT=1 \$END
 \$DATA
\${1:Molecule title}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
    "ts-search": {
        "label": "Transition state search",
        "documentation": "Transition state optimization using SADDLE point calculation",
        "insertText": r"""! Transition state search
 \$CONTRL SCFTYP=RHF RUNTYP=SADPOINT \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$STATPT OPTTOL=0.0001 NSTEP=100 IFOLOW=1 HESS=CALC \$END
 \$DATA
\${1:Transition state}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
    "irc-calc": {
        "label": "IRC calculation",
        "documentation": "Intrinsic Reaction Coordinate path following from TS",
        "insertText": r"""! IRC calculation
 \$CONTRL SCFTYP=RHF RUNTYP=IRC \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$IRC NPOINT=50 STRIDE=0.1 FORWRD=.TRUE. \$END
 \$DATA
\${1:IRC path}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
    "ccsd": {
        "label": "CCSD(T) calculation",
        "documentation": "Coupled Cluster single point with perturbative triples",
        "insertText": r"""! CCSD(T) single point
 \$CONTRL SCFTYP=RHF RUNTYP=ENERGY CCTYP=CCSD(T) \$END
 \$SYSTEM MWORDS=100 MEMDDI=1000 \$END
 \$BASIS GBASIS=CC-PVTZ \$END
 \$CC NCORE=0 MAXCC=100 CCCONV=1.0E-06 \$END
 \$DATA
\${1:Molecule title}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
    "pcm-water": {
        "label": "PCM solvation (water)",
        "documentation": "DFT calculation with PCM water solvation",
        "insertText": r"""! PCM solvation in water
 \$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$PCM SOLVNT=WATER ICAV=0 \$END
 \$STATPT OPTTOL=0.0001 NSTEP=50 \$END
 \$DATA
\${1:Molecule in water}
\${2:C1}

\${3:Atom}   \${4:Z}   \${5:x}   \${6:y}   \${7:z}
 \$END""",
    },
}


def _get_diagnostics(content: str) -> List[Diagnostic]:
    """Get diagnostics for GAMESS input content.

    This combines syntax-level diagnostics from the parser with
    semantic-level diagnostics from the validator.
    """
    # Security: Check content size before parsing
    size_error = _check_content_size(content, "")
    if size_error:
        return size_error

    parser = GAMESSParser()
    parsed_input = parser.parse(content)

    diagnostics = []

    # 1. Syntax-level diagnostics from parser
    for item in parser.get_diagnostics():
        severity = DiagnosticSeverity.Warning
        if item.get("severity") == "error":
            severity = DiagnosticSeverity.Error

        line = item.get("line", 1) - 1
        diagnostics.append(
            Diagnostic(
                range=Range(
                    start=Position(line=line, character=0), end=Position(line=line, character=100)
                ),
                message=item.get("message", ""),
                severity=severity,
                source="gamess-lsp",
            )
        )

    # 2. Semantic-level diagnostics from validator
    semantic_diagnostics = validate_semantics(parsed_input)
    for diag in semantic_diagnostics:
        severity = DiagnosticSeverity.Warning
        if diag.severity == "error":
            severity = DiagnosticSeverity.Error

        line = diag.line - 1  # Convert to 0-based
        diagnostics.append(
            Diagnostic(
                range=Range(
                    start=Position(line=line, character=0), end=Position(line=line, character=100)
                ),
                message=diag.message,
                severity=severity,
                source="gamess-lsp",
                code=diag.code,
            )
        )

    return diagnostics


def _update_document(doc: Document) -> None:
    """Update cached document and publish diagnostics."""
    content = doc.source
    document_cache.set(doc.uri, content)

    diagnostics = diagnostic_provider.get_diagnostics(content)
    lint_diagnostics = lint_provider.lint(content)
    diagnostics.extend(lint_diagnostics)
    server.publish_diagnostics(doc.uri, diagnostics)


@server.feature("textDocument/didOpen")
def did_open(params: DidOpenTextDocumentParams) -> None:
    """Handle document open."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    _update_document(doc)


@server.feature("textDocument/didChange")
def did_change(params: DidChangeTextDocumentParams) -> None:
    """Handle document change."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    _update_document(doc)


@server.feature("textDocument/completion")
def completion(params: CompletionParams) -> CompletionList:
    """Handle completion requests including snippets."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    content = doc.source
    line = doc.lines[params.position.line]
    line_before = line[: params.position.character]

    items = []

    # Check for snippet triggers at start of line
    stripped_line = line_before.strip()
    if not stripped_line or stripped_line.startswith("!"):
        # Add snippet completions
        for snippet_id, snippet in GAMESS_SNIPPETS.items():
            items.append(
                CompletionItem(
                    label=snippet["label"],
                    kind=CompletionItemKind.Snippet,
                    documentation=snippet["documentation"],
                    insert_text=snippet["insertText"],
                    insert_text_format=InsertTextFormat.Snippet,
                    detail="GAMESS snippet",
                )
            )

    # Check if we're after an equals sign (value completion)
    if "=" in line_before:
        parts = line_before.rsplit("=", 1)
        if len(parts) == 2:
            keyword_part = parts[0].strip().split()[-1].upper() if parts[0].strip() else ""
            value_prefix = parts[1].strip().upper()

            parser = GAMESSParser()
            current_group = parser.get_group_at_position(content, params.position.line + 1)

            if current_group and current_group in GAMESS_KEYWORDS:
                if keyword_part in GAMESS_KEYWORDS[current_group]:
                    keyword_info = GAMESS_KEYWORDS[current_group][keyword_part]
                    allowed_values = keyword_info.get("values", [])

                    for val in allowed_values:
                        if val.upper().startswith(value_prefix):
                            items.append(
                                CompletionItem(
                                    label=val,
                                    kind=CompletionItemKind.Value,
                                    detail=f"Value for {keyword_part}",
                                    documentation=str(keyword_info.get("doc", "")),
                                )
                            )

            if items:
                return CompletionList(is_incomplete=False, items=items)

    # Check if completing a group
    if "$" in line_before:
        group_prefix = line_before.split("$")[-1].upper()
        for group_name in GAMESS_GROUPS:
            if group_name.startswith(group_prefix):
                items.append(
                    CompletionItem(
                        label=f"${group_name}",
                        kind=CompletionItemKind.Module,
                        detail="GAMESS group",
                        documentation=GAMESS_GROUPS.get(group_name, ""),
                    )
                )

        parser = GAMESSParser()
        current_group = parser.get_group_at_position(content, params.position.line + 1)

        if current_group and current_group in GAMESS_KEYWORDS:
            for keyword, info in GAMESS_KEYWORDS[current_group].items():
                if keyword.upper().startswith(group_prefix):
                    items.append(
                        CompletionItem(
                            label=keyword,
                            kind=CompletionItemKind.Property,
                            detail=f"{current_group} keyword",
                            documentation=str(info.get("doc", "")),
                        )
                    )
    else:
        for group_name, doc_text in GAMESS_GROUPS.items():
            items.append(
                CompletionItem(
                    label=f"${group_name}",
                    kind=CompletionItemKind.Module,
                    detail="GAMESS group",
                    documentation=doc_text,
                )
            )

    return CompletionList(is_incomplete=False, items=items)


@server.feature("textDocument/hover")
def hover(params: HoverParams) -> Optional[Hover]:
    """Handle hover requests."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    position = params.position

    line = doc.lines[position.line]
    word = _get_word_at_position(line, position.character)

    if not word:
        return None

    word_upper = word.upper()

    if word_upper in GAMESS_GROUPS:
        return Hover(contents=GAMESS_GROUPS[word_upper])

    parser = GAMESSParser()
    current_group = parser.get_group_at_position(doc.source, position.line + 1)

    if current_group and current_group in GAMESS_KEYWORDS:
        if word_upper in GAMESS_KEYWORDS[current_group]:
            info = GAMESS_KEYWORDS[current_group][word_upper]
            return Hover(contents=f"**{word}**\n\n{info.get('doc', 'No documentation available')}")

    return None


def _get_word_at_position(line: str, character: int) -> str:
    """Get the word at a character position."""
    if not line or character >= len(line):
        return ""

    start = character
    while start > 0 and line[start - 1].isalnum():
        start -= 1

    end = character
    while end < len(line) and line[end].isalnum():
        end += 1

    return line[start:end]


@server.feature("textDocument/diagnostic")
def diagnostic(params: Any) -> List[Diagnostic]:
    """Handle diagnostic requests."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    return diagnostic_provider.get_diagnostics(doc.source)


@server.feature("textDocument/formatting")
def formatting(params: DocumentFormattingParams) -> List[TextEdit]:
    """Handle document formatting requests."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    content = doc.source
    lines = content.split("\n")

    formatted_lines = []
    in_group = False
    indent = "  "

    for line in lines:
        stripped = line.strip()

        if not stripped:
            formatted_lines.append("")
            continue

        if stripped.startswith("!"):
            formatted_lines.append(stripped)
            continue

        if stripped.startswith("$") and not re.match(r"^\$END\b", stripped, re.IGNORECASE):
            match = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)\s*(.*)", stripped)
            if match:
                group_name = match.group(1).upper()
                rest = match.group(2).strip()

                if rest and not rest.startswith("$"):
                    formatted_lines.append(f"${group_name}")
                    in_group = True
                    keywords = _format_keywords(rest)
                    formatted_lines.append(f"{indent}{keywords}")
                else:
                    formatted_lines.append(f"${group_name}")
                    in_group = True

                    if rest.upper().startswith("$END"):
                        in_group = False
                        formatted_lines.append("$END")
        elif re.match(r"^\$END\b", stripped, re.IGNORECASE):
            in_group = False
            formatted_lines.append("$END")
        elif in_group:
            if "=" in stripped and not stripped.startswith("!"):
                formatted_keywords = _format_keywords(stripped)
                formatted_lines.append(f"{indent}{formatted_keywords}")
            else:
                formatted_lines.append(f"{indent}{stripped}")
        else:
            formatted_lines.append(stripped)

    return [
        TextEdit(
            range=Range(
                start=Position(line=0, character=0), end=Position(line=len(lines), character=0)
            ),
            new_text="\n".join(formatted_lines),
        )
    ]


def _format_keywords(line: str) -> str:
    """Format a line of keyword=value pairs."""
    tokens = tokenize_line(line)

    formatted_tokens = []
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            formatted_tokens.append(f"{key.strip()}={value.strip()}")
        else:
            formatted_tokens.append(token.strip())

    return " ".join(formatted_tokens)


@server.feature("textDocument/documentSymbol")
def document_symbol(params: DocumentSymbolParams) -> List[SymbolInformation]:
    """Handle document symbol requests."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    content = doc.source

    symbols = []

    parser = GAMESSParser()
    parsed = parser.parse(content)

    for group_name, group in parsed.groups.items():
        symbol = SymbolInformation(
            name=f"${group_name}",
            kind=SymbolKind.Class,
            location=Location(
                uri=params.text_document.uri,
                range=Range(
                    start=Position(line=group.line_start - 1, character=0),
                    end=Position(line=group.line_end - 1, character=0),
                ),
            ),
        )
        symbols.append(symbol)

        for keyword_name, keyword in group.keywords.items():
            kw_symbol = SymbolInformation(
                name=keyword_name,
                kind=SymbolKind.Property,
                location=Location(
                    uri=params.text_document.uri,
                    range=Range(
                        start=Position(line=keyword.line_number - 1, character=0),
                        end=Position(line=keyword.line_number - 1, character=100),
                    ),
                ),
                container_name=f"${group_name}",
            )
            symbols.append(kw_symbol)

    return symbols


@server.feature("workspace/symbol")
def workspace_symbol(params: WorkspaceSymbolParams) -> List[SymbolInformation]:
    """Handle workspace symbol requests."""
    query = params.query.upper() if params.query else ""
    symbols: List[SymbolInformation] = []

    for uri, content in document_cache.items():
        parser = GAMESSParser()
        parsed = parser.parse(content)

        for group_name, group in parsed.groups.items():
            if not query or query in group_name:
                symbol = SymbolInformation(
                    name=f"${group_name}",
                    kind=SymbolKind.Class,
                    location=Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=group.line_start - 1, character=0),
                            end=Position(line=group.line_end - 1, character=0),
                        ),
                    ),
                )
                symbols.append(symbol)

            for keyword_name, keyword in group.keywords.items():
                if not query or query in keyword_name:
                    kw_symbol = SymbolInformation(
                        name=keyword_name,
                        kind=SymbolKind.Property,
                        location=Location(
                            uri=uri,
                            range=Range(
                                start=Position(line=keyword.line_number - 1, character=0),
                                end=Position(line=keyword.line_number - 1, character=100),
                            ),
                        ),
                        container_name=f"${group_name}",
                    )
                    symbols.append(kw_symbol)

    return symbols


@server.feature("textDocument/definition")
def definition(params: DefinitionParams) -> Optional[List[Location]]:
    """Handle go to definition requests."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    content = doc.source
    position = params.position

    line = doc.lines[position.line]
    word = _get_word_at_position(line, position.character)

    if not word:
        return None

    word_upper = word.upper()
    parser = GAMESSParser()
    parsed = parser.parse(content)

    locations: List[Location] = []

    if word_upper in parsed.groups:
        group = parsed.groups[word_upper]
        locations.append(
            Location(
                uri=params.text_document.uri,
                range=Range(
                    start=Position(line=group.line_start - 1, character=0),
                    end=Position(line=group.line_start - 1, character=len(f"${word_upper}")),
                ),
            )
        )
        return locations

    current_group = parser.get_group_at_position(content, position.line + 1)
    if current_group:
        current_group_obj = parsed.get_group(current_group)
        if current_group_obj and word_upper in current_group_obj.keywords:
            keyword = current_group_obj.keywords[word_upper]
            locations.append(
                Location(
                    uri=params.text_document.uri,
                    range=Range(
                        start=Position(line=keyword.line_number - 1, character=0),
                        end=Position(line=keyword.line_number - 1, character=100),
                    ),
                )
            )
            return locations

    return None


@server.feature("textDocument/references")
def references(params: ReferenceParams) -> Optional[List[Location]]:
    """Handle find references requests."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    content = doc.source
    position = params.position

    line = doc.lines[position.line]
    word = _get_word_at_position(line, position.character)

    if not word:
        return None

    word_upper = word.upper()
    # Security: Escape regex special characters in user input
    escaped_word = re.escape(word_upper)

    locations: List[Location] = []
    lines = content.split("\n")

    for i, line_content in enumerate(lines):
        if re.search(rf"\\${escaped_word}\b", line_content, re.IGNORECASE):
            locations.append(
                Location(
                    uri=params.text_document.uri,
                    range=Range(
                        start=Position(line=i, character=0),
                        end=Position(line=i, character=len(line_content)),
                    ),
                )
            )
        elif re.search(rf"\b{escaped_word}\s*=", line_content, re.IGNORECASE):
            locations.append(
                Location(
                    uri=params.text_document.uri,
                    range=Range(
                        start=Position(line=i, character=0),
                        end=Position(line=i, character=len(line_content)),
                    ),
                )
            )

    return locations if locations else None


@server.feature("textDocument/codeAction")
def code_action(params: CodeActionParams) -> List[CodeAction]:
    """Handle code action requests."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    content = doc.source
    line_num = params.range.start.line
    line = doc.lines[line_num] if line_num < len(doc.lines) else ""

    actions = []
    parser = GAMESSParser()
    parser.parse(content)

    for warning in parser.warnings:
        if warning.get("line") == line_num + 1:
            message = warning.get("message", "")

            if "not properly closed" in message:
                action = CodeAction(
                    title="Add missing $END",
                    kind=CodeActionKind.QuickFix,
                    edit=WorkspaceEdit(
                        document_changes=[
                            TextDocumentEdit(
                                text_document=OptionalVersionedTextDocumentIdentifier(
                                    uri=params.text_document.uri,
                                    version=doc.version,
                                ),
                                edits=[
                                    TextEdit(
                                        range=Range(
                                            start=Position(line=line_num, character=len(line)),
                                            end=Position(line=line_num, character=len(line)),
                                        ),
                                        new_text="\n\\$END",
                                    )
                                ],
                            )
                        ]
                    ),
                )
                actions.append(action)

            if "Unknown group" in message:
                unknown_group = message.split(": $")[-1].strip() if ": $" in message else ""
                if unknown_group:
                    suggestions = get_close_matches(
                        unknown_group, GAMESS_GROUPS.keys(), n=3, cutoff=0.5
                    )
                    for suggestion in suggestions:
                        action = CodeAction(
                            title=f"Change to \\${suggestion}",
                            kind=CodeActionKind.QuickFix,
                            edit=WorkspaceEdit(
                                changes={
                                    params.text_document.uri: [
                                        TextEdit(
                                            range=Range(
                                                start=Position(line=line_num, character=0),
                                                end=Position(line=line_num, character=len(line)),
                                            ),
                                            new_text=line.replace(
                                                f"${unknown_group}", f"${suggestion}"
                                            ),
                                        )
                                    ]
                                }
                            ),
                        )
                        actions.append(action)

    current_group = parser.get_group_at_position(content, line_num + 1)
    if current_group == "CONTRL":
        parsed = parser.parse(content)
        contrl_group = parsed.get_group("CONTRL")
        if contrl_group and "RUNTYP" not in contrl_group.keywords:
            action = CodeAction(
                title="Add RUNTYP=ENERGY to \\$CONTRL",
                kind=CodeActionKind.QuickFix,
                edit=WorkspaceEdit(
                    changes={
                        params.text_document.uri: [
                            TextEdit(
                                range=Range(
                                    start=Position(line=line_num, character=len(line.rstrip())),
                                    end=Position(line=line_num, character=len(line.rstrip())),
                                ),
                                new_text=" RUNTYP=ENERGY",
                            )
                        ]
                    }
                ),
            )
            actions.append(action)

    return actions


@server.feature("textDocument/rename")
def rename(params: RenameParams) -> Optional[WorkspaceEdit]:
    """Handle rename requests."""
    doc = server.workspace.get_text_document(params.text_document.uri)
    content = doc.source
    position = params.position
    new_name = params.new_name

    line = doc.lines[position.line]
    word = _get_word_at_position(line, position.character)

    if not word:
        return None

    word_upper = word.upper()
    parser = GAMESSParser()
    parsed = parser.parse(content)

    if word_upper in GAMESS_GROUPS or word_upper.startswith("$"):
        group_name = word_upper.lstrip("$")
        if group_name in parsed.groups:
            changes = []
            lines = content.split("\n")
            # Security: Escape regex special characters in user input
            escaped_group_name = re.escape(group_name)
            for i, line_content in enumerate(lines):
                match = re.match(rf"^\s*\$({escaped_group_name})\b", line_content, re.IGNORECASE)
                if match:
                    start_char = line_content.find(f"${group_name}")
                    if start_char == -1:
                        start_char = line_content.upper().find(f"${group_name}")
                    changes.append(
                        TextEdit(
                            range=Range(
                                start=Position(line=i, character=start_char + 1),
                                end=Position(line=i, character=start_char + 1 + len(group_name)),
                            ),
                            new_text=new_name.lstrip("$"),
                        )
                    )

            if changes:
                return WorkspaceEdit(changes={params.text_document.uri: changes})

    current_group = parser.get_group_at_position(content, position.line + 1)
    if current_group:
        current_group_obj = parsed.get_group(current_group)
        if current_group_obj and word_upper in current_group_obj.keywords:
            keyword = current_group_obj.keywords[word_upper]
            return WorkspaceEdit(
                changes={
                    params.text_document.uri: [
                        TextEdit(
                            range=Range(
                                start=Position(line=keyword.line_number - 1, character=0),
                                end=Position(line=keyword.line_number - 1, character=100),
                            ),
                            new_text=line.replace(word, new_name, 1),
                        )
                    ]
                }
            )

    return None


def main() -> None:
    """Main entry point."""
    server.start_io()


if __name__ == "__main__":
    main()
