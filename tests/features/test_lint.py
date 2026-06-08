"""Tests for the LintProvider feature.

Covers structure rules, schema rules, best-practice rules, snapshot
serialisation, and determinism.
"""

import json

import pytest

from gamess_lsp.features.lint import (
    LINT_BOOLEAN_FORMAT,
    LINT_DUPLICATE_KEYWORD,
    LINT_INVALID_ENUM,
    LINT_LOW_MEMORY,
    LINT_MISSING_BASIS,
    LINT_MISSING_CONTRL,
    LINT_MISSING_DATA,
    LINT_MISSING_RUNTYP,
    LINT_MISSING_SYSTEM,
    LINT_NUMERIC_RANGE,
    LINT_REDUNDANT_DEFAULT,
    LINT_UNCLOSED_GROUP,
    LINT_UNKNOWN_KEYWORD,
    LintProvider,
)


@pytest.fixture
def provider() -> LintProvider:
    """Create a LintProvider with a minimal LanguageServer."""
    from pygls.server import LanguageServer

    server = LanguageServer("test", "1.0")
    return LintProvider(server)


# ------------------------------------------------------------------
# Provider instantiation
# ------------------------------------------------------------------


class TestProviderExists:
    """Sanity checks that the provider can be created."""

    def test_provider_not_none(self, provider: LintProvider) -> None:
        assert provider is not None

    def test_provider_has_server(self, provider: LintProvider) -> None:
        assert provider.server is not None


# ------------------------------------------------------------------
# Empty / minimal input
# ------------------------------------------------------------------


class TestEmptyInput:
    """Lint for empty or blank documents."""

    def test_empty_string_has_structure_errors(self, provider: LintProvider) -> None:
        diagnostics = provider.lint("")
        # Should flag missing $CONTRL and $DATA
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_CONTRL in codes
        assert LINT_MISSING_DATA in codes

    def test_whitespace_only(self, provider: LintProvider) -> None:
        diagnostics = provider.lint("   \n  \n")
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_CONTRL in codes

    def test_comment_only(self, provider: LintProvider) -> None:
        diagnostics = provider.lint("! This is a comment\n")
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_CONTRL in codes


# ------------------------------------------------------------------
# Structure rules
# ------------------------------------------------------------------


