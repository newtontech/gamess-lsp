"""GAMESS LSP Folding Range provider."""

from typing import List

from lsprotocol.types import (
    FoldingRange,
    FoldingRangeKind,
)

from .parser import GamessParser


class FoldingRangeProvider:
    """Provides folding ranges for GAMESS input files."""
    
    def get_folding_ranges(self, content: str) -> List[FoldingRange]:
        """Get folding ranges for $GROUP sections.
        
        Args:
            content: The input file content
            
        Returns:
            List of FoldingRange objects
        """
        ranges = []
        parser = GamessParser()
        groups, _ = parser.parse(content)
        
        for group in groups:
            # Each group can be folded
            # Lines are 0-indexed in LSP
            start_line = group.start_line - 1
            end_line = group.end_line - 1
            
            if end_line > start_line:
                ranges.append(FoldingRange(
                    start_line=start_line,
                    end_line=end_line,
                    kind=FoldingRangeKind.Region,
                    collapsed_text=f"${group.name}"
                ))
        
        return ranges
