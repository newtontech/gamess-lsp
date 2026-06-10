"""Tests for the DiagnosticProvider feature.

Covers empty input, valid input, warning-level diagnostics, error-level
diagnostics, and JSON-serialisable snapshot determinism.
"""

import json

import pytest

from gamess_lsp.features.diagnostic import DiagnosticProvider


@pytest.fixture
def provider() -> DiagnosticProvider:
    """Create a DiagnosticProvider with a minimal LanguageServer."""
    from pygls.server import LanguageServer

    server = LanguageServer("test", "1.0")
    return DiagnosticProvider(server)


# ------------------------------------------------------------------
# Provider instantiation
# ------------------------------------------------------------------


class TestProviderExists:
    """Sanity checks that the provider can be created."""

    def test_provider_not_none(self, provider: DiagnosticProvider) -> None:
        assert provider is not None

    def test_provider_has_server(self, provider: DiagnosticProvider) -> None:
        assert provider.server is not None


# ------------------------------------------------------------------
# Empty / minimal input
# ------------------------------------------------------------------


class TestEmptyInput:
    """Diagnostics for empty or blank documents."""

    def test_empty_string_no_diagnostics(self, provider: DiagnosticProvider) -> None:
        diagnostics = provider.get_diagnostics("")
        assert isinstance(diagnostics, list)
        # Empty input triggers missing required group diagnostics from typecheck
        assert all(d.source == "gamess-lsp-typecheck" for d in diagnostics)

    def test_whitespace_only_no_diagnostics(self, provider: DiagnosticProvider) -> None:
        diagnostics = provider.get_diagnostics("   \n  \n")
        # Whitespace input triggers missing required group diagnostics from typecheck
        assert all(d.source == "gamess-lsp-typecheck" for d in diagnostics)

    def test_comment_only_no_diagnostics(self, provider: DiagnosticProvider) -> None:
        diagnostics = provider.get_diagnostics("! This is a comment\n")
        # Comment-only input triggers missing required group diagnostics from typecheck
        assert all(d.source == "gamess-lsp-typecheck" for d in diagnostics)


# ------------------------------------------------------------------
# Valid input (no diagnostics expected)
# ------------------------------------------------------------------


class TestValidInput:
    """Valid GAMESS input should produce no diagnostics."""

    def test_valid_contrl(self, provider: DiagnosticProvider) -> None:
        text = "$CONTRL\n SCFTYP=RHF RUNTYP=ENERGY\n $END"
        diagnostics = provider.get_diagnostics(text)
        assert isinstance(diagnostics, list)
        # Missing $DATA triggers typecheck diagnostic; no syntax/semantic errors
        assert all(d.source == "gamess-lsp-typecheck" for d in diagnostics)

    def test_valid_multi_group(self, provider: DiagnosticProvider) -> None:
        text = (
            "$CONTRL\n SCFTYP=RHF RUNTYP=ENERGY\n $END\n"
            "$SYSTEM\n MWORDS=100\n $END\n"
            "$BASIS\n GBASIS=STO NGAUSS=3\n $END\n"
        )
        diagnostics = provider.get_diagnostics(text)
        assert isinstance(diagnostics, list)
        # Missing $DATA triggers typecheck diagnostic; no syntax/semantic errors
        assert all(d.source == "gamess-lsp-typecheck" for d in diagnostics)

    def test_valid_full_calculation(self, provider: DiagnosticProvider) -> None:
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
        diagnostics = provider.get_diagnostics(text)
        assert isinstance(diagnostics, list)
        # No errors expected for valid input
        errors = [d for d in diagnostics if d.severity == 1]  # Error = 1
        assert len(errors) == 0


# ------------------------------------------------------------------
# Warning-level diagnostics
# ------------------------------------------------------------------


class TestWarningDiagnostics:
    """Tests for warning-severity diagnostics."""

    def test_unknown_group_warning(self, provider: DiagnosticProvider) -> None:
        text = "$UNKNOWN $END"
        diagnostics = provider.get_diagnostics(text)
        assert len(diagnostics) >= 1
        messages = [d.message for d in diagnostics]
        assert any("Unknown group" in m for m in messages)

    def test_unclosed_group_warning(self, provider: DiagnosticProvider) -> None:
        text = "$CONTRL SCFTYP=RHF"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("not properly closed" in m for m in messages)

    def test_unknown_keyword_warning(self, provider: DiagnosticProvider) -> None:
        text = "$CONTRL SCFTYP=RHF BOGUSKEY=TRUE $END"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("Unknown keyword" in m for m in messages)


# ------------------------------------------------------------------
# Error-level diagnostics
# ------------------------------------------------------------------


