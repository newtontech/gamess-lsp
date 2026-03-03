"""Tests for GAMESS diagnostics."""

import pytest
from lsprotocol.types import DiagnosticSeverity

from gamess_lsp.diagnostics import GamessDiagnostics


class TestDiagnostics:
    """Test cases for diagnostics."""
    
    def test_empty_file(self):
        diag = GamessDiagnostics()
        diagnostics = diag.validate("")
        assert len(diagnostics) == 0
    
    def test_valid_input(self):
        diag = GamessDiagnostics()
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$DATA
Test
C1
O 8.0 0 0 0
$END
"""
        diagnostics = diag.validate(content)
        # Should have no errors for valid input
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert len(errors) == 0
    
    def test_unknown_group(self):
        diag = GamessDiagnostics()
        content = "$UNKNOWN PARAM=VALUE $END"
        diagnostics = diag.validate(content)
        
        warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.Warning]
        assert len(warnings) >= 1
        assert "Unknown" in warnings[0].message
    
    def test_unclosed_group(self):
        diag = GamessDiagnostics()
        content = "$CONTRL SCFTYP=RHF"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert len(errors) >= 1
        assert any("Unclosed" in d.message for d in errors)
    
    def test_missing_required_group(self):
        diag = GamessDiagnostics()
        content = "$SYSTEM MEMORY=1000000 $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert len(errors) >= 1
        assert any("CONTRL" in d.message and "missing" in d.message.lower() for d in errors)
    
    def test_unknown_parameter(self):
        diag = GamessDiagnostics()
        content = "$CONTRL UNKNOWNPARAM=VALUE $END"
        diagnostics = diag.validate(content)
        
        warnings = [d for d in diagnostics if d.severity == DiagnosticSeverity.Warning]
        assert len(warnings) >= 1
        assert any("Unknown parameter" in d.message for d in warnings)


class TestParameterTypeValidation:
    """Test parameter type validation."""
    
    def test_valid_integer(self):
        diag = GamessDiagnostics()
        content = "$CONTRL MAXIT=50 $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "integer" in d.message.lower()]
        assert len(errors) == 0
    
    def test_invalid_integer(self):
        diag = GamessDiagnostics()
        content = "$CONTRL MAXIT=INVALID $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "integer" in d.message.lower()]
        assert len(errors) >= 1
    
    def test_valid_real(self):
        diag = GamessDiagnostics()
        content = "$SCF CONV=1.0E-06 $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "real" in d.message.lower()]
        assert len(errors) == 0
    
    def test_invalid_real(self):
        diag = GamessDiagnostics()
        content = "$SCF CONV=INVALID $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "real" in d.message.lower()]
        assert len(errors) >= 1
    
    def test_valid_logical(self):
        diag = GamessDiagnostics()
        content = "$SCF DIIS=.TRUE. $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "logical" in d.message.lower()]
        assert len(errors) == 0
    
    def test_invalid_logical(self):
        diag = GamessDiagnostics()
        content = "$SCF DIIS=INVALID $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "logical" in d.message.lower()]
        assert len(errors) >= 1


class TestValueValidation:
    """Test valid value validation."""
    
    def test_valid_scftyp(self):
        diag = GamessDiagnostics()
        content = "$CONTRL SCFTYP=RHF $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "Invalid value" in d.message]
        assert len(errors) == 0
    
    def test_invalid_scftyp(self):
        diag = GamessDiagnostics()
        content = "$CONTRL SCFTYP=INVALID $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "Invalid value" in d.message]
        assert len(errors) >= 1
        assert "SCFTYP" in errors[0].message
    
    def test_valid_runtyp(self):
        diag = GamessDiagnostics()
        content = "$CONTRL RUNTYP=OPTIMIZE $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "Invalid value" in d.message]
        assert len(errors) == 0
    
    def test_invalid_runtyp(self):
        diag = GamessDiagnostics()
        content = "$CONTRL RUNTYP=INVALID $END"
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics if "Invalid value" in d.message]
        assert len(errors) >= 1


class TestDataGroupDiagnostics:
    """Test $DATA group specific diagnostics."""
    
    def test_data_group_missing_title(self):
        diag = GamessDiagnostics()
        content = """$DATA
$END
"""
        diagnostics = diag.validate(content)
        
        errors = [d for d in diagnostics]
        # Should report empty data group
        assert len(errors) >= 1
    
    def test_data_group_invalid_symmetry(self):
        diag = GamessDiagnostics()
        content = """$DATA
Test
INVALID 1
O 8.0 0 0 0
$END
"""
        diagnostics = diag.validate(content)
        
        # Should have warnings about unknown symmetry
        warnings = [d for d in diagnostics if "symmetry" in d.message.lower()]
        assert len(warnings) >= 1
    
    def test_data_group_wrong_atomic_number(self):
        diag = GamessDiagnostics()
        content = """$CONTRL SCFTYP=RHF $END
$DATA
Test
C1
O 6.0 0 0 0
$END
"""
        diagnostics = diag.validate(content)
        
        # Should have warning about atomic number mismatch
        warnings = [d for d in diagnostics if "mismatch" in d.message.lower()]
        assert len(warnings) >= 1


class TestQuickFixes:
    """Test quick fix suggestions."""
    
    def test_quick_fix_invalid_value(self):
        diag = GamessDiagnostics()
        content = "$CONTRL SCFTYP=XXX $END"
        diagnostics = diag.validate(content)
        
        invalid_value_diagnostics = [d for d in diagnostics if "Invalid value" in d.message]
        if invalid_value_diagnostics:
            fixes = diag.get_quick_fixes(invalid_value_diagnostics[0], content)
            assert len(fixes) > 0
            assert any("RHF" in fix[1] for fix in fixes)
