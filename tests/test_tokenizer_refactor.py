"""Tests for the shared parse_keyword_pairs tokenizer (issue #66).

Verifies that the consolidated keyword parsing function correctly handles
all GAMESS input formats, including edge cases.
"""

import pytest

from gamess_lsp.tokenizer import parse_keyword_pairs, tokenize_line


# ------------------------------------------------------------------
# tokenize_line (existing, verify still works)
# ------------------------------------------------------------------


class TestTokenizeLine:
    """Low-level tokenization still works after refactor."""

    def test_simple_pairs(self) -> None:
        assert tokenize_line("SCFTYP=RHF RUNTYP=ENERGY") == [
            "SCFTYP=RHF",
            "RUNTYP=ENERGY",
        ]

    def test_quoted_values(self) -> None:
        tokens = tokenize_line('TITLE="My Title"')
        assert tokens == ['TITLE="My Title"']

    def test_empty_line(self) -> None:
        assert tokenize_line("") == []

    def test_only_spaces(self) -> None:
        assert tokenize_line("   ") == []


# ------------------------------------------------------------------
# parse_keyword_pairs (new consolidated function)
# ------------------------------------------------------------------


class TestParseKeywordPairs:
    """parse_keyword_pairs extracts (name, value) tuples."""

    def test_simple_pairs(self) -> None:
        result = parse_keyword_pairs("SCFTYP=RHF RUNTYP=ENERGY")
        assert result == [("SCFTYP", "RHF"), ("RUNTYP", "ENERGY")]

    def test_boolean_values(self) -> None:
        result = parse_keyword_pairs("DIIS=.TRUE. SOSCF=.FALSE.")
        assert result == [("DIIS", ".TRUE."), ("SOSCF", ".FALSE.")]

    def test_numeric_values(self) -> None:
        result = parse_keyword_pairs("MWORDS=100 TIMLIM=60")
        assert result == [("MWORDS", "100"), ("TIMLIM", "60")]

    def test_scientific_notation(self) -> None:
        result = parse_keyword_pairs("CONV=1.0E-05")
        assert result == [("CONV", "1.0E-05")]

    def test_quoted_values(self) -> None:
        result = parse_keyword_pairs('TITLE="My Calculation"')
        assert result == [("TITLE", "My Calculation")]

    def test_empty_line(self) -> None:
        assert parse_keyword_pairs("") == []

    def test_only_spaces(self) -> None:
        assert parse_keyword_pairs("   ") == []

    def test_token_without_equals(self) -> None:
        """Tokens without = are returned with empty value."""
        result = parse_keyword_pairs("STANDALONE")
        assert result == [("STANDALONE", "")]

    def test_mixed_with_equals_and_without(self) -> None:
        result = parse_keyword_pairs("SCFTYP=RHF NOSYM")
        assert result == [("SCFTYP", "RHF"), ("NOSYM", "")]

    def test_standalone_equals_merged(self) -> None:
        """KEY = VALUE (with spaces around =) is merged correctly."""
        result = parse_keyword_pairs("SCFTYP = RHF")
        assert result == [("SCFTYP", "RHF")]

    def test_multiple_standalone_equals(self) -> None:
        result = parse_keyword_pairs("SCFTYP = RHF RUNTYP = ENERGY")
        assert result == [("SCFTYP", "RHF"), ("RUNTYP", "ENERGY")]

    def test_negative_value(self) -> None:
        result = parse_keyword_pairs("ICHARG=-1")
        assert result == [("ICHARG", "-1")]

    def test_complex_line(self) -> None:
        result = parse_keyword_pairs(
            "SCFTYP=RHF RUNTYP=OPTIMIZE ICHARG=0 MULT=1 COORD=UNIQUE"
        )
        assert len(result) == 5
        assert result[0] == ("SCFTYP", "RHF")
        assert result[4] == ("COORD", "UNIQUE")

    def test_strip_quotes_single(self) -> None:
        result = parse_keyword_pairs("TITLE='My Title'")
        assert result == [("TITLE", "My Title")]

    def test_strip_quotes_double(self) -> None:
        result = parse_keyword_pairs('TITLE="My Title"')
        assert result == [("TITLE", "My Title")]


# ------------------------------------------------------------------
# Integration: parser uses shared function
# ------------------------------------------------------------------


class TestParserUsesSharedTokenizer:
    """Verify the parser correctly uses the shared parse_keyword_pairs."""

    def test_parse_keyword_pairs(self) -> None:
        from gamess_lsp.parser import parse_gamess_input

        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        parsed = parse_gamess_input(text)
        contrl = parsed.get_group("CONTRL")
        assert contrl is not None
        assert contrl.get_keyword("SCFTYP").value == "RHF"
        assert contrl.get_keyword("RUNTYP").value == "ENERGY"

    def test_parse_boolean_values(self) -> None:
        from gamess_lsp.parser import parse_gamess_input

        text = "$SCF DIIS=.TRUE. SOSCF=.FALSE. $END\n"
        parsed = parse_gamess_input(text)
        scf = parsed.get_group("SCF")
        assert scf.get_keyword("DIIS").value == ".TRUE."
        assert scf.get_keyword("SOSCF").value == ".FALSE."

    def test_parse_multiple_groups(self) -> None:
        from gamess_lsp.parser import parse_gamess_input

        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$BASIS GBASIS=STO NGAUSS=3 $END\n"
            "$SYSTEM MWORDS=100 TIMLIM=60 $END\n"
        )
        parsed = parse_gamess_input(text)
        assert "CONTRL" in parsed.groups
        assert "BASIS" in parsed.groups
        assert "SYSTEM" in parsed.groups
        assert parsed.get_group("SYSTEM").get_keyword("MWORDS").value == "100"
