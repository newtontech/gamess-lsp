"""Tests for closed-loop fixtures, fix operation, and output/log diagnostics.

This module implements the requirements from issue #86:
- Golden fixtures for valid/invalid inputs and runtime output/log files
- Tests that run the agent CLI against fixtures and assert stable DiagnosticEnvelope/v1
- Fix operation as preview patch/action plan
- Output/log diagnostics support
- OpenQC smoke evidence
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gamess_lsp import tool
from gamess_lsp.output_parser import (
    parse_output_file,
    diagnostic_to_dict,
    CODE_SCF_CONVERGENCE_FAILURE,
    CODE_MEMORY_ERROR,
    CODE_CALCULATION_SUCCESS,
)

FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT_FIXTURES = FIXTURES / "gamess_output"
CASE_DIR_FIXTURES = FIXTURES / "gamess_case_directory"
CASE_INVALID_FIXTURES = FIXTURES / "gamess_case_invalid"


class TestFixOperation:
    """Tests for the fix operation with preview patches."""

    def test_fix_operation_returns_actions(self, capsys) -> None:
        rc = tool.main(["fix", str(FIXTURES / "invalid_unclosed_group.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["capabilities"]["operation"] == "fix"
        assert "actions" in payload
        assert isinstance(payload["actions"], list)

    def test_fix_operation_has_required_fields(self, capsys) -> None:
        rc = tool.main(["fix", str(FIXTURES / "invalid_unclosed_group.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        for action in payload["actions"]:
            assert "title" in action
            assert "kind" in action
            assert "diagnostic_code" in action
            assert "confidence" in action
            assert "blocking" in action
            assert "safe_to_auto_apply" in action
            assert "edit" in action

    def test_fix_operation_on_valid_fixture_has_no_actions(self, capsys) -> None:
        rc = tool.main(["fix", str(FIXTURES / "valid_water_dft.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["actions"] == []

    def test_fix_operation_returns_diagnostic_envelope_v1(self, capsys) -> None:
        rc = tool.main(["fix", str(FIXTURES / "invalid_missing_contrl.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["diagnostic_envelope"] == "v1"
        assert payload["diagnostic_engine"] == "1.0"
        assert payload["software"] == "gamess"

    def test_fix_operation_status_available_when_actions_exist(self, capsys) -> None:
        rc = tool.main(["fix", str(FIXTURES / "invalid_bad_scftyp.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["capabilities"]["status"] == "available"

    def test_fix_operation_status_unavailable_when_no_actions(self, capsys) -> None:
        rc = tool.main(["fix", str(FIXTURES / "valid_hf_sp.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["capabilities"]["status"] == "unavailable"


class TestOutputLogDiagnostics:
    """Tests for output/log file parsing and diagnostics."""

    def test_parse_successful_output(self) -> None:
        path = OUTPUT_FIXTURES / "sample_output.log"
        diagnostics = parse_output_file(path)
        codes = {d.code for d in diagnostics}
        assert CODE_CALCULATION_SUCCESS in codes

    def test_parse_convergence_failure(self) -> None:
        path = OUTPUT_FIXTURES / "convergence_failure.log"
        diagnostics = parse_output_file(path)
        codes = {d.code for d in diagnostics}
        assert CODE_SCF_CONVERGENCE_FAILURE in codes

    def test_parse_memory_error(self) -> None:
        path = OUTPUT_FIXTURES / "memory_error.log"
        diagnostics = parse_output_file(path)
        codes = {d.code for d in diagnostics}
        assert CODE_MEMORY_ERROR in codes

    def test_output_diagnostics_have_envelope_fields(self) -> None:
        path = OUTPUT_FIXTURES / "convergence_failure.log"
        diagnostics = parse_output_file(path)
        for diag in diagnostics:
            result = diagnostic_to_dict(diag)
            assert "code" in result
            assert "severity" in result
            assert "message" in result
            assert "line" in result
            assert "range" in result
            assert "blocking" in result
            assert "facts" in result
            assert "fix_hints" in result
            assert "source_provenance" in result

    def test_convergence_failure_is_blocking(self) -> None:
        path = OUTPUT_FIXTURES / "convergence_failure.log"
        diagnostics = parse_output_file(path)
        convergence_diag = next(d for d in diagnostics if d.code == CODE_SCF_CONVERGENCE_FAILURE)
        assert convergence_diag.blocking is True
        assert convergence_diag.severity == "error"
        assert len(convergence_diag.fix_hints) > 0

    def test_memory_error_is_blocking(self) -> None:
        path = OUTPUT_FIXTURES / "memory_error.log"
        diagnostics = parse_output_file(path)
        memory_diag = next(d for d in diagnostics if d.code == CODE_MEMORY_ERROR)
        assert memory_diag.blocking is True
        assert memory_diag.severity == "error"
        assert "required_mwords" in memory_diag.facts

    def test_log_operation_returns_diagnostics(self, capsys) -> None:
        rc = tool.main(["log", str(OUTPUT_FIXTURES / "convergence_failure.log")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["capabilities"]["operation"] == "log"
        assert len(payload["diagnostics"]) > 0
        assert payload["has_errors"] is True

    def test_log_operation_has_output_type(self, capsys) -> None:
        rc = tool.main(["log", str(OUTPUT_FIXTURES / "sample_output.log")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["output_type"] == "gamess-log"

    def test_log_operation_on_nonexistent_file(self, capsys) -> None:
        rc = tool.main(["log", str(FIXTURES / "nonexistent.log")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["capabilities"]["status"] == "unavailable"


class TestCaseDirectoryFixtures:
    """Tests for case directory fixtures."""

    def test_case_directory_with_intent(self, capsys) -> None:
        rc = tool.main(["check", str(CASE_DIR_FIXTURES / "input.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is True

    def test_case_directory_has_version_assumption(self, capsys) -> None:
        rc = tool.main(["check", str(CASE_DIR_FIXTURES / "input.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert "version_assumption" in payload
        assert payload["version_assumption"]["exact_runtime_known"] is True

    def test_invalid_case_directory_has_blocking_diagnostics(self, capsys) -> None:
        rc = tool.main(["check", str(CASE_INVALID_FIXTURES / "input.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is False
        blocking = [d for d in payload["diagnostics"] if d["blocking"]]
        assert len(blocking) > 0


class TestDiagnosticEnvelopeV1:
    """Tests for DiagnosticEnvelope/v1 contract stability."""

    @pytest.mark.parametrize(
        "fixture",
        [
            "valid_water_dft.inp",
            "valid_hf_sp.inp",
            "valid_mp2_energy.inp",
        ],
    )
    def test_valid_fixtures_have_clean_diagnostics(self, fixture: str, capsys) -> None:
        rc = tool.main(["check", str(FIXTURES / fixture)])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["diagnostic_envelope"] == "v1"
        assert payload["ok"] is True
        blocking = [d for d in payload["diagnostics"] if d["blocking"]]
        assert blocking == []

    @pytest.mark.parametrize(
        "fixture, expected_code",
        [
            ("invalid_unclosed_group.inp", "LINT_UNCLOSED_GROUP"),
            ("invalid_missing_data.inp", "GAMESS601"),
            ("invalid_bad_scftyp.inp", "LINT_INVALID_ENUM"),
        ],
    )
    def test_invalid_fixtures_have_blocking_diagnostics(
        self, fixture: str, expected_code: str, capsys
    ) -> None:
        rc = tool.main(["check", str(FIXTURES / fixture)])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["diagnostic_envelope"] == "v1"
        codes = {d["code"] for d in payload["diagnostics"]}
        assert expected_code in codes


class TestOpenQCSmokeEvidence:
    """Tests for OpenQC compatibility smoke evidence."""

    def test_capabilities_payload_has_required_fields(self) -> None:
        from gamess_lsp.tool import _capabilities_payload

        payload = _capabilities_payload()
        assert payload["schema"] == "OpenQCLspCapabilities"
        assert payload["software"] == "gamess"
        assert "log" in payload["agentCli"]["operations"]
        assert "output-log-diagnostics" in payload["capabilities"]

    def test_capabilities_file_has_required_fields(self) -> None:
        capabilities_path = Path(__file__).parent.parent / "lsp-capabilities.json"
        assert capabilities_path.exists()
        payload = json.loads(capabilities_path.read_text(encoding="utf-8"))
        assert payload["schema"] == "OpenQCLspCapabilities"
        assert payload["software"] == "gamess"
        assert "log" in payload["agentCli"]["operations"]
        assert "output-log-diagnostics" in payload["capabilities"]

    def test_manifest_operation_works(self, capsys) -> None:
        rc = tool.main(["manifest"])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert "capabilities" in payload
        assert "codes" in payload

    def test_check_operation_produces_valid_envelope(self, capsys) -> None:
        rc = tool.main(["check", str(FIXTURES / "valid_water_dft.inp")])
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)

        assert "diagnostic_envelope" in payload
        assert "diagnostic_engine" in payload
        assert "software" in payload
        assert "capabilities" in payload
        assert "diagnostics" in payload
        assert "ok" in payload

        assert payload["diagnostic_envelope"] == "v1"
        assert payload["diagnostic_engine"] == "1.0"
        assert payload["software"] == "gamess"
        assert payload["capabilities"]["operation"] == "check"
