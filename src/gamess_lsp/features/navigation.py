"""Navigation feature providers for GAMESS LSP.

Provides go-to-definition, hover, and references functionality for
GAMESS input files.  Covers sections ($CONTRL, $BASIS, ...), keywords
(RUNTYP, SCFTYP, ...), include references (EXTFIL / BASNAM), and
local variables ($VEC, $DATA geometry atoms).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from lsprotocol.types import (
    Hover,
    Location,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
)

from ..keywords import GAMESS_GROUPS, GAMESS_KEYWORDS
from ..parser import GAMESSInputFile, GAMESSKeyword, GAMESSParser


# ---------------------------------------------------------------------------
# Symbol index — shared across definition / hover / references
# ---------------------------------------------------------------------------


@dataclass
class SymbolInfo:
    """A single navigable symbol inside a GAMESS input file."""

    kind: str  # "section" | "keyword" | "include" | "variable"
    name: str
    line: int  # 0-based line number
    character: int  # start column (0-based)
    end_character: int
    uri: str = ""
    group_name: str = ""  # parent section for keywords
    detail: str = ""


class SymbolIndex:
    """Lightweight symbol index built from parsed GAMESS content.

    The index is cheap to compute (a single pass) and can later be reused
    for rename and code-action features.
    """

    def __init__(self) -> None:
        self._symbols: List[SymbolInfo] = []

    # -- building -----------------------------------------------------------

    def build(self, content: str, uri: str = "") -> None:
        """Build (or rebuild) the index from *content*."""
        self._symbols.clear()
        parser = GAMESSParser()
        parsed = parser.parse(content)
        lines = content.split("\n")

        # 1. Sections
        for group_name, group in parsed.groups.items():
            start_char = self._find_section_col(lines, group.line_start, group_name)
            self._symbols.append(
                SymbolInfo(
                    kind="section",
                    name=group_name,
                    line=group.line_start - 1,
                    character=start_char,
                    end_character=start_char + len(group_name) + 1,
                    uri=uri,
                    detail=GAMESS_GROUPS.get(group_name, ""),
                )
            )
            # 2. Keywords inside each section
            for kw_name, kw in group.keywords.items():
                col = self._find_keyword_col(lines, kw.line_number - 1, kw_name)
                self._symbols.append(
                    SymbolInfo(
                        kind="keyword",
                        name=kw_name,
                        line=kw.line_number - 1,
                        character=col,
                        end_character=col + len(kw_name),
                        uri=uri,
                        group_name=group_name,
                    )
                )

            # 3. Include references (EXTFIL / BASNAM in $BASIS)
            if group_name == "BASIS":
                self._index_basis_includes(group, lines, uri)

        # 4. Variables — $DATA geometry atoms and $VEC references
        self._index_data_variables(parsed, lines, uri)
        self._index_vec_variables(parsed, lines, uri)

    # -- querying -----------------------------------------------------------

    @property
    def symbols(self) -> List[SymbolInfo]:
        """Return all indexed symbols."""
        return self._symbols

    def symbol_at(self, line: int, character: int) -> Optional[SymbolInfo]:
        """Return the narrowest symbol that spans (*line*, *character*)."""
        candidates = [
            s
            for s in self._symbols
            if s.line == line and s.character <= character < s.end_character
        ]
        if not candidates:
            return None
        # Prefer keywords/variables over sections (narrower scope)
        kind_order = {"variable": 0, "keyword": 1, "include": 2, "section": 3}
        candidates.sort(key=lambda s: kind_order.get(s.kind, 99))
        return candidates[0]

    def find_definitions(self, name: str, kind: Optional[str] = None) -> List[SymbolInfo]:
        """Return all symbols whose upper-case name matches *name*."""
        upper = name.upper()
        results = [s for s in self._symbols if s.name.upper() == upper]
        if kind is not None:
            results = [s for s in results if s.kind == kind]
        return results

    def find_references(self, name: str) -> List[SymbolInfo]:
        """Return all symbols whose upper-case name matches *name*.

        For sections this includes every occurrence of ``$NAME`` in the file.
        For keywords it includes every ``KEY=`` occurrence.
        """
        return self.find_definitions(name)

    # -- private helpers ----------------------------------------------------

    @staticmethod
    def _find_section_col(lines: List[str], line_num: int, name: str) -> int:
        """Return the column where ``$name`` starts on *line_num* (1-based)."""
        if line_num < 1 or line_num > len(lines):
            return 0
        text = lines[line_num - 1]
        idx = text.upper().find(f"${name.upper()}")
        return max(idx, 0)

    @staticmethod
    def _find_keyword_col(lines: List[str], line_idx: int, kw_name: str) -> int:
        """Return the column where *kw_name* starts on *line_idx* (0-based)."""
        if line_idx < 0 or line_idx >= len(lines):
            return 0
        text = lines[line_idx]
        idx = text.upper().find(kw_name.upper())
        return max(idx, 0)

    def _index_basis_includes(
        self,
        group: "GAMESSGroup",
        lines: List[str],
        uri: str,
    ) -> None:
        """Index EXTFIL and BASNAM as include symbols."""
        from ..parser import GAMESSGroup as _G  # noqa: F811 (re-import for type)

        for kw_name in ("EXTFIL", "BASNAM"):
            kw = group.keywords.get(kw_name)
            if kw is None:
                continue
            col = self._find_keyword_col(lines, kw.line_number - 1, kw_name)
            self._symbols.append(
                SymbolInfo(
                    kind="include",
                    name=kw_name,
                    line=kw.line_number - 1,
                    character=col,
                    end_character=col + len(kw_name),
                    uri=uri,
                    group_name="BASIS",
                    detail=kw.value,
                )
            )

    def _index_data_variables(
        self,
        parsed: GAMESSInputFile,
        lines: List[str],
        uri: str,
    ) -> None:
        """Index geometry atom symbols as variables inside $DATA."""
        data_group = parsed.get_group("DATA")
        if data_group is None:
            return
        start = data_group.line_start - 1
        end = data_group.line_end  # 0-based exclusive
        data_line_count = 0
        for idx in range(start, min(end, len(lines))):
            stripped = lines[idx].strip()
            if not stripped or stripped.startswith("!"):
                continue
            # First two non-empty lines after $DATA are title and symmetry
            data_line_count += 1
            if data_line_count <= 2:
                continue
            parts = stripped.split()
            if parts:
                symbol = parts[0]
                col = lines[idx].find(symbol)
                self._symbols.append(
                    SymbolInfo(
                        kind="variable",
                        name=symbol.upper(),
                        line=idx,
                        character=max(col, 0),
                        end_character=max(col, 0) + len(symbol),
                        uri=uri,
                        group_name="DATA",
                    )
                )

    def _index_vec_variables(
        self,
        parsed: GAMESSInputFile,
        lines: List[str],
        uri: str,
    ) -> None:
        """Index $VEC group as a variable symbol for cross-reference."""
        vec_group = parsed.get_group("VEC")
        if vec_group is None:
            return
        col = self._find_section_col(lines, vec_group.line_start, "VEC")
        self._symbols.append(
            SymbolInfo(
                kind="variable",
                name="VEC",
                line=vec_group.line_start - 1,
                character=col,
                end_character=col + 4,
                uri=uri,
                group_name="VEC",
                detail="Molecular orbital vectors",
            )
        )


# ---------------------------------------------------------------------------
# Definition provider
# ---------------------------------------------------------------------------


class DefinitionProvider:
    """Go-to-definition for GAMESS sections, keywords, includes, variables."""

    def get_definition(
        self,
        content: str,
        uri: str,
        position: Position,
    ) -> Optional[List[Location]]:
        """Return definition locations for the symbol at *position*."""
        index = SymbolIndex()
        index.build(content, uri)

        sym = index.symbol_at(position.line, position.character)
        if sym is None:
            return None

        # For includes, try to resolve the target file
        if sym.kind == "include" and sym.name == "BASNAM":
            target_uri = self._resolve_include_uri(uri, sym.detail)
            if target_uri:
                return [
                    Location(
                        uri=target_uri,
                        range=Range(
                            start=Position(line=0, character=0),
                            end=Position(line=0, character=0),
                        ),
                    )
                ]

        # Sections and keywords: find the first (definition) occurrence
        if sym.kind == "section":
            defs = index.find_definitions(sym.name, kind="section")
        elif sym.kind == "keyword":
            defs = index.find_definitions(sym.name, kind="keyword")
        elif sym.kind == "variable":
            defs = index.find_definitions(sym.name, kind="variable")
        else:
            defs = [sym]

        if not defs:
            return None

        return [
            Location(
                uri=d.uri or uri,
                range=Range(
                    start=Position(line=d.line, character=d.character),
                    end=Position(line=d.line, character=d.end_character),
                ),
            )
            for d in defs[:1]
        ]

    @staticmethod
    def _resolve_include_uri(source_uri: str, filename: str) -> Optional[str]:
        """Best-effort resolution of a BASNAM include path."""
        if not filename:
            return None
        try:
            from urllib.parse import urlparse
            import pathlib

            parsed = urlparse(source_uri)
            if parsed.scheme != "file":
                return None
            base = pathlib.Path(parsed.path).parent
            target = base / filename
            if not filename.endswith(".inp") and not filename.endswith(".gms"):
                # Try common extensions
                for ext in (".inp", ".gms", ".bas", ""):
                    candidate = base / (filename + ext)
                    if candidate.exists():
                        return candidate.as_uri()
            if target.exists():
                return target.as_uri()
            # Return best-guess URI even if file doesn't exist
            return target.as_uri()
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Hover provider
# ---------------------------------------------------------------------------


class HoverProvider:
    """Hover documentation for GAMESS sections, keywords, and variables."""

    def get_hover(
        self,
        content: str,
        position: Position,
    ) -> Optional[Hover]:
        """Return hover info for the symbol at *position*."""
        index = SymbolIndex()
        index.build(content)

        sym = index.symbol_at(position.line, position.character)
        if sym is None:
            return self._fallback_hover(content, position)

        if sym.kind == "section":
            return self._hover_section(sym)
        if sym.kind == "keyword":
            return self._hover_keyword(sym)
        if sym.kind == "include":
            return self._hover_include(sym)
        if sym.kind == "variable":
            return self._hover_variable(sym, content)
        return None

    # -- section hover ------------------------------------------------------

    @staticmethod
    def _hover_section(sym: SymbolInfo) -> Optional[Hover]:
        doc = GAMESS_GROUPS.get(sym.name, "")
        if not doc:
            return None
        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=f"## `${sym.name}`\n\n{doc.strip()}",
            )
        )

    # -- keyword hover ------------------------------------------------------

    @staticmethod
    def _hover_keyword(sym: SymbolInfo) -> Optional[Hover]:
        group = sym.group_name
        kw_db = GAMESS_KEYWORDS.get(group, {})
        info = kw_db.get(sym.name)
        if info is None:
            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=f"**{sym.name}**\n\n_Unknown keyword in ${group}_",
                )
            )
        parts = [f"**{sym.name}** (in `${group}`)\n"]
        parts.append(info.get("doc", "No documentation available."))
        values = info.get("values", [])
        if values:
            parts.append("\n**Allowed values:** " + ", ".join(f"`{v}`" for v in values))
        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value="\n".join(parts),
            )
        )

    # -- include hover ------------------------------------------------------

    @staticmethod
    def _hover_include(sym: SymbolInfo) -> Optional[Hover]:
        target = sym.detail or "unknown file"
        return Hover(
            contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=f"**Include:** `{target}`\n\nExternal basis set file reference.",
            )
        )

    # -- variable hover -----------------------------------------------------

    @staticmethod
    def _hover_variable(sym: SymbolInfo, content: str) -> Optional[Hover]:
        if sym.group_name == "DATA":
            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=f"**Atom:** `{sym.name}`\n\nGeometry atom in `$DATA` section.",
                )
            )
        if sym.group_name == "VEC":
            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=(
                        "**$VEC** — Molecular orbital vectors\n\n"
                        "Contains MO coefficient data, typically read via "
                        "`$GUESS GUESS=MOREAD`."
                    ),
                )
            )
        return None

    # -- fallback hover (dollar-prefixed section names) ---------------------

    def _fallback_hover(self, content: str, position: Position) -> Optional[Hover]:
        """Try to hover on a ``$SECTION`` name that may not be in the index."""
        lines = content.split("\n")
        if position.line >= len(lines):
            return None
        line = lines[position.line]
        word = self._get_word_at_position(line, position.character)
        if not word:
            return None
        upper = word.upper().lstrip("$")
        if upper in GAMESS_GROUPS:
            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=f"## `${upper}`\n\n{GAMESS_GROUPS[upper].strip()}",
                )
            )
        return None

    @staticmethod
    def _get_word_at_position(line: str, character: int) -> str:
        if not line or character >= len(line):
            return ""
        start = character
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "$"):
            start -= 1
        end = character
        while end < len(line) and line[end].isalnum():
            end += 1
        return line[start:end]


# ---------------------------------------------------------------------------
# References provider
# ---------------------------------------------------------------------------


class ReferencesProvider:
    """Find-references for GAMESS sections, keywords, includes, variables."""

    def get_references(
        self,
        content: str,
        uri: str,
        position: Position,
        include_declaration: bool = True,
    ) -> List[Location]:
        """Return all references to the symbol at *position*."""
        index = SymbolIndex()
        index.build(content, uri)

        sym = index.symbol_at(position.line, position.character)

        if sym is None:
            return self._textual_references(content, uri, position)

        # For sections, always use textual search because the parser
        # deduplicates groups (dict key), losing earlier occurrences.
        if sym.kind == "section":
            return self._textual_references_for_name(
                content, uri, sym.name, include_declaration
            )

        # For keywords, also use textual search for full coverage
        if sym.kind == "keyword":
            return self._textual_references_for_keyword(
                content, uri, sym.name, include_declaration
            )

        # For variables and includes, use the index
        all_refs = index.find_references(sym.name)
        if not include_declaration:
            all_refs = [r for r in all_refs if not (r.line == sym.line and r.character == sym.character)]

        return [
            Location(
                uri=r.uri or uri,
                range=Range(
                    start=Position(line=r.line, character=r.character),
                    end=Position(line=r.line, character=r.end_character),
                ),
            )
            for r in all_refs
        ]

    # -- textual searches ---------------------------------------------------

    @staticmethod
    def _textual_references(
        content: str,
        uri: str,
        position: Position,
    ) -> List[Location]:
        """Textual search when the symbol index has no match."""
        lines = content.split("\n")
        if position.line >= len(lines):
            return []
        line = lines[position.line]
        word = _extract_word(line, position.character)
        if not word:
            return []
        upper = word.upper().lstrip("$")
        if not upper:
            return []

        locations: List[Location] = []
        escaped = re.escape(upper)
        for i, text in enumerate(lines):
            if re.search(rf"\${escaped}\b", text, re.IGNORECASE):
                locations.append(
                    Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=i, character=0),
                            end=Position(line=i, character=len(text)),
                        ),
                    )
                )
            elif re.search(rf"\b{escaped}\s*=", text, re.IGNORECASE):
                locations.append(
                    Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=i, character=0),
                            end=Position(line=i, character=len(text)),
                        ),
                    )
                )
        return locations

    @staticmethod
    def _textual_references_for_name(
        content: str,
        uri: str,
        name: str,
        include_declaration: bool,
    ) -> List[Location]:
        """Find all lines referencing section *name* via textual search."""
        lines = content.split("\n")
        escaped = re.escape(name)
        locations: List[Location] = []
        for i, text in enumerate(lines):
            if re.search(rf"\${escaped}\b", text, re.IGNORECASE):
                locations.append(
                    Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=i, character=0),
                            end=Position(line=i, character=len(text)),
                        ),
                    )
                )
        if not include_declaration and locations:
            locations = locations[1:]
        return locations

    @staticmethod
    def _textual_references_for_keyword(
        content: str,
        uri: str,
        name: str,
        include_declaration: bool,
    ) -> List[Location]:
        """Find all lines referencing keyword *name* via textual search."""
        lines = content.split("\n")
        escaped = re.escape(name)
        locations: List[Location] = []
        for i, text in enumerate(lines):
            if re.search(rf"\b{escaped}\s*=", text, re.IGNORECASE):
                locations.append(
                    Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=i, character=0),
                            end=Position(line=i, character=len(text)),
                        ),
                    )
                )
        if not include_declaration and locations:
            locations = locations[1:]
        return locations


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _extract_word(line: str, character: int) -> str:
    """Extract the alphanumeric (plus ``$``) word at *character* in *line*."""
    if not line or character >= len(line):
        return ""
    # If the character itself is $, advance past it to get the section name
    if character < len(line) and line[character] == "$":
        start = character
        end = character + 1
        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1
        return line[start:end]
    start = character
    while start > 0 and (line[start - 1].isalnum() or line[start - 1] in ("$", "_")):
        start -= 1
    end = character
    while end < len(line) and (line[end].isalnum() or line[end] == "_"):
        end += 1
    return line[start:end]
