"""Tests for GAMESS folding range provider."""

import pytest
from gamess_lsp.folding import FoldingRangeProvider


class TestFoldingRanges:
    """Test cases for folding range provider."""
    
    def test_empty_document(self):
        provider = FoldingRangeProvider()
        ranges = provider.get_folding_ranges("")
        assert len(ranges) == 0
    
    def test_single_group_folding(self):
        provider = FoldingRangeProvider()
        content = """$CONTRL
   SCFTYP=RHF
   RUNTYP=ENERGY
$END"""
        ranges = provider.get_folding_ranges(content)
        
        assert len(ranges) == 1
        assert ranges[0].start_line == 0
        assert ranges[0].end_line == 3
    
    def test_multiple_groups_folding(self):
        provider = FoldingRangeProvider()
        content = """$CONTRL SCFTYP=RHF $END
$BASIS
   GBASIS=N31
   NGAUSS=6
$END
$SYSTEM MEMORY=1000 $END"""
        ranges = provider.get_folding_ranges(content)
        
        # Should have 1 folding range (only for multi-line BASIS group)
        # Single-line groups don't get folding ranges
        assert len(ranges) == 1
        assert ranges[0].start_line == 1  # BASIS starts at line 1
        assert ranges[0].end_line == 4
    
    def test_inline_group_no_folding(self):
        provider = FoldingRangeProvider()
        content = """$CONTRL SCFTYP=RHF $END"""
        ranges = provider.get_folding_ranges(content)
        
        # Single line group should not have folding range
        assert len(ranges) == 0
    
    def test_data_group_folding(self):
        provider = FoldingRangeProvider()
        content = """$DATA
Water
C1
O 8.0 0 0 0
$END"""
        ranges = provider.get_folding_ranges(content)
        
        assert len(ranges) == 1
        assert ranges[0].start_line == 0
        assert ranges[0].end_line == 4
    
    def test_folding_kind(self):
        provider = FoldingRangeProvider()
        content = """$CONTRL
   SCFTYP=RHF
$END"""
        ranges = provider.get_folding_ranges(content)
        
        assert ranges[0].kind.value == "region"
