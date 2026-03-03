"""Integration tests for GAMESS LSP features."""

import pytest
from gamess_lsp.parser import GamessParser
from gamess_lsp.diagnostics import GamessDiagnostics
from gamess_lsp.groups import get_group_documentation, get_parameter_documentation
from gamess_lsp.data_parser import DataGroupParser
from gamess_lsp.document_symbols import DocumentSymbolProvider
from gamess_lsp.folding import FoldingRangeProvider


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_workflow_water(self):
        """Test complete workflow with water molecule."""
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY MAXIT=50 MULT=1 $END
$SYSTEM MEMORY=1000000 $END
$BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
$SCF CONV=1.0E-06 DIIS=.TRUE. $END
$DATA
Water molecule
Cnv 2

O  8.0   0.000000   0.000000   0.117790
H  1.0   0.000000   0.755453  -0.471161
H  1.0   0.000000  -0.755453  -0.471161
$END
$GUESS GUESS=HUCKEL $END"""
        
        # Parse
        parser = GamessParser()
        groups, parse_errors = parser.parse(content)
        assert len(groups) == 6
        assert len(parse_errors) == 0
        
        # Validate with diagnostics
        diagnostics = GamessDiagnostics()
        diag_results = diagnostics.validate(content)
        errors = [d for d in diag_results if d.severity.value == 1]
        assert len(errors) == 0  # No errors for valid input
        
        # Check document symbols
        symbol_provider = DocumentSymbolProvider()
        symbols = symbol_provider.get_document_symbols(content)
        assert len(symbols) == 6
        assert symbols[0].name == "$CONTRL"
        
        # Check folding ranges
        folding_provider = FoldingRangeProvider()
        folds = folding_provider.get_folding_ranges(content)
        assert len(folds) >= 1  # Should have at least DATA group folding
    
    def test_dft_calculation_integration(self):
        """Test DFT calculation setup."""
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY DFTTYP=B3LYP $END
$BASIS GBASIS=CC-PVDZ $END
$DFT METHOD=B3LYP GRID=FINE $END
$DATA
Methane
Td

C 6.0 0.0 0.0 0.0
$END"""
        
        parser = GamessParser()
        groups, errors = parser.parse(content)
        
        # Should parse all groups
        group_names = [g.name for g in groups]
        assert "CONTRL" in group_names
        assert "BASIS" in group_names
        assert "DFT" in group_names
        assert "DATA" in group_names
        
        # Check DFT parameters
        dft_group = next(g for g in groups if g.name == "DFT")
        param_names = [p.name for p in dft_group.parameters]
        assert "METHOD" in param_names
        assert "GRID" in param_names
    
    def test_optimization_integration(self):
        """Test geometry optimization setup."""
        content = """$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END
$STATPT NSTEP=100 OPTTOL=0.0001 $END
$BASIS GBASIS=N31 NGAUSS=6 $END
$DATA
Test
C1

O 8.0 0.0 0.0 0.0
$END"""
        
        parser = GamessParser()
        groups, errors = parser.parse(content)
        
        contrl = next(g for g in groups if g.name == "CONTRL")
        runtyp_param = next(p for p in contrl.parameters if p.name == "RUNTYP")
        assert runtyp_param.value == "OPTIMIZE"
        
        statpt = next(g for g in groups if g.name == "STATPT")
        assert len(statpt.parameters) == 2
    
    def test_data_group_with_symmetry(self):
        """Test DATA group with different symmetries."""
        symmetries = ["C1", "Cs", "Ci", "C2", "C2v", "C2h", "D2h", "Td", "Oh"]
        
        for sym in symmetries:
            content = f"""$DATA
Test
{sym}
O 8.0 0.0 0.0 0.0
$END"""
            parser = DataGroupParser()
            lines = content.split('\n')
            result = parser.parse_data_group(lines, 1, len(lines))
            assert result is not None
            assert result.symmetry == sym
    
    def test_documentation_lookup(self):
        """Test documentation lookup integration."""
        # Test group documentation
        contrl_doc = get_group_documentation("CONTRL")
        assert contrl_doc is not None
        assert contrl_doc.required
        
        # Test parameter documentation
        scftyp_doc = get_parameter_documentation("CONTRL", "SCFTYP")
        assert scftyp_doc is not None
        assert "RHF" in scftyp_doc.valid_values
        
        # Test case insensitivity
        assert get_group_documentation("contrl") is not None
        assert get_parameter_documentation("CONTRL", "scftyp") is not None
    
    def test_error_recovery(self):
        """Test parser error recovery."""
        content = """$CONTRL SCFTYP=RHF
$BASIS GBASIS=N31 $END
$END"""
        
        parser = GamessParser()
        groups, errors = parser.parse(content)
        
        # Should still parse some groups despite errors
        assert len(groups) >= 2
        # Should report errors
        assert len(errors) >= 1


class TestRealWorldExamples:
    """Tests based on real GAMESS input files."""
    
    def test_complex_molecule(self):
        """Test parsing of a complex molecule input."""
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY MPLEVL=2 $END
$SYSTEM MEMORY=4000000 TIMLIM=600 $END
$BASIS GBASIS=CC-PVTZ $END
$MP2 METHOD=SEMI $END
$DATA
Benzene dimer
C1

C   6.0   1.390000   0.000000   0.000000
C   6.0   0.695000   1.203785   0.000000
C   6.0  -0.695000   1.203785   0.000000
C   6.0  -1.390000   0.000000   0.000000
C   6.0  -0.695000  -1.203785   0.000000
C   6.0   0.695000  -1.203785   0.000000
H   1.0   2.470000   0.000000   0.000000
H   1.0   1.235000   2.139078   0.000000
H   1.0  -1.235000   2.139078   0.000000
H   1.0  -2.470000   0.000000   0.000000
H   1.0  -1.235000  -2.139078   0.000000
H   1.0   1.235000  -2.139078   0.000000
$END"""
        
        parser = GamessParser()
        groups, errors = parser.parse(content)
        
        assert len(groups) == 5
        assert len(errors) == 0
        
        data_group = next(g for g in groups if g.name == "DATA")
        # Should have parsed DATA group correctly
        assert data_group.end_line > data_group.start_line
    
    def test_multiline_group_format(self):
        """Test traditional multiline GAMESS format."""
        content = """ $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
 $SYSTEM MEMORY=1000000 $END
 $BASIS GBASIS=N31 NGAUSS=6 $END
 $DATA
Water
C1
O 8.0 0.0 0.0 0.0
H 1.0 0.757 0.586 0.0
H 1.0 -0.757 0.586 0.0
 $END"""
        
        parser = GamessParser()
        groups, errors = parser.parse(content)
        
        # Should handle leading spaces
        assert len(groups) == 4
        assert len(errors) == 0