class TestErrorDiagnostics:
    """Tests for error-severity diagnostics."""

    def test_invalid_contrl_value(self, provider: DiagnosticProvider) -> None:
        text = "$CONTRL SCFTYP=INVALID $END"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("Invalid value" in m for m in messages)

    def test_incompatible_dft_mp2(self, provider: DiagnosticProvider) -> None:
        """DFTTYP and MPLEVL=2 are mutually exclusive."""
        text = "$CONTRL SCFTYP=RHF DFTTYP=B3LYP MPLEVL=2 $END"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("DFT" in m and "MP2" in m for m in messages)

    def test_incompatible_dft_cc(self, provider: DiagnosticProvider) -> None:
        """DFTTYP and CCTYP are mutually exclusive."""
        text = "$CONTRL SCFTYP=RHF DFTTYP=B3LYP CCTYP=CCSD $END"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("DFT" in m and "Coupled Cluster" in m for m in messages)

    def test_invalid_basis_value(self, provider: DiagnosticProvider) -> None:
        text = "$BASIS GBASIS=INVALID $END"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("Invalid value" in m and "GBASIS" in m for m in messages)


# ------------------------------------------------------------------
# Snapshot (JSON serialisation)
# ------------------------------------------------------------------


class TestSnapshot:
    """Tests for the snapshot/snapshot_json methods."""

    def test_snapshot_structure(self, provider: DiagnosticProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$CONTRL SCFTYP=RHF $END")
        assert "uri" in snap
        assert "version" in snap
        assert "diagnostics" in snap
        assert snap["uri"] == "file:///test.inp"
        assert isinstance(snap["diagnostics"], list)

    def test_snapshot_empty_diagnostics(self, provider: DiagnosticProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "")
        # Empty input triggers missing required group diagnostics
        assert len(snap["diagnostics"]) >= 1
        assert all(d["source"] == "gamess-lsp-typecheck" for d in snap["diagnostics"])

    def test_snapshot_with_diagnostics(self, provider: DiagnosticProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$UNKNOWN $END")
        assert len(snap["diagnostics"]) >= 1
        diag = snap["diagnostics"][0]
        assert "range" in diag
        assert "severity" in diag
        assert "source" in diag
        assert "message" in diag

    def test_snapshot_json_is_valid_json(self, provider: DiagnosticProvider) -> None:
        json_str = provider.snapshot_json("file:///test.inp", "$CONTRL SCFTYP=RHF $END")
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "diagnostics" in parsed

    def test_snapshot_deterministic(self, provider: DiagnosticProvider) -> None:
        """Two calls with the same input must produce identical output."""
        text = "$CONTRL SCFTYP=RHF DFTTYP=B3LYP MPLEVL=2 $END"
        snap1 = provider.snapshot("file:///test.inp", text)
        snap2 = provider.snapshot("file:///test.inp", text)
        assert snap1 == snap2

    def test_snapshot_json_deterministic(self, provider: DiagnosticProvider) -> None:
        text = "$CONTRL SCFTYP=INVALID $END"
        json1 = provider.snapshot_json("file:///test.inp", text)
        json2 = provider.snapshot_json("file:///test.inp", text)
        assert json1 == json2

    def test_snapshot_error_has_error_severity(self, provider: DiagnosticProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$CONTRL SCFTYP=INVALID $END")
        severities = [d["severity"] for d in snap["diagnostics"]]
        assert "error" in severities

    def test_snapshot_warning_has_warning_severity(self, provider: DiagnosticProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$UNKNOWN $END")
        severities = [d["severity"] for d in snap["diagnostics"]]
        assert "warning" in severities

    def test_snapshot_code_present(self, provider: DiagnosticProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$CONTRL SCFTYP=INVALID $END")
        codes = [d["code"] for d in snap["diagnostics"] if d.get("code")]
        assert len(codes) >= 1

    def test_snapshot_source_is_gamess_lsp(self, provider: DiagnosticProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$CONTRL SCFTYP=INVALID $END")
        sources = {d["source"] for d in snap["diagnostics"]}
        assert "gamess-lsp" in sources

    def test_snapshot_range_structure(self, provider: DiagnosticProvider) -> None:
        snap = provider.snapshot("file:///test.inp", "$UNKNOWN $END")
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

    def test_multiple_diagnostics_sorted(self, provider: DiagnosticProvider) -> None:
        """Diagnostics from multiple sources must be consistently ordered."""
        text = "$CONTRL SCFTYP=RHF DFTTYP=B3LYP MPLEVL=2 RUNTYP=IRC $END\n" "$UNKNOWN $END\n"
        d1 = provider.get_diagnostics(text)
        d2 = provider.get_diagnostics(text)
        # Must produce the same list each time
        assert len(d1) == len(d2)
        for a, b in zip(d1, d2):
            assert a.range.start.line == b.range.start.line
            assert a.message == b.message
            assert a.severity == b.severity
