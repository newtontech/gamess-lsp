"""Tests for the TypecheckProvider feature.

Covers:
- Required group validation ($CONTRL, $DATA)
- Enum value validation (SCFTYP, RUNTYP, GBASIS, etc.)
- Boolean type checking
- Integer type checking (positive and general)
- Float / numeric type checking
- Unit annotations in diagnostics
- Valid inputs that should produce no typecheck diagnostics
"""

import pytest

from gamess_lsp.features.typecheck import TypecheckProvider
from gamess_lsp.parser import GAMESSParser

# Shorter alias for severity constant
from lsprotocol.types import DiagnosticSeverity

_ERROR = DiagnosticSeverity.Error
_WARNING = DiagnosticSeverity.Warning


@pytest.fixture
def provider() -> TypecheckProvider:
    """Create a TypecheckProvider instance."""
    return TypecheckProvider()


def _parse_and_validate(text: str) -> list:
    """Parse text, run typecheck validation, and return diagnostics."""
    parser = GAMESSParser()
    parsed = parser.parse(text)
    provider = TypecheckProvider()
    return provider.validate(parsed)


def _messages(diagnostics: list) -> list[str]:
    """Extract messages from a diagnostic list."""
    return [d.message for d in diagnostics]


def _codes(diagnostics: list) -> list[str]:
    """Extract codes from a diagnostic list."""
    return [str(d.code) for d in diagnostics if d.code]


def _sources(diagnostics: list) -> set[str]:
    """Extract unique sources from a diagnostic list."""
    return {d.source for d in diagnostics if d.source}


# ------------------------------------------------------------------
# Provider instantiation
# ------------------------------------------------------------------


class TestProviderExists:
    """Sanity checks that the provider can be created."""

    def test_provider_not_none(self, provider: TypecheckProvider) -> None:
        assert provider is not None


# ------------------------------------------------------------------
# Required groups
# ------------------------------------------------------------------


class TestRequiredGroups:
    """Validate missing required group detection."""

    def test_missing_contrl_group(self) -> None:
        """$CONTRL is always required."""
        text = "$SYSTEM MWORDS=100 $END"
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("$CONTRL group is required" in m for m in msgs)

    def test_missing_data_group(self) -> None:
        """$DATA is always required."""
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("$DATA group is required" in m for m in msgs)

    def test_both_groups_present_no_missing_error(self) -> None:
        """No missing-group errors when both $CONTRL and $DATA are present."""
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$DATA\nTitle\nC1\n\nO 8.0 0.0 0.0 0.0\n $END\n"
        )
        diagnostics = _parse_and_validate(text)
        missing_codes = [c for c in _codes(diagnostics) if c == "MISSING_REQUIRED_GROUP"]
        assert len(missing_codes) == 0

    def test_missing_group_code(self) -> None:
        """Diagnostics have code MISSING_REQUIRED_GROUP."""
        text = "$SYSTEM MWORDS=100 $END"
        diagnostics = _parse_and_validate(text)
        assert "MISSING_REQUIRED_GROUP" in _codes(diagnostics)

    def test_missing_group_source(self) -> None:
        """Missing-group diagnostics use the typecheck source."""
        text = "$SYSTEM MWORDS=100 $END"
        diagnostics = _parse_and_validate(text)
        assert "gamess-lsp-typecheck" in _sources(diagnostics)


# ------------------------------------------------------------------
# Enum validation
# ------------------------------------------------------------------


