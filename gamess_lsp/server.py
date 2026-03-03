"""GAMESS Language Server Protocol implementation."""

import logging
import re
from typing import Any, List, Optional

from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_DIAGNOSTIC,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_FOLDING_RANGE,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    Position,
    TextDocumentContentChangeEvent,
    DiagnosticOptions,
)
from pygls.server import LanguageServer

from .groups import (
    GAMESS_GROUPS,
    get_all_group_names,
    get_group_documentation,
    get_group_parameters,
    get_parameter_documentation,
)
from .parser import GamessParser
from .diagnostics import GamessDiagnostics
from .document_symbols import DocumentSymbolProvider
from .folding import FoldingRangeProvider
from .snippets import get_all_snippets


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GamessLanguageServer(LanguageServer):
    """GAMESS Language Server."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = GamessParser()
        self.diagnostics = GamessDiagnostics()
        self.documents: dict = {}
        self.symbol_provider = DocumentSymbolProvider()
        self.folding_provider = FoldingRangeProvider()


server = GamessLanguageServer("gamess-lsp", "v0.1.0")


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: GamessLanguageServer, params: DidOpenTextDocumentParams):
    """Handle document open."""
    uri = params.text_document.uri
    content = params.text_document.text
    ls.documents[uri] = content
    
    # Run diagnostics on open
    diagnostics = ls.diagnostics.validate(content)
    ls.publish_diagnostics(uri, diagnostics)
    
    logger.info(f"Opened document: {uri}, found {len(diagnostics)} diagnostics")


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: GamessLanguageServer, params: DidChangeTextDocumentParams):
    """Handle document change."""
    uri = params.text_document.uri
    # Get the latest content
    for change in params.content_changes:
        if hasattr(change, 'text'):
            ls.documents[uri] = change.text
    
    # Run diagnostics on change
    if uri in ls.documents:
        diagnostics = ls.diagnostics.validate(ls.documents[uri])
        ls.publish_diagnostics(uri, diagnostics)
        logger.debug(f"Changed document: {uri}, found {len(diagnostics)} diagnostics")
    
    logger.debug(f"Changed document: {uri}")


@server.feature(TEXT_DOCUMENT_COMPLETION)
def completions(ls: GamessLanguageServer, params: CompletionParams) -> Optional[CompletionList]:
    """Provide completions."""
    uri = params.text_document.uri
    position = params.position
    
    if uri not in ls.documents:
        return None
    
    content = ls.documents[uri]
    lines = content.split('\n')
    
    if position.line >= len(lines):
        return None
    
    current_line = lines[position.line]
    line_before_cursor = current_line[:position.character]
    
    items = []
    
    # Check for snippet triggers at line start
    if not line_before_cursor.strip():
        # Add snippets
        for snippet in get_all_snippets():
            items.append(CompletionItem(
                label=snippet.prefix,
                kind=CompletionItemKind.Snippet,
                documentation=snippet.description,
                insert_text='\n'.join(snippet.body),
                insert_text_format=2,  # Snippet format
            ))
    
    # Check if we're typing a $GROUP
    if '$' in line_before_cursor:
        # Check if we're after the $ and typing a group name
        match = re.search(r'\$([A-Za-z_]*)$', line_before_cursor)
        if match:
            typed = match.group(1).upper()
            # Suggest group names
            for group_name in get_all_group_names():
                if group_name.startswith(typed):
                    group_doc = get_group_documentation(group_name)
                    items.append(CompletionItem(
                        label=f"${group_name}",
                        kind=CompletionItemKind.Module,
                        documentation=group_doc.description if group_doc else "",
                        insert_text=group_name[len(typed):]
                    ))
        
        # Check if we're inside a $GROUP and typing a parameter
        elif re.search(r'\$[A-Z]+\s+', line_before_cursor.upper()):
            # Parse current document to find which group we're in
            parser = GamessParser()
            groups, _ = parser.parse(content)
            
            # Find the group at current position
            current_group = None
            for group in groups:
                if group.start_line <= position.line + 1 <= group.end_line:
                    current_group = group
                    break
            
            # Also check for incomplete group
            if not current_group:
                # Look for a $GROUP start without $END
                for line_idx, line in enumerate(lines[:position.line + 1]):
                    if line.strip().startswith('$') and not line.strip().upper().endswith('$END'):
                        group_name_match = re.match(r'\$([A-Z][A-Z0-9_]*)', line.strip().upper())
                        if group_name_match:
                            group_name = group_name_match.group(1)
                            group_doc = get_group_documentation(group_name)
                            if group_doc:
                                current_group = type('obj', (object,), {
                                    'name': group_name
                                })()
            
            if current_group:
                # Suggest parameters for this group
                group_doc = get_group_documentation(current_group.name)
                if group_doc:
                    # Check if we're typing a parameter name
                    param_match = re.search(r'([A-Za-z_]*)$', line_before_cursor)
                    if param_match:
                        typed = param_match.group(1).upper()
                        for param_name, param_doc in group_doc.parameters.items():
                            if param_name.startswith(typed):
                                items.append(CompletionItem(
                                    label=param_name,
                                    kind=CompletionItemKind.Property,
                                    documentation=_format_param_doc(param_doc),
                                    insert_text=f"{param_name[len(typed):]}="
                                ))
                    
                    # Also suggest parameters if at a space
                    elif line_before_cursor.endswith(' ') or line_before_cursor.endswith('\t'):
                        for param_name, param_doc in group_doc.parameters.items():
                            items.append(CompletionItem(
                                label=param_name,
                                kind=CompletionItemKind.Property,
                                documentation=_format_param_doc(param_doc),
                                insert_text=f"{param_name}="
                            ))
        
        # Check if we're after = (parameter value completion)
        elif '=' in line_before_cursor:
            # Find the parameter name
            param_match = re.search(r'([A-Z][A-Z0-9_]*)\s*=\s*([A-Za-z0-9_]*)$', line_before_cursor.upper())
            if param_match:
                param_name = param_match.group(1)
                typed = param_match.group(2)
                
                # Find which group we're in
                parser = GamessParser()
                groups, _ = parser.parse(content)
                for group in groups:
                    if group.start_line <= position.line + 1 <= group.end_line:
                        param_doc = get_parameter_documentation(group.name, param_name)
                        if param_doc and param_doc.valid_values:
                            for value in param_doc.valid_values:
                                if value.upper().startswith(typed.upper()):
                                    items.append(CompletionItem(
                                        label=value,
                                        kind=CompletionItemKind.Value,
                                        insert_text=value[len(typed):]
                                    ))
                        break
    
    # If no specific context, suggest all groups
    if not items and (not line_before_cursor.strip() or line_before_cursor.strip().startswith('!')):
        for group_name in get_all_group_names():
            group_doc = get_group_documentation(group_name)
            items.append(CompletionItem(
                label=f"${group_name}",
                kind=CompletionItemKind.Module,
                documentation=group_doc.description if group_doc else "",
                insert_text=f"${group_name}\n$END"
            ))
    
    return CompletionList(is_incomplete=False, items=items)


@server.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: GamessLanguageServer, params: HoverParams) -> Optional[Hover]:
    """Provide hover information."""
    uri = params.text_document.uri
    position = params.position
    
    if uri not in ls.documents:
        return None
    
    content = ls.documents[uri]
    lines = content.split('\n')
    
    if position.line >= len(lines):
        return None
    
    current_line = lines[position.line]
    
    # Check if hovering over a $GROUP
    # Find word at position
    word_match = _get_word_at_position(current_line, position.character)
    if word_match:
        word = word_match.upper()
        
        # Check if it's a group name (with or without $)
        if word.startswith('$'):
            word = word[1:]
        
        group_doc = get_group_documentation(word)
        if group_doc:
            return Hover(
                contents=MarkupContent(
                    kind=MarkupKind.Markdown,
                    value=_format_group_hover(group_doc)
                )
            )
        
        # Check if it's a parameter
        # Parse document to find which group we're in
        parser = GamessParser()
        groups, _ = parser.parse(content)
        
        for group in groups:
            if group.start_line <= position.line + 1 <= group.end_line:
                param_doc = get_parameter_documentation(group.name, word)
                if param_doc:
                    return Hover(
                        contents=MarkupContent(
                            kind=MarkupKind.Markdown,
                            value=_format_param_hover(param_doc)
                        )
                    )
                break
    
    return None


@server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(ls: GamessLanguageServer, params):
    """Provide document symbols for outline view."""
    uri = params.text_document.uri
    
    if uri not in ls.documents:
        return []
    
    content = ls.documents[uri]
    return ls.symbol_provider.get_document_symbols(content)


@server.feature(TEXT_DOCUMENT_FOLDING_RANGE)
def folding_range(ls: GamessLanguageServer, params):
    """Provide folding ranges."""
    uri = params.text_document.uri
    
    if uri not in ls.documents:
        return []
    
    content = ls.documents[uri]
    return ls.folding_provider.get_folding_ranges(content)


def _get_word_at_position(line: str, character: int) -> Optional[str]:
    """Extract the word at a specific position in a line."""
    # Match GAMESS identifiers (letters, numbers, underscores, starting with letter or $)
    for match in re.finditer(r'\$?[A-Za-z][A-Za-z0-9_]*', line):
        if match.start() <= character <= match.end():
            return match.group()
    return None


def _format_group_hover(group_doc) -> str:
    """Format group documentation for hover."""
    lines = [
        f"## ${group_doc.name}",
        "",
        group_doc.description,
        "",
    ]
    
    if group_doc.required:
        lines.append("**Required**: Yes")
        lines.append("")
    
    if group_doc.parameters:
        lines.append("**Parameters**:")
        for param_name, param_doc in group_doc.parameters.items():
            default_info = f" (default: `{param_doc.default}`)" if param_doc.default else ""
            lines.append(f"- `{param_name}`{default_info}")
    
    return "\n".join(lines)


def _format_param_doc(param_doc) -> str:
    """Format parameter documentation."""
    lines = [param_doc.description]
    
    if param_doc.type:
        lines.append(f"\nType: `{param_doc.type}`")
    
    if param_doc.default:
        lines.append(f"\nDefault: `{param_doc.default}`")
    
    if param_doc.valid_values:
        lines.append(f"\nValid values: {', '.join(f'`{v}`' for v in param_doc.valid_values)}")
    
    return "\n".join(lines)


def _format_param_hover(param_doc) -> str:
    """Format parameter documentation for hover."""
    lines = [
        f"## {param_doc.name}",
        "",
        param_doc.description,
        "",
    ]
    
    if param_doc.type:
        lines.append(f"**Type**: `{param_doc.type}`")
    
    if param_doc.default:
        lines.append(f"**Default**: `{param_doc.default}`")
    
    if param_doc.valid_values:
        lines.append("")
        lines.append("**Valid values**:")
        for value in param_doc.valid_values:
            lines.append(f"- `{value}`")
    
    return "\n".join(lines)


def main():
    """Entry point for the language server."""
    server.start_io()


if __name__ == "__main__":
    main()
