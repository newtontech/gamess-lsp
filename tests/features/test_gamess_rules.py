"""Tests for the new GAMESS-prefixed RULE diagnostics (issues #68-#75).

Each test class covers one rule, testing both the positive (triggers) and
negative (does not trigger) case.  Golden fixtures at the bottom verify
end-to-end behaviour against curated inputs.
"""

import json

import pytest

from gamess_lsp.features.lint import (
    GAMESS_CONTROL_INVALID_RUNTYP,
    GAMESS_CONTROL_INVALID_SCFTYP,
    GAMESS_CONTROL_MISSING_CONTRL,
    GAMESS_DATA_CHARGE_MULT_MISMATCH,
    GAMESS_DATA_MISSING_DATA,
    GAMESS_LOG_RUNTIME_ERROR,
    GAMESS_LOG_SCF_NOT_CONVERGED,
    GAMESS_SYNTAX_MISSING_END,
    LintProvider,
)


@pytest.fixture
def provider() -> LintProvider:
    """Create a LintProvider with a minimal LanguageServer."""
    from pygls.server import LanguageServer

    server = LanguageServer("test", "1.0")
    return LintProvider(server)


# ------------------------------------------------------------------
# GAMESS-E050: Missing $END (#68)
# ------------------------------------------------------------------