class TestEnumValidation:
    """Validate enum value checking."""

    def test_invalid_scftyp(self) -> None:
        text = "$CONTRL SCFTYP=BADVALUE RUNTYP=ENERGY $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Invalid value" in m and "SCFTYP" in m for m in msgs)

    def test_valid_scftyp_no_error(self) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        enum_errors = [c for c in _codes(diagnostics) if c == "INVALID_ENUM"]
        assert len(enum_errors) == 0

    def test_invalid_runtyp(self) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=BOGUS $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Invalid value" in m and "RUNTYP" in m for m in msgs)

    def test_invalid_gbasis(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$BASIS GBASIS=FAKE $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Invalid value" in m and "GBASIS" in m for m in msgs)

    def test_invalid_scftyp_lists_allowed_values(self) -> None:
        """Error message should list allowed values."""
        text = "$CONTRL SCFTYP=BADVALUE $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        enum_msgs = [m for m in msgs if "SCFTYP" in m and "Invalid value" in m]
        assert len(enum_msgs) >= 1
        assert "RHF" in enum_msgs[0]
        assert "UHF" in enum_msgs[0]

    def test_enum_case_insensitive(self) -> None:
        """Enum matching should be case-insensitive (valid lowercase)."""
        text = "$CONTRL SCFTYP=rhf RUNTYP=energy $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        enum_errors = [c for c in _codes(diagnostics) if c == "INVALID_ENUM"]
        assert len(enum_errors) == 0

    def test_enum_diagnostic_code(self) -> None:
        text = "$CONTRL SCFTYP=BAD $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        assert "INVALID_ENUM" in _codes(diagnostics)

    def test_enum_diagnostic_source(self) -> None:
        text = "$CONTRL SCFTYP=BAD $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        assert "gamess-lsp-typecheck" in _sources(diagnostics)

    def test_enum_diagnostic_range_points_to_value(self) -> None:
        """The diagnostic range should target the value, not the whole line."""
        text = "$CONTRL SCFTYP=BAD $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        enum_diags = [d for d in diagnostics if d.code == "INVALID_ENUM"]
        assert len(enum_diags) >= 1
        diag = enum_diags[0]
        # Value column should be after "SCFTYP="
        assert diag.range.start.character >= 6  # len("SCFTYP") + 1

    def test_statpt_method_enum(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
            "$STATPT METHOD=INVALID $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Invalid value" in m and "METHOD" in m for m in msgs)

    def test_pcm_solvnt_enum(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$PCM SOLVNT=INVALID $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Invalid value" in m and "SOLVNT" in m for m in msgs)


# ------------------------------------------------------------------
# Boolean type validation
# ------------------------------------------------------------------


class TestBooleanType:
    """Validate boolean keyword type checking."""

    def test_invalid_boolean_value(self) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=YES $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Expected boolean" in m and "NOSYM" in m for m in msgs)

    def test_valid_boolean_true(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=.TRUE. $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        bool_errors = [m for m in _messages(diagnostics) if "NOSYM" in m and "boolean" in m.lower()]
        assert len(bool_errors) == 0

    def test_valid_boolean_false(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=.FALSE. $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        bool_errors = [m for m in _messages(diagnostics) if "NOSYM" in m and "boolean" in m.lower()]
        assert len(bool_errors) == 0

    def test_valid_boolean_one(self) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=1 $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        bool_errors = [m for m in _messages(diagnostics) if "NOSYM" in m and "boolean" in m.lower()]
        assert len(bool_errors) == 0

    def test_valid_boolean_zero(self) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=0 $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        bool_errors = [m for m in _messages(diagnostics) if "NOSYM" in m and "boolean" in m.lower()]
        assert len(bool_errors) == 0

    def test_boolean_diagnostic_code(self) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=YES $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        assert "TYPE_BOOLEAN" in _codes(diagnostics)

    def test_scf_dirscf_boolean(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SCF DIRSCF=MAYBE $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Expected boolean" in m and "DIRSCF" in m for m in msgs)

    def test_basis_diffsp_boolean(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$BASIS GBASIS=STO NGAUSS=3 DIFFSP=ON $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Expected boolean" in m and "DIFFSP" in m for m in msgs)


# ------------------------------------------------------------------
# Integer type validation
# ------------------------------------------------------------------


class TestIntegerType:
    """Validate integer keyword type checking."""

    def test_non_integer_mwords(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=abc $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Expected positive integer" in m and "MWORDS" in m for m in msgs)

    def test_float_mwords(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=1.5 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Expected positive integer" in m and "MWORDS" in m for m in msgs)

    def test_valid_integer_mwords(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=100 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        int_errors = [m for m in _messages(diagnostics) if "MWORDS" in m and "integer" in m.lower()]
        assert len(int_errors) == 0

    def test_zero_mwords(self) -> None:
        """MWORDS must be positive; zero should be flagged."""
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=0 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("positive integer" in m and "MWORDS" in m for m in msgs)

    def test_negative_mwords(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=-5 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("positive integer" in m and "MWORDS" in m for m in msgs)

    def test_integer_diagnostic_code(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=abc $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        assert "TYPE_INTEGER" in _codes(diagnostics)

    def test_negative_icharg_allowed(self) -> None:
        """ICHARG can be negative (anion). It is a general integer, not positive-only."""
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY ICHARG=-1 $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        int_errors = [m for m in _messages(diagnostics) if "ICHARG" in m and "integer" in m.lower()]
        assert len(int_errors) == 0

    def test_statpt_nstep_non_integer(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
            "$STATPT NSTEP=many $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Expected positive integer" in m and "NSTEP" in m for m in msgs)

    def test_ispher_negative_one_allowed(self) -> None:
        """ISPHER accepts -1 (general integer, not positive-only)."""
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY ISPHER=-1 $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        int_errors = [m for m in _messages(diagnostics) if "ISPHER" in m and "integer" in m.lower()]
        assert len(int_errors) == 0


# ------------------------------------------------------------------
# Float / numeric type validation
# ------------------------------------------------------------------


class TestFloatType:
    """Validate float keyword type checking."""

    def test_non_numeric_opttol(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
            "$STATPT OPTTOL=small $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Expected numeric" in m and "OPTTOL" in m for m in msgs)

    def test_valid_float_opttol(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
            "$STATPT OPTTOL=0.0001 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        float_errors = [
            m for m in _messages(diagnostics) if "OPTTOL" in m and "numeric" in m.lower()
        ]
        assert len(float_errors) == 0

    def test_scientific_notation_opttol(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
            "$STATPT OPTTOL=1.0E-4 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        float_errors = [
            m for m in _messages(diagnostics) if "OPTTOL" in m and "numeric" in m.lower()
        ]
        assert len(float_errors) == 0

    def test_scientific_notation_lowercase(self) -> None:
        """GAMESS accepts lowercase 'e' and 'd' in scientific notation."""
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
            "$STATPT OPTTOL=1.0e-4 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        float_errors = [
            m for m in _messages(diagnostics) if "OPTTOL" in m and "numeric" in m.lower()
        ]
        assert len(float_errors) == 0

    def test_d_notation(self) -> None:
        """GAMESS Fortran-style 'D' exponent notation."""
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
            "$STATPT OPTTOL=1.0D-4 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        float_errors = [
            m for m in _messages(diagnostics) if "OPTTOL" in m and "numeric" in m.lower()
        ]
        assert len(float_errors) == 0

    def test_numeric_diagnostic_code(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
            "$STATPT OPTTOL=bad $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        assert "TYPE_NUMERIC" in _codes(diagnostics)

    def test_force_temp_non_numeric(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=HESSIAN $END\n"
            "$FORCE TEMP=room $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("Expected numeric" in m and "TEMP" in m for m in msgs)

    def test_ccconv_float(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY CCTYP=CCSD $END\n"
            "$CC CCCONV=1.0E-06 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        float_errors = [
            m for m in _messages(diagnostics) if "CCCONV" in m and "numeric" in m.lower()
        ]
        assert len(float_errors) == 0


# ------------------------------------------------------------------
# Unit annotations
# ------------------------------------------------------------------


class TestUnitAnnotations:
    """Validate that unit hints appear in diagnostic messages."""

    def test_mwords_unit_in_error(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=bad $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        mwords_msgs = [m for m in msgs if "MWORDS" in m]
        assert len(mwords_msgs) >= 1
        assert "million words" in mwords_msgs[0]

    def test_temp_unit_in_error(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=HESSIAN $END\n"
            "$FORCE TEMP=bad $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        temp_msgs = [m for m in msgs if "TEMP" in m]
        assert len(temp_msgs) >= 1
        assert "Kelvin" in temp_msgs[0]

    def test_timlim_unit_in_error(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM TIMLIM=forever $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        timlim_msgs = [m for m in msgs if "TIMLIM" in m]
        assert len(timlim_msgs) >= 1
        assert "minutes" in timlim_msgs[0]


# ------------------------------------------------------------------
# Valid inputs (no typecheck errors)
# ------------------------------------------------------------------


class TestValidInput:
    """Valid inputs should produce no typecheck diagnostics."""

    def test_minimal_valid(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$DATA\nTitle\nC1\n\nO 8.0 0.0 0.0 0.0\n $END\n"
        )
        diagnostics = _parse_and_validate(text)
        assert len(diagnostics) == 0

    def test_full_valid_calculation(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END\n"
            "$SYSTEM MWORDS=100 $END\n"
            "$BASIS GBASIS=CC-PVDZ $END\n"
            "$STATPT OPTTOL=0.0001 NSTEP=50 $END\n"
            "$DATA\nWater\nC1\n\n"
            "O 8.0 0.0 0.0 0.117\n"
            "H 1.0 0.0 0.757 -0.470\n"
            "H 1.0 0.0 -0.757 -0.470\n"
            " $END\n"
        )
        diagnostics = _parse_and_validate(text)
        assert len(diagnostics) == 0

    def test_valid_mp2(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY MPLEVL=2 $END\n"
            "$SYSTEM MWORDS=100 $END\n"
            "$BASIS GBASIS=CC-PVDZ $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END\n"
        )
        diagnostics = _parse_and_validate(text)
        assert len(diagnostics) == 0

    def test_valid_ccsd(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY CCTYP=CCSD(T) $END\n"
            "$SYSTEM MWORDS=100 MEMDDI=1000 $END\n"
            "$BASIS GBASIS=CC-PVTZ $END\n"
            "$CC NCORE=0 MAXCC=100 CCCONV=1.0E-06 $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END\n"
        )
        diagnostics = _parse_and_validate(text)
        assert len(diagnostics) == 0

    def test_valid_pcm(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END\n"
            "$PCM SOLVNT=WATER RSOLV=1.0 $END\n"
            "$BASIS GBASIS=CC-PVDZ $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END\n"
        )
        diagnostics = _parse_and_validate(text)
        assert len(diagnostics) == 0

    def test_valid_tddft(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=ENERGY $END\n"
            "$TDDFT NSTATE=5 IROOT=1 CVG=1.0E-05 $END\n"
            "$BASIS GBASIS=CC-PVDZ $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END\n"
        )
        diagnostics = _parse_and_validate(text)
        assert len(diagnostics) == 0


# ------------------------------------------------------------------
# Multiple errors
# ------------------------------------------------------------------


class TestMultipleErrors:
    """Verify that multiple errors are reported correctly."""

    def test_multiple_type_errors(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=YES MAXIT=five $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        msgs = _messages(diagnostics)
        assert any("boolean" in m.lower() and "NOSYM" in m for m in msgs)
        assert any("integer" in m.lower() and "MAXIT" in m for m in msgs)

    def test_enum_and_type_errors(self) -> None:
        text = "$CONTRL SCFTYP=BAD RUNTYP=WORSE NOSYM=YES $END\n" "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        codes = _codes(diagnostics)
        assert "INVALID_ENUM" in codes
        assert "TYPE_BOOLEAN" in codes


# ------------------------------------------------------------------
# Diagnostic source
# ------------------------------------------------------------------


class TestDiagnosticSource:
    """All typecheck diagnostics should carry the correct source."""

    def test_all_diagnostics_use_typecheck_source(self) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=YES MAXIT=bad $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = _parse_and_validate(text)
        assert len(diagnostics) > 0
        for d in diagnostics:
            assert d.source == "gamess-lsp-typecheck"

    def test_severity_is_error(self) -> None:
        text = "$CONTRL SCFTYP=BAD $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = _parse_and_validate(text)
        for d in diagnostics:
            assert d.severity == DiagnosticSeverity.Error


# ------------------------------------------------------------------
# Integration with DiagnosticProvider
# ------------------------------------------------------------------


class TestDiagnosticProviderIntegration:
    """Verify typecheck diagnostics flow through the DiagnosticProvider."""

    def test_typecheck_errors_in_provider(self) -> None:
        from pygls.server import LanguageServer
        from gamess_lsp.features.diagnostic import DiagnosticProvider

        server = LanguageServer("test", "1.0")
        provider = DiagnosticProvider(server)

        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY NOSYM=YES $END\n$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        diagnostics = provider.get_diagnostics(text)
        sources = {d.source for d in diagnostics if d.source}
        assert "gamess-lsp-typecheck" in sources

    def test_typecheck_and_semantic_errors_coexist(self) -> None:
        from pygls.server import LanguageServer
        from gamess_lsp.features.diagnostic import DiagnosticProvider

        server = LanguageServer("test", "1.0")
        provider = DiagnosticProvider(server)

        # DFT+MP2 (semantic error) + invalid boolean (typecheck error)
        text = (
            "$CONTRL SCFTYP=RHF DFTTYP=B3LYP MPLEVL=2 NOSYM=YES $END\n"
            "$DATA\nT\nC1\n\nO 8 0 0 0\n $END"
        )
        diagnostics = provider.get_diagnostics(text)
        sources = {d.source for d in diagnostics if d.source}
        msgs = [d.message for d in diagnostics]
        assert "gamess-lsp-typecheck" in sources
        assert "gamess-lsp" in sources
        assert any("boolean" in m.lower() and "NOSYM" in m for m in msgs)
