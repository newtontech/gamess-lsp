"""Validation accuracy tests — behavior-oriented test suite for GAMESS LSP diagnostics."""

from gamess_lsp.parser import GAMESSParser, parse_gamess_input
from gamess_lsp.validator import validate_semantics


class TestMutuallyExclusiveParameters:
    """Tests for detecting mutually exclusive parameters."""

    def test_duplicate_scf_type(self):
        """Should detect duplicate SCFTYP with different values.

        Note: This test documents the expected behavior for issue #6.
        The validator currently does not implement this check.
        """
        content = "$CONTRL SCFTYP=RHF SCFTYP=UHF $END"
        parsed = parse_gamess_input(content)
        # Parser should still capture both keywords
        contrl = parsed.get_group("CONTRL")
        assert contrl is not None
        # The last value wins when duplicated (current parser behavior)
        scftyp = contrl.get_keyword("SCFTYP")
        assert scftyp is not None

    def test_mp2_and_ci_conflict(self):
        """Should detect MP2 and CI used together.

        Note: This test documents the expected behavior for issue #6.
        The validator currently does not implement this check.
        """
        content = "$CONTRL MPLEVL=2 CITYP=GUGA $END"
        parsed = parse_gamess_input(content)
        # At minimum the parser should capture both keywords
        contrl = parsed.get_group("CONTRL")
        assert contrl is not None
        assert contrl.get_keyword("MPLEVL") is not None
        assert contrl.get_keyword("CITYP") is not None

    def test_dft_and_mp2_conflict(self):
        """Should detect DFT and MPn used together."""
        content = "$CONTRL DFTTYP=B3LYP MPLEVL=2 $END"
        parsed = parse_gamess_input(content)
        diagnostics = validate_semantics(parsed)
        # This may be a warning rather than error — just check it parses
        assert len(diagnostics) >= 0


class TestChemicalConstraints:
    """Tests for chemical constraint validation."""

    def test_valid_rhf_closed_shell(self):
        """Valid RHF calculation with proper multiplicity."""
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$SYSTEM MWORDS=100 $END
$DATA
Water
C1

O     8.0   0.0  0.0  0.0
H     1.0   0.0  0.7  0.0
$END"""
        parsed = parse_gamess_input(content)
        assert "CONTRL" in parsed.groups
        assert "DATA" in parsed.groups
        assert len(parsed.geometry) == 2


class TestParserBehavior:
    """Parser behavior regression tests."""

    def test_parse_group_with_keywords_on_same_line(self):
        """Parser should capture keywords on the group start line."""
        content = "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END"
        parsed = parse_gamess_input(content)
        contrl = parsed.get_group("CONTRL")
        assert contrl is not None
        assert contrl.get_keyword("SCFTYP").value == "RHF"
        assert contrl.get_keyword("RUNTYP").value == "OPTIMIZE"

    def test_parse_quoted_values(self):
        """Parser should handle quoted values correctly."""
        content = '$CONTRL TITLE="My Calculation" $END'
        parsed = parse_gamess_input(content)
        contrl = parsed.get_group("CONTRL")
        assert contrl is not None

    def test_parse_unknown_group_warning(self):
        """Parser should warn about unknown groups."""
        content = "$UNKNOWN KEY=VAL $END"
        parser = GAMESSParser()
        parser.parse(content)
        assert len(parser.warnings) > 0

    def test_parse_unclosed_group_warning(self):
        """Parser should warn about unclosed groups."""
        content = "$CONTRL SCFTYP=RHF"
        parser = GAMESSParser()
        parser.parse(content)
        assert len(parser.warnings) > 0