class TestStructureRules:
    """Tests for structure-level lint rules."""

    def test_missing_contrl(self, provider: LintProvider) -> None:
        text = "$BASIS GBASIS=STO NGAUSS=3 $END\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_CONTRL in codes

    def test_missing_data(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_DATA in codes

    def test_unclosed_group(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_UNCLOSED_GROUP in codes

    def test_properly_closed_group_no_unclosed_warning(self, provider: LintProvider) -> None:
        """Multi-line group closed with $END should not flag LINT_UNCLOSED_GROUP."""
        text = "$CONTRL\n SCFTYP=RHF RUNTYP=ENERGY\n $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_UNCLOSED_GROUP not in codes


# ------------------------------------------------------------------
# Schema rules
# ------------------------------------------------------------------


class TestSchemaRules:
    """Tests for schema-level lint rules."""

    def test_unknown_keyword(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF BOGUSKEY=TRUE $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_UNKNOWN_KEYWORD in codes

    def test_known_keyword_no_warning(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_UNKNOWN_KEYWORD not in codes

    def test_invalid_enum_value(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=INVALID $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_INVALID_ENUM in codes

    def test_valid_enum_no_error(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_INVALID_ENUM not in codes

    def test_numeric_range_out_of_bounds(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF MAXIT=-5 $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_NUMERIC_RANGE in codes

    def test_numeric_range_in_bounds(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF MAXIT=100 $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_NUMERIC_RANGE not in codes

    def test_boolean_format_missing_dots(self, provider: LintProvider) -> None:
        text = "$SCF DIIS=TRUE $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_BOOLEAN_FORMAT in codes

    def test_boolean_format_correct_dots(self, provider: LintProvider) -> None:
        text = "$SCF DIIS=.TRUE. $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_BOOLEAN_FORMAT not in codes


# ------------------------------------------------------------------
# Best-practice rules
# ------------------------------------------------------------------


class TestBestPracticeRules:
    """Tests for best-practice lint rules."""

    def test_missing_runtyp(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_RUNTYP in codes

    def test_has_runtyp_no_warning(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_RUNTYP not in codes

    def test_missing_basis(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_BASIS in codes

    def test_has_basis_no_warning(self, provider: LintProvider) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$BASIS GBASIS=STO NGAUSS=3 $END\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_BASIS not in codes

    def test_missing_system(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_MISSING_SYSTEM in codes

    def test_low_memory_warning(self, provider: LintProvider) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=2 $END\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_LOW_MEMORY in codes

    def test_adequate_memory_no_warning(self, provider: LintProvider) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$SYSTEM MWORDS=100 $END\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_LOW_MEMORY not in codes

    def test_redundant_default(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY EXETYP=RUN $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_REDUNDANT_DEFAULT in codes

    def test_non_default_value_no_redundant(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY EXETYP=CHECK $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_REDUNDANT_DEFAULT not in codes

    def test_system_without_mwords(self, provider: LintProvider) -> None:
        text = "$SYSTEM TIMLIM=60 $END"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert LINT_LOW_MEMORY in codes


# ------------------------------------------------------------------
# Valid input -- should not produce lint errors
# ------------------------------------------------------------------


class TestValidInput:
    """Well-formed GAMESS input should not produce lint errors or warnings."""

    def test_full_valid_calculation(self, provider: LintProvider) -> None:
        text = (
            "$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END\n"
            "$SYSTEM MWORDS=100 $END\n"
            "$BASIS GBASIS=CC-PVDZ $END\n"
            "$STATPT OPTTOL=0.0001 NSTEP=50 $END\n"
            "$DATA\n"
            "Water molecule\n"
            "C1\n"
            "\n"
            "O     8.0   0.000000   0.000000   0.117489\n"
            "H     1.0   0.000000   0.757210  -0.469957\n"
            "H     1.0   0.000000  -0.757210  -0.469957\n"
            " $END\n"
        )
        diagnostics = provider.lint(text)
        # Should have no errors or warnings (may have hints/information)
        errors_and_warnings = [
            d for d in diagnostics
            if d.severity in (1, 2)  # Error=1, Warning=2
        ]
        assert len(errors_and_warnings) == 0


# ------------------------------------------------------------------
# Snapshot (JSON serialisation)
# ------------------------------------------------------------------


class TestSnapshot:
    """Tests for the snapshot/snapshot_json methods."""

    def test_snapshot_structure(self, provider: LintProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$CONTRL SCFTYP=RHF $END")
        assert "uri" in snap
        assert "version" in snap
        assert "source" in snap
        assert "diagnostics" in snap
        assert snap["uri"] == "file:///test.inp"
        assert snap["source"] == "gamess-lsp-lint"
        assert isinstance(snap["diagnostics"], list)

    def test_snapshot_empty_diagnostics(self, provider: LintProvider) -> None:
        # Empty input still has structure errors
        snap = provider.snapshot("file:///test.inp", "")
        assert len(snap["diagnostics"]) >= 1

    def test_snapshot_with_diagnostics(self, provider: LintProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$CONTRL SCFTYP=INVALID $END")
        assert len(snap["diagnostics"]) >= 1
        diag = snap["diagnostics"][0]
        assert "range" in diag
        assert "severity" in diag
        assert "source" in diag
        assert "message" in diag
        assert "code" in diag

    def test_snapshot_json_is_valid_json(self, provider: LintProvider) -> None:
        json_str = provider.snapshot_json("file:///test.inp", "$CONTRL SCFTYP=RHF $END")
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "diagnostics" in parsed

    def test_snapshot_deterministic(self, provider: LintProvider) -> None:
        """Two calls with the same input must produce identical output."""
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"
        snap1 = provider.snapshot("file:///test.inp", text)
        snap2 = provider.snapshot("file:///test.inp", text)
        assert snap1 == snap2

    def test_snapshot_json_deterministic(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=INVALID $END"
        json1 = provider.snapshot_json("file:///test.inp", text)
        json2 = provider.snapshot_json("file:///test.inp", text)
        assert json1 == json2

    def test_snapshot_source_is_lint(self, provider: LintProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$CONTRL SCFTYP=INVALID $END")
        sources = {d["source"] for d in snap["diagnostics"]}
        assert sources == {"gamess-lsp-lint"}

    def test_snapshot_range_structure(self, provider: LintProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$CONTRL SCFTYP=RHF BOGUSKEY=X $END")
        for diag in snap["diagnostics"]:
            rng = diag["range"]
            assert "start" in rng
            assert "end" in rng
            assert "line" in rng["start"]
            assert "character" in rng["start"]


# ------------------------------------------------------------------
# Diagnostics sorting / determinism
# ------------------------------------------------------------------


class TestDeterminism:
    """Ensure diagnostics ordering is deterministic."""

    def test_multiple_diagnostics_sorted(self, provider: LintProvider) -> None:
        text = (
            "$CONTRL SCFTYP=RHF BOGUS=TRUE $END\n"
            "$UNKNOWN $END\n"
        )
        d1 = provider.lint(text)
        d2 = provider.lint(text)
        assert len(d1) == len(d2)
        for a, b in zip(d1, d2):
            assert a.range.start.line == b.range.start.line
            assert a.message == b.message
            assert a.severity == b.severity


# ------------------------------------------------------------------
# Diagnostics carry rule codes
# ------------------------------------------------------------------


class TestRuleCodes:
    """All lint diagnostics must carry a string code."""

    def test_all_diagnostics_have_code(self, provider: LintProvider) -> None:
        text = (
            "$CONTRL SCFTYP=RHF BOGUS=TRUE EXETYP=RUN $END\n"
            "$SYSTEM MWORDS=2 $END\n"
        )
        diagnostics = provider.lint(text)
        for d in diagnostics:
            assert d.code is not None
            assert isinstance(d.code, str)
            assert d.code.startswith("LINT_")

    def test_all_diagnostics_have_lint_source(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF $END"
        diagnostics = provider.lint(text)
        for d in diagnostics:
            assert d.source == "gamess-lsp-lint"
