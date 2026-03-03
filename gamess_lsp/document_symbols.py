"""GAMESS LSP Document Symbols provider."""

from typing import List, Optional, Any

from lsprotocol.types import (
    DocumentSymbol,
    SymbolKind,
    Range,
    Position,
)

from .parser import GamessParser


class DocumentSymbolProvider:
    """Provides document symbols for outline view."""
    
    def get_document_symbols(self, content: str) -> List[DocumentSymbol]:
        """Get document symbols for the outline view.
        
        Args:
            content: The input file content
            
        Returns:
            List of DocumentSymbol objects representing groups and parameters
        """
        symbols = []
        parser = GamessParser()
        groups, _ = parser.parse(content)
        
        lines = content.split('\n')
        
        for group in groups:
            # Create symbol for the group
            group_range = self._get_group_range(group, lines)
            # Use dict to avoid 'range' keyword conflict
            group_symbol = DocumentSymbol(
                name=f"${group.name}",
                kind=SymbolKind.Module,
                range=group_range,
                selection_range=self._get_group_name_range(group, lines),
                detail=self._get_group_detail(group),
                children=[]
            )
            
            # Add parameters as children
            for param in group.parameters:
                param_range = Range(
                    start=Position(line=param.line - 1, character=param.column),
                    end=Position(line=param.line - 1, character=param.column + len(param.name) + len(param.value) + 1)
                )
                param_symbol = DocumentSymbol(
                    name=param.name,
                    kind=SymbolKind.Property,
                    range=param_range,
                    selection_range=Range(
                        start=Position(line=param.line - 1, character=param.column),
                        end=Position(line=param.line - 1, character=param.column + len(param.name))
                    ),
                    detail=param.value,
                    children=[]
                )
                group_symbol.children.append(param_symbol)
            
            symbols.append(group_symbol)
        
        return symbols
    
    def _get_group_range(self, group, lines: List[str]) -> Range:
        """Get the full range of a group."""
        start_line = group.start_line - 1
        end_line = min(group.end_line - 1, len(lines) - 1)
        
        start_char = 0
        end_char = len(lines[end_line]) if end_line < len(lines) else 0
        
        return Range(
            start=Position(line=start_line, character=start_char),
            end=Position(line=end_line, character=end_char)
        )
    
    def _get_group_name_range(self, group, lines: List[str]) -> Range:
        """Get the range of just the group name."""
        line_idx = group.start_line - 1
        if line_idx < len(lines):
            line = lines[line_idx]
            dollar_pos = line.find('$')
            if dollar_pos >= 0:
                name_end = dollar_pos + 1 + len(group.name)
                return Range(
                    start=Position(line=line_idx, character=dollar_pos),
                    end=Position(line=line_idx, character=name_end)
                )
        
        return Range(
            start=Position(line=group.start_line - 1, character=0),
            end=Position(line=group.start_line - 1, character=len(group.name) + 1)
        )
    
    def _get_group_detail(self, group) -> str:
        """Get a detail string for the group."""
        param_count = len(group.parameters)
        if param_count == 0:
            return ""
        elif param_count == 1:
            return f"1 parameter"
        else:
            return f"{param_count} parameters"
