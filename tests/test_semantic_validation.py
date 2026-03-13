"""Tests for semantic validation."""

import pytest

from gamess_lsp.parser import GAMESSParser
from gamess_lsp.validator import SemanticValidator, validate_semantics


class TestSCFTYPMultValidation:
    """Test SCFTYP vs MULT compatibility validation."""

    def test_rhf_with_mult_1_is_valid(self):
        """RHF with MULT=1 (singlet) is valid."""
        content = """
 $CONTRL SCFTYP=RHF MULT=1 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
H     1.0   0.0   0.74  0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        # Should not have SCFTYP_MULT_INCOMPAT error
        codes = [d.code for d in diagnostics]
        assert "SCFTYP_MULT_INCOMPAT" not in codes

    def test_rhf_with_mult_2_is_error(self):
        """RHF with MULT=2 (doublet) is invalid - RHF only for closed-shell."""
        content = """
 $CONTRL SCFTYP=RHF MULT=2 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        # Should have SCFTYP_MULT_INCOMPAT error
        codes = [d.code for d in diagnostics]
        assert "SCFTYP_MULT_INCOMPAT" in codes

        # Check error message
        error = next(d for d in diagnostics if d.code == "SCFTYP_MULT_INCOMPAT")
        assert "RHF" in error.message
        assert "MULT=2" in error.message
        assert error.severity == "error"

    def test_uhf_with_any_mult_is_valid(self):
        """UHF accepts any multiplicity."""
        for mult in [1, 2, 3, 4]:
            content = f"""
 $CONTRL SCFTYP=UHF MULT={mult} RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
 $END
"""
            parser = GAMESSParser()
            parsed = parser.parse(content)
            diagnostics = validate_semantics(parsed)

            codes = [d.code for d in diagnostics]
            assert "SCFTYP_MULT_INCOMPAT" not in codes, f"Failed for MULT={mult}"

    def test_rohf_with_mult_1_is_error(self):
        """ROHF with MULT=1 is invalid - ROHF requires open-shell."""
        content = """
 $CONTRL SCFTYP=ROHF MULT=1 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "SCFTYP_MULT_INCOMPAT" in codes

    def test_rohf_with_mult_2_is_valid(self):
        """ROHF with MULT=2 (doublet) is valid."""
        content = """
 $CONTRL SCFTYP=ROHF MULT=2 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "SCFTYP_MULT_INCOMPAT" not in codes


class TestElectronMultiplicityValidation:
    """Test electron count vs multiplicity validation."""

    def test_singlet_with_even_electrons_is_valid(self):
        """Singlet (MULT=1) with even electron count is valid."""
        content = """
 $CONTRL SCFTYP=RHF MULT=1 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
H2 molecule
C1
H     1.0   0.0   0.0   0.0
H     1.0   0.0   0.74  0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "ELECTRON_MULT_MISMATCH" not in codes

    def test_doublet_with_odd_electrons_is_valid(self):
        """Doublet (MULT=2) with odd electron count is valid."""
        content = """
 $CONTRL SCFTYP=UHF MULT=2 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
H atom
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "ELECTRON_MULT_MISMATCH" not in codes

    def test_singlet_with_odd_electrons_is_error(self):
        """Singlet (MULT=1) with odd electron count is invalid."""
        content = """
 $CONTRL SCFTYP=UHF MULT=1 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
H atom
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "ELECTRON_MULT_MISMATCH" in codes

    def test_open_shell_system_with_rhf_is_error(self):
        """Open-shell system (odd electrons) with RHF should raise error."""
        content = """
 $CONTRL SCFTYP=RHF MULT=2 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
H atom
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        # Should have both SCFTYP_MULT_INCOMPAT and OPEN_SHELL_RHF
        assert "OPEN_SHELL_RHF" in codes


class TestMethodCompatibility:
    """Test method parameter compatibility validation."""

    def test_dft_with_mp2_is_error(self):
        """DFTTYP with MPLEVL=2 is incompatible."""
        content = """
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP MPLEVL=2 RUNTYP=ENERGY $END
 $BASIS GBASIS=CC-PVDZ $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "INCOMPAT_DFT_MP2" in codes

    def test_dft_with_cc_is_error(self):
        """DFTTYP with CCTYP is incompatible."""
        content = """
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP CCTYP=CCSD(T) RUNTYP=ENERGY $END
 $BASIS GBASIS=CC-PVDZ $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "INCOMPAT_DFT_CC" in codes

    def test_rohf_dft_is_warning(self):
        """ROHF-DFT is not recommended and should raise warning."""
        content = """
 $CONTRL SCFTYP=ROHF DFTTYP=B3LYP RUNTYP=ENERGY $END
 $BASIS GBASIS=CC-PVDZ $END
 $DATA
Test
C1
O     8.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "WARN_ROHF_DFT" in codes

        # Check it's a warning, not error
        diag = next(d for d in diagnostics if d.code == "WARN_ROHF_DFT")
        assert diag.severity == "warning"

    def test_valid_dft_calculation(self):
        """Valid DFT calculation should have no errors."""
        content = """
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=ENERGY $END
 $BASIS GBASIS=CC-PVDZ $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
H     1.0   0.0   0.74  0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        # Filter out warnings, only check errors
        errors = [d for d in diagnostics if d.severity == "error"]
        assert len(errors) == 0


class TestRequiredGroups:
    """Test required groups validation."""

    def test_optimize_without_statpt_is_warning(self):
        """RUNTYP=OPTIMIZE without $STATPT should raise warning."""
        content = """
 $CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
H     1.0   0.0   0.74  0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "MISSING_STATPT" in codes

    def test_irc_without_irc_group_is_error(self):
        """RUNTYP=IRC without $IRC group should raise error."""
        content = """
 $CONTRL SCFTYP=RHF RUNTYP=IRC $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Test
C1
H     1.0   0.0   0.0   0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        codes = [d.code for d in diagnostics]
        assert "MISSING_IRC" in codes

        # Check it's an error
        diag = next(d for d in diagnostics if d.code == "MISSING_IRC")
        assert diag.severity == "error"


class TestIntegration:
    """Integration tests for complex scenarios."""

    def test_realistic_dft_optimization(self):
        """A realistic DFT optimization should have no errors."""
        content = """
! Water molecule DFT optimization
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS=CC-PVDZ $END
 $STATPT OPTTOL=0.0001 NSTEP=50 $END
 $DATA
Water molecule
Cnv 2

O     8.0   0.000000   0.000000   0.117489
H     1.0   0.000000   0.757210  -0.469957
H     1.0   0.000000  -0.757210  -0.469957
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        # Should have no errors
        errors = [d for d in diagnostics if d.severity == "error"]
        assert len(errors) == 0

    def test_charged_system(self):
        """Charged system should correctly count electrons."""
        # Cation with 1 electron removed
        content = """
 $CONTRL SCFTYP=RHF ICHARG=1 MULT=2 RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
H2+ cation
C1
H     1.0   0.0   0.0   0.0
H     1.0   0.0   0.74  0.0
 $END
"""
        parser = GAMESSParser()
        parsed = parser.parse(content)
        diagnostics = validate_semantics(parsed)

        # H2 has 2 electrons, minus 1 charge = 1 electron (odd)
        # MULT=2 is correct for 1 unpaired electron
        codes = [d.code for d in diagnostics]
        assert "ELECTRON_MULT_MISMATCH" not in codes