class TestMissingEnd:
    """GAMESS-E050: Group missing $END terminator."""

    def test_unclosed_contrl(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_SYNTAX_MISSING_END in codes

    def test_unclosed_basis(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF $END\n$BASIS GBASIS=STO\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_SYNTAX_MISSING_END in codes

    def test_closed_group_no_error(self, provider: LintProvider) -> None:
        text = "$CONTRL\n SCFTYP=RHF\n $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_SYNTAX_MISSING_END not in codes

    def test_diagnostic_severity_is_error(self, provider: LintProvider) -> None:
        from lsprotocol.types import DiagnosticSeverity

        text = "$CONTRL SCFTYP=RHF\n"
        for d in provider.lint(text):
            if d.code == GAMESS_SYNTAX_MISSING_END:
                assert d.severity == DiagnosticSeverity.Error
                break


# ------------------------------------------------------------------
# GAMESS-E051: Missing $CONTRL (#69)
# ------------------------------------------------------------------


class TestMissingContrl:
    """GAMESS-E051: Required $CONTRL group is missing."""

    def test_empty_input(self, provider: LintProvider) -> None:
        codes = [d.code for d in provider.lint("")]
        assert GAMESS_CONTROL_MISSING_CONTRL in codes

    def test_only_basis(self, provider: LintProvider) -> None:
        text = "$BASIS GBASIS=STO NGAUSS=3 $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_MISSING_CONTRL in codes

    def test_has_contrl(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_MISSING_CONTRL not in codes

    def test_diagnostic_at_line_0(self, provider: LintProvider) -> None:
        text = "$BASIS GBASIS=STO $END\n"
        for d in provider.lint(text):
            if d.code == GAMESS_CONTROL_MISSING_CONTRL:
                assert d.range.start.line == 0
                break


# ------------------------------------------------------------------
# GAMESS-E052: Invalid SCFTYP (#70)
# ------------------------------------------------------------------


class TestInvalidScftyp:
    """GAMESS-E052: Invalid SCFTYP value in $CONTRL."""

    def test_invalid_scftyp(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=INVALID $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_SCFTYP in codes

    def test_valid_rhf(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_SCFTYP not in codes

    def test_valid_uhf(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=UHF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_SCFTYP not in codes

    def test_valid_rohf(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=ROHF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_SCFTYP not in codes

    def test_valid_mcscf(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=MCSCF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_SCFTYP not in codes

    def test_valid_none(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=NONE RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_SCFTYP not in codes

    def test_case_insensitive(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=rhf RUNTYP=energy $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_SCFTYP not in codes

    def test_message_lists_allowed(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=BOGUS $END\n"
        for d in provider.lint(text):
            if d.code == GAMESS_CONTROL_INVALID_SCFTYP:
                assert "RHF" in d.message
                assert "UHF" in d.message
                break


# ------------------------------------------------------------------
# GAMESS-E053: Invalid RUNTYP (#71)
# ------------------------------------------------------------------


class TestInvalidRuntyp:
    """GAMESS-E053: Invalid RUNTYP value in $CONTRL."""

    def test_invalid_runtyp(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=BOGUS $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_RUNTYP in codes

    def test_valid_energy(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_RUNTYP not in codes

    def test_valid_optimize(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_RUNTYP not in codes

    def test_valid_gradient(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=GRADIENT $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_RUNTYP not in codes

    def test_valid_hessian(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=HESSIAN $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_RUNTYP not in codes

    def test_valid_sadpoint(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=SADPOINT $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_RUNTYP not in codes

    def test_no_runtyp_no_error(self, provider: LintProvider) -> None:
        """If RUNTYP is not specified, no E053 fires (different rule for missing)."""
        text = "$CONTRL SCFTYP=RHF $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_CONTROL_INVALID_RUNTYP not in codes

    def test_message_lists_allowed(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=FOO $END\n"
        for d in provider.lint(text):
            if d.code == GAMESS_CONTROL_INVALID_RUNTYP:
                assert "ENERGY" in d.message
                assert "OPTIMIZE" in d.message
                break


# ------------------------------------------------------------------
# GAMESS-E054: Missing $DATA (#72)
# ------------------------------------------------------------------


class TestMissingData:
    """GAMESS-E054: Required $DATA group is missing."""

    def test_no_data_group(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_MISSING_DATA in codes

    def test_has_data_group(self, provider: LintProvider) -> None:
        text = (
            "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
            "$DATA\nTitle\nC1\n"
            "H     1.0   0.0   0.0   0.0\n"
            " $END\n"
        )
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_MISSING_DATA not in codes

    def test_diagnostic_at_line_0(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF $END\n"
        for d in provider.lint(text):
            if d.code == GAMESS_DATA_MISSING_DATA:
                assert d.range.start.line == 0
                break


# ------------------------------------------------------------------
# GAMESS-W050: Charge/multiplicity mismatch (#73)
# ------------------------------------------------------------------


class TestChargeMultMismatch:
    """GAMESS-W050: Charge/multiplicity vs electron count mismatch."""

    def _make_input(
        self,
        mult: str = "1",
        icharg: str = "0",
        atoms: str = "H     1.0   0.0   0.0   0.0",
    ) -> str:
        return (
            f"$CONTRL SCFTYP=RHF RUNTYP=ENERGY ICHARG={icharg} MULT={mult} $END\n"
            f"$DATA\nTitle\nC1\n{atoms}\n $END\n"
        )

    def test_singlet_even_electrons_ok(self, provider: LintProvider) -> None:
        """H2: 2 electrons, MULT=1 (singlet) is valid."""
        text = self._make_input(mult="1", atoms="H     1.0   0.0   0.0   0.0\nH     1.0   0.0   0.0   0.9")
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_CHARGE_MULT_MISMATCH not in codes

    def test_doublet_odd_electrons_ok(self, provider: LintProvider) -> None:
        """H: 1 electron, MULT=2 (doublet) is valid."""
        text = self._make_input(mult="2")
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_CHARGE_MULT_MISMATCH not in codes

    def test_triplet_even_electrons_ok(self, provider: LintProvider) -> None:
        """2 electrons, MULT=3 (triplet) is valid (2 unpaired)."""
        text = self._make_input(mult="3", atoms="H     1.0   0.0   0.0   0.0\nH     1.0   0.0   0.0   0.9")
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_CHARGE_MULT_MISMATCH not in codes

    def test_doublet_even_electrons_mismatch(self, provider: LintProvider) -> None:
        """H2: 2 electrons (even), MULT=2 (doublet) requires odd electrons."""
        text = self._make_input(
            mult="2", atoms="H     1.0   0.0   0.0   0.0\nH     1.0   0.0   0.0   0.9"
        )
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_CHARGE_MULT_MISMATCH in codes

    def test_singlet_odd_electrons_mismatch(self, provider: LintProvider) -> None:
        """H: 1 electron (odd), MULT=1 (singlet) requires even electrons."""
        text = self._make_input(mult="1")
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_CHARGE_MULT_MISMATCH in codes

    def test_charged_system(self, provider: LintProvider) -> None:
        """H+: ICHARG=1, 0 electrons, MULT=1 (even/0, singlet requires even -> ok)."""
        text = self._make_input(icharg="1", mult="1")
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_CHARGE_MULT_MISMATCH not in codes

    def test_severity_is_warning(self, provider: LintProvider) -> None:
        from lsprotocol.types import DiagnosticSeverity

        text = self._make_input(mult="1")  # 1 electron, singlet
        for d in provider.lint(text):
            if d.code == GAMESS_DATA_CHARGE_MULT_MISMATCH:
                assert d.severity == DiagnosticSeverity.Warning
                break

    def test_no_geometry_no_error(self, provider: LintProvider) -> None:
        """Without geometry, the rule cannot fire."""
        text = "$CONTRL SCFTYP=RHF MULT=2 $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_DATA_CHARGE_MULT_MISMATCH not in codes


# ------------------------------------------------------------------
# GAMESS-E055: SCF not converged (#74)
# ------------------------------------------------------------------


class TestScfNotConverged:
    """GAMESS-E055: Detect SCF convergence failure in log-style output."""

    def test_scf_failed(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\nSCF FAILED TO CONVERGE\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_SCF_NOT_CONVERGED in codes

    def test_convergence_not_achieved(self, provider: LintProvider) -> None:
        text = "CONVERGENCE NOT ACHIEVED\n$CONTRL SCFTYP=RHF $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_SCF_NOT_CONVERGED in codes

    def test_max_iterations_exceeded(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF $END\nMAXIMUM NUMBER OF SCF ITERATIONS EXCEEDED\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_SCF_NOT_CONVERGED in codes

    def test_no_convergence_issue(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_SCF_NOT_CONVERGED not in codes

    def test_case_insensitive(self, provider: LintProvider) -> None:
        text = "scf failed to converge\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_SCF_NOT_CONVERGED in codes


# ------------------------------------------------------------------
# GAMESS-E056: Runtime error (#75)
# ------------------------------------------------------------------


class TestRuntimeError:
    """GAMESS-E056: Detect runtime errors in log-style output."""

    def test_fatal_error(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF $END\nFATAL ERROR IN INTEGRAL\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_RUNTIME_ERROR in codes

    def test_execution_terminated(self, provider: LintProvider) -> None:
        text = "EXECUTION OF GAMESS TERMINATED\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_RUNTIME_ERROR in codes

    def test_bad_input(self, provider: LintProvider) -> None:
        text = "BAD INPUT DETECTED\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_RUNTIME_ERROR in codes

    def test_no_runtime_error(self, provider: LintProvider) -> None:
        text = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_RUNTIME_ERROR not in codes

    def test_case_insensitive(self, provider: LintProvider) -> None:
        text = "fatal error\n"
        codes = [d.code for d in provider.lint(text)]
        assert GAMESS_LOG_RUNTIME_ERROR in codes

    def test_multiple_errors_on_different_lines(self, provider: LintProvider) -> None:
        text = "FATAL ERROR\nEXECUTION OF GAMESS TERMINATED\n"
        error_count = sum(
            1 for d in provider.lint(text) if d.code == GAMESS_LOG_RUNTIME_ERROR
        )
        assert error_count == 2


# ------------------------------------------------------------------
# Golden fixtures
# ------------------------------------------------------------------


class TestGoldenFixtures:
    """End-to-end tests with curated GAMESS inputs."""

    def test_valid_water_optimization(self, provider: LintProvider) -> None:
        """Well-formed water optimization should have no GAMESS-prefixed errors."""
        text = (
            " $CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE COORD=UNIQUE $END\n"
            " $BASIS GBASIS=N31 NGAUSS=6 $END\n"
            " $SYSTEM MWORDS=100 $END\n"
            " $STATPT OPTTOL=0.0001 NSTEP=50 $END\n"
            " $DATA\n"
            "Water optimization\n"
            "C1\n"
            "O     8.0   0.000000   0.000000   0.117489\n"
            "H     1.0   0.000000   0.757210  -0.469957\n"
            "H     1.0   0.000000  -0.757210  -0.469957\n"
            " $END\n"
        )
        gamess_codes = [
            d.code
            for d in provider.lint(text)
            if d.code and d.code.startswith("GAMESS-")
        ]
        assert gamess_codes == []

    def test_minimal_input_triggers_e051_e054(self, provider: LintProvider) -> None:
        """Empty input triggers missing CONTRL and missing DATA."""
        codes = [d.code for d in provider.lint("")]
        assert GAMESS_CONTROL_MISSING_CONTRL in codes
        assert GAMESS_DATA_MISSING_DATA in codes

    def test_snapshot_includes_gamess_codes(self, provider: LintProvider) -> None:
        """Snapshot JSON includes GAMESS-prefixed codes."""
        snap = provider.snapshot("file:///test.inp", "")
        json_str = json.dumps(snap, sort_keys=True)
        assert "GAMESS-E051" in json_str
        assert "GAMESS-E054" in json_str

    def test_all_rules_in_manifest(self, provider: LintProvider) -> None:
        """Verify all rule codes are used consistently."""
        from gamess_lsp.features.agent_api import AgentAPIProvider

        api = AgentAPIProvider()
        manifest = api.get_rule_manifest()
        manifest_codes = {r["code"] for r in manifest["rules"]}
        expected = {
            GAMESS_SYNTAX_MISSING_END,
            GAMESS_CONTROL_MISSING_CONTRL,
            GAMESS_CONTROL_INVALID_SCFTYP,
            GAMESS_CONTROL_INVALID_RUNTYP,
            GAMESS_DATA_MISSING_DATA,
            GAMESS_DATA_CHARGE_MULT_MISMATCH,
            GAMESS_LOG_SCF_NOT_CONVERGED,
            GAMESS_LOG_RUNTIME_ERROR,
        }
        assert manifest_codes == expected
