"""Tests for GAMESS document symbols."""

import pytest
from gamess_lsp.document_symbols import DocumentSymbolProvider


class TestDocumentSymbols:
    """Test cases for document symbol provider."""
    
    def test_empty_document(self):
        provider = DocumentSymbolProvider()
        symbols = provider.get_document_symbols("")
        assert len(symbols) == 0
    
    def test_single_group(self):
        provider = DocumentSymbolProvider()
        content = """$CONTRL SCFTYP=RHF $END"""
        symbols = provider.get_document_symbols(content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "$CONTRL"
        assert symbols[0].kind.value == 2  # Module
        assert len(symbols[0].children) == 1
        assert symbols[0].children[0].name == "SCFTYP"
    
    def test_multiple_groups(self):
        provider = DocumentSymbolProvider()
        content = """$CONTRL SCFTYP=RHF $END
$BASIS GBASIS=N31 $END
$SYSTEM MEMORY=1000 $END"""
        symbols = provider.get_document_symbols(content)
        
        assert len(symbols) == 3
        assert symbols[0].name == "$CONTRL"
        assert symbols[1].name == "$BASIS"
        assert symbols[2].name == "$SYSTEM"
    
    def test_multiline_group(self):
        provider = DocumentSymbolProvider()
        content = """$CONTRL
   SCFTYP=RHF
   RUNTYP=ENERGY
   MAXIT=50
$END"""
        symbols = provider.get_document_symbols(content)
        
        assert len(symbols) == 1
        assert symbols[0].name == "$CONTRL"
        assert len(symbols[0].children) == 3
        assert symbols[0].children[0].name == "SCFTYP"
        assert symbols[0].children[1].name == "RUNTYP"
        assert symbols[0].children[2].name == "MAXIT"
    
    def test_group_detail(self):
        provider = DocumentSymbolProvider()
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"""
        symbols = provider.get_document_symbols(content)
        
        assert "2 parameters" in symbols[0].detail


class TestDocumentSymbolsRanges:
    """Test document symbol ranges."""
    
    def test_group_range(self):
        provider = DocumentSymbolProvider()
        content = """$CONTRL
   SCFTYP=RHF
$END"""
        symbols = provider.get_document_symbols(content)
        
        # Range should cover the entire group
        assert symbols[0].range.start.line == 0
        assert symbols[0].range.end.line == 2
    
    def test_parameter_range(self):
        provider = DocumentSymbolProvider()
        content = """$CONTRL SCFTYP=RHF $END"""
        symbols = provider.get_document_symbols(content)
        
        param = symbols[0].children[0]
        assert param.name == "SCFTYP"
        assert param.range.start.line == 0
        assert param.range.start.character >= 0
