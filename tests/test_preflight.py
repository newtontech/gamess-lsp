from __future__ import annotations

import json
from pathlib import Path

import pytest

from gamess_lsp import tool
from gamess_lsp.preflight import (
    ALL_ROLES,
    CODE_DFT_WITHOUT_FUNCTIONAL,
    CODE_ECP_WITHOUT_BASIS,
    CODE_GUESS_WITHOUT_VEC,
    CODE_LOW_MWORDS,
    CODE_METHOD_BASIS_MISMATCH,
    CODE_MISSING_BASIS,
    CODE_MISSING_GROUP,
    CODE_STATPT_DISABLED,
    CODE_STRUCTURE_EMPTY,
    CODE_VERSION_ASSUMPTION,
    DEFAULT_MWORDS_WARNING,
    ArtifactGraph,
    build_artifact_graph,
    fleet_manifest,
    resolve_version_assumption,
)
from gamess_lsp.tool import (
    _dedupe_preflight,
    _looks_like_workspace,
    manifest_path,
    preflight_path,
)
from gamess_lsp.parser import GAMESSParser

FIXTURES = Path(__file__).parent / "fixtures" / "preflight"

# Envelope fields the issue acceptance criteria require on failing fixtures.
REQUIRED_FAILING_FIELDS = {
    "code",
    "severity",
    "path",
    "range",
    "blocking",
    "category",
    "source_provenance",
}


def _envelope_codes(payload: dict) -> set[str]:
    return {item["code"] for item in payload["diagnostics"]}


def _parse(text: str):
    return GAMESSParser().parse(text)


# --- Envelope shape --------------------------------------------------------


def test_agent_check_payload_carries_diagnostic_envelope_v1(capsys) -> None:
    # No --fail-on-blocking, so the CLI exits 0 even with blocking findings;
    # the contract here is the envelope shape, not the exit code.
    rc = tool.main(["check", str(FIXTURES / "missing_data" / "input.inp")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["diagnostic_engine"] == "1.0"
    assert payload["software"] == "gamess"
    assert payload["capabilities"]["operation"] == "check"
    assert "version_assumption" in payload
    assert payload["version_assumption"]["software"] == "gamess"
    assert isinstance(payload.get("artifacts"), list)
    assert payload["artifacts"]
    # preflight GAMESS601 (missing $DATA) is merged into the check payload.
    assert CODE_MISSING_GROUP in _envelope_codes(payload)


def test_failing_diagnostics_carry_required_envelope_fields() -> None:
    payload = preflight_path(FIXTURES / "missing_data" / "input.inp")
    failing = [
        item
        for item in payload["diagnostics"]
        if item["code"] == CODE_MISSING_GROUP
    ]
    assert failing, "missing_data fixture must emit GAMESS601"
    item = failing[0]
    for field in REQUIRED_FAILING_FIELDS:
        assert field in item, f"missing required envelope field: {field}"
    assert item["confidence"] >= 0.0
    assert "actions" in item and item["actions"]
    assert "fix_hints" in item and item["fix_hints"]
    assert "facts" in item
    assert "artifact_roles" in item
    assert item["range"]["start"]["line"] >= 0
    assert "character" in item["range"]["start"]


# --- Fixture behavior ------------------------------------------------------


@pytest.mark.parametrize(
    "fixture, expected_ok, must_include",
    [
        ("valid_scf", True, set()),
        ("missing_data", False, {CODE_MISSING_GROUP}),
        ("missing_basis", False, {CODE_MISSING_BASIS}),
        ("guess_moread_no_vec", False, {CODE_GUESS_WITHOUT_VEC}),
        ("low_mwords", True, {CODE_LOW_MWORDS}),
        ("method_basis_mismatch", False, {CODE_METHOD_BASIS_MISMATCH}),
    ],
)
def test_preflight_fixture_expectations(
    fixture: str,
    expected_ok: bool,
    must_include: set[str],
) -> None:
    payload = preflight_path(FIXTURES / fixture / "input.inp")
    codes = _envelope_codes(payload)
    assert payload["ok"] is expected_ok, (
        f"{fixture}: expected ok={expected_ok}, got codes={sorted(codes)}"
    )
    assert must_include <= codes, (
        f"{fixture}: expected codes {must_include}, got {sorted(codes)}"
    )


def test_valid_scf_fixture_has_no_blocking_or_error_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "valid_scf" / "input.inp")
    assert payload["summary"]["errors"] == 0
    assert payload["summary"]["blocking"] == 0
    error_codes = {
        CODE_MISSING_GROUP,
        CODE_STRUCTURE_EMPTY,
        CODE_MISSING_BASIS,
        CODE_GUESS_WITHOUT_VEC,
        CODE_METHOD_BASIS_MISMATCH,
        CODE_DFT_WITHOUT_FUNCTIONAL,
    }
    assert not (_envelope_codes(payload) & error_codes)


def test_low_mwords_is_non_blocking_warning_with_threshold_fact() -> None:
    payload = preflight_path(FIXTURES / "low_mwords" / "input.inp")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_LOW_MWORDS)
    assert item["severity"] == "warning"
    assert item["blocking"] is False
    assert item["facts"]["mwords"] == 1.0
    assert item["facts"]["threshold"] == DEFAULT_MWORDS_WARNING


def test_low_mwords_intent_override_changes_threshold(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    # MWORDS=1 is below the default 2.0 threshold -> warning fires.
    (case / "input.inp").write_text(
        " $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        " $SYSTEM MWORDS=1 $END\n"
        " $BASIS GBASIS=STO NGAUSS=3 $END\n"
        " $DATA\nWater\nC1\nO 8.0 0 0 0\nH 1.0 0 0 0\nH 1.0 0 0 0\n $END\n",
        encoding="utf-8",
    )
    base = preflight_path(case / "input.inp")
    assert CODE_LOW_MWORDS in _envelope_codes(base)

    cfg = case / ".gamess-lsp"
    cfg.mkdir()
    # Override the threshold down to 1.0 so MWORDS=1 is no longer below it.
    (cfg / "intent.json").write_text(
        json.dumps({"mwords_warning": 1.0}), encoding="utf-8"
    )
    overridden = preflight_path(case / "input.inp")
    assert CODE_LOW_MWORDS not in _envelope_codes(overridden)


# --- version-aware-keywords ------------------------------------------------


def test_version_assumption_unknown_when_intent_absent() -> None:
    assumption = resolve_version_assumption(None)
    assert assumption["exact_runtime_known"] is False
    assert assumption["declared_by"] == "fallback"
    assert assumption["software_version"] == "unknown"


def test_version_assumption_known_when_intent_declares_version() -> None:
    assumption = resolve_version_assumption(
        {"software_version": "gamess >=2024", "runtime_image": "img:2024"}
    )
    assert assumption["exact_runtime_known"] is True
    assert assumption["declared_by"] == "intent"
    assert assumption["software_version"] == "gamess >=2024"


def test_version_assumption_information_diagnostic_when_unknown(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "input.inp").write_text(
        " $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        " $SYSTEM MWORDS=100 $END\n"
        " $BASIS GBASIS=STO NGAUSS=3 $END\n"
        " $DATA\nWater\nC1\nO 8.0 0 0 0\nH 1.0 0 0 0\nH 1.0 0 0 0\n $END\n",
        encoding="utf-8",
    )
    payload = preflight_path(case / "input.inp")
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_VERSION_ASSUMPTION),
        None,
    )
    assert item is not None
    assert item["severity"] == "information"
    assert item["blocking"] is False
    assert item["version_assumption"]["exact_runtime_known"] is False


def test_version_assumption_silent_when_intent_declares_version(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "input.inp").write_text(
        " $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        " $SYSTEM MWORDS=100 $END\n"
        " $BASIS GBASIS=STO NGAUSS=3 $END\n"
        " $DATA\nWater\nC1\nO 8.0 0 0 0\nH 1.0 0 0 0\nH 1.0 0 0 0\n $END\n",
        encoding="utf-8",
    )
    cfg = case / ".gamess-lsp"
    cfg.mkdir()
    (cfg / "intent.json").write_text(
        json.dumps({"software_version": "gamess >=2024"}), encoding="utf-8"
    )
    payload = preflight_path(case / "input.inp")
    assert CODE_VERSION_ASSUMPTION not in _envelope_codes(payload)
    assert payload["version_assumption"]["exact_runtime_known"] is True


def test_method_basis_mismatch_carries_version_assumption() -> None:
    payload = preflight_path(FIXTURES / "method_basis_mismatch" / "input.inp")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_METHOD_BASIS_MISMATCH)
    assert item["facts"]["gbasis"] == "STO"
    assert item["facts"]["method"] == "MP2"
    assert "version-aware" in item["domain_tags"]
    assert "version_assumption" in item


def test_dft_without_functional_is_blocking(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "input.inp").write_text(
        " $CONTRL SCFTYP=RHF DFTTYP= RUNTYP=ENERGY $END\n"
        " $SYSTEM MWORDS=100 $END\n"
        " $BASIS GBASIS=N31 NGAUSS=6 $END\n"
        " $DATA\nWater\nC1\nO 8.0 0 0 0\nH 1.0 0 0 0\nH 1.0 0 0 0\n $END\n",
        encoding="utf-8",
    )
    payload = preflight_path(case / "input.inp")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_DFT_WITHOUT_FUNCTIONAL)
    assert item["severity"] == "error"
    assert item["blocking"] is True


# --- cross-artifact-graph --------------------------------------------------


def test_artifact_graph_uses_generic_roles() -> None:
    input_path = (FIXTURES / "valid_scf" / "input.inp").resolve()
    parsed = _parse(input_path.read_text(encoding="utf-8"))
    graph = build_artifact_graph(input_path, parsed)
    roles = {node.role for node in graph.nodes}
    assert roles <= set(ALL_ROLES)
    # primary-input, control, basis, structure are always modeled.
    for required in ("primary-input", "control", "basis", "structure"):
        assert graph.by_role(required), f"missing required role: {required}"
    serialized = graph.to_json()
    assert isinstance(serialized, list)
    assert all(
        "role" in node and "group" in node and "exists" in node for node in serialized
    )


def test_missing_data_records_role_provenance() -> None:
    payload = preflight_path(FIXTURES / "missing_data" / "input.inp")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_GROUP)
    prov = item["source_provenance"]
    assert prov["role"] == "structure"
    assert prov["expected_group"] == "DATA"


def test_ecp_with_minimal_basis_is_non_blocking_warning(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "input.inp").write_text(
        " $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        " $SYSTEM MWORDS=100 $END\n"
        " $BASIS GBASIS=STO NGAUSS=3 $END\n"
        " $ECP\n $END\n"
        " $DATA\nWater\nC1\nO 8.0 0 0 0\nH 1.0 0 0 0\nH 1.0 0 0 0\n $END\n",
        encoding="utf-8",
    )
    payload = preflight_path(case / "input.inp")
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_ECP_WITHOUT_BASIS),
        None,
    )
    assert item is not None
    assert item["severity"] == "warning"
    assert item["blocking"] is False


def test_statpt_disabled_on_optimization_runtyp(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "input.inp").write_text(
        " $CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END\n"
        " $SYSTEM MWORDS=100 $END\n"
        " $BASIS GBASIS=STO NGAUSS=3 $END\n"
        " $STATPT NSTEP=0 $END\n"
        " $DATA\nWater\nC1\nO 8.0 0 0 0\nH 1.0 0 0 0\nH 1.0 0 0 0\n $END\n",
        encoding="utf-8",
    )
    payload = preflight_path(case / "input.inp")
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_STATPT_DISABLED),
        None,
    )
    assert item is not None
    assert item["severity"] == "warning"
    assert item["facts"]["runtyp"] == "OPTIMIZE"
    assert item["facts"]["nstep"] == 0


# --- code-actions / blocking gate -----------------------------------------


def test_check_fail_on_blocking_exits_nonzero_on_failing_fixture() -> None:
    rc = tool.main(
        ["check", str(FIXTURES / "missing_data" / "input.inp"), "--fail-on-blocking"]
    )
    assert rc == 1


def test_check_fail_on_blocking_exits_zero_on_valid_fixture(capsys) -> None:
    rc = tool.main(
        ["check", str(FIXTURES / "valid_scf" / "input.inp"), "--fail-on-blocking"]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_preflight_subcommand_emits_envelope(capsys) -> None:
    rc = tool.main(["preflight", str(FIXTURES / "low_mwords" / "input.inp")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation"] == "preflight"
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["capabilities"]["operation"] == "preflight"


def test_actions_present_on_blocking_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "missing_basis" / "input.inp")
    blocking = [d for d in payload["diagnostics"] if d["blocking"]]
    assert blocking
    for item in blocking:
        assert item.get("actions"), (
            f"blocking diagnostic {item['code']} must carry actions"
        )
        assert all("kind" in action for action in item["actions"])


# --- fleet-regression-fixtures / manifest ---------------------------------


def test_manifest_lists_all_four_capabilities() -> None:
    manifest = manifest_path(FIXTURES / "valid_scf" / "input.inp")
    capabilities = manifest["capabilities"]
    for cap in (
        "version-aware-keywords",
        "cross-artifact-graph",
        "code-actions",
        "fleet-regression-fixtures",
    ):
        assert cap in capabilities, f"missing capability: {cap}"
        assert capabilities[cap]["status"] == "available"
    assert set(manifest["artifact_roles"]) == set(ALL_ROLES)
    assert manifest["preflight_envelope"] == "DiagnosticEnvelope/v1"


def test_manifest_without_path_still_describes_surface() -> None:
    manifest = manifest_path(None)
    assert set(manifest["codes"])
    assert manifest["capabilities"]["code-actions"]["blocking_gate"]


def test_manifest_merges_fixture_expectations() -> None:
    manifest = manifest_path(FIXTURES / "valid_scf" / "input.inp")
    fixtures = manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]
    names = {item["name"] for item in fixtures}
    assert {
        "valid_scf",
        "missing_data",
        "missing_basis",
        "guess_moread_no_vec",
        "low_mwords",
        "method_basis_mismatch",
    } <= names


def test_fleet_manifest_helper_pure_data() -> None:
    manifest = fleet_manifest(fixtures=[{"name": "x", "expect_ok": True}])
    assert manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"] == [
        {"name": "x", "expect_ok": True}
    ]
    for body in manifest["codes"].values():
        assert body["severity"] in {"error", "warning", "information", "hint"}
        assert "capability" in body
        assert "summary" in body


def test_fixture_expectations_match_actual_preflight() -> None:
    """The fleet manifest's declared fixture expectations must match reality.

    This is the regression-evidence contract: the parent ``bohrium_skills``
    probe consumes the manifest and replays these fixtures, so the declared
    expectations have to agree with what the preflight actually emits.
    """
    manifest = manifest_path(FIXTURES / "valid_scf" / "input.inp")
    repo_root = Path(__file__).resolve().parent.parent
    for fixture in manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]:
        payload = preflight_path(repo_root / fixture["path"])
        assert payload["ok"] is fixture["expect_ok"], (
            f"{fixture['name']}: manifest expects ok={fixture['expect_ok']}, "
            f"got ok={payload['ok']}"
        )
        if fixture["expect_codes"]:
            assert set(fixture["expect_codes"]) <= _envelope_codes(payload), (
                f"{fixture['name']}: expected codes {fixture['expect_codes']}, "
                f"got {sorted(_envelope_codes(payload))}"
            )


# --- dedupe + workspace detection -----------------------------------------


def test_dedupe_preflight_passthrough_when_no_overlap() -> None:
    legacy: list = []
    preflight = [
        {"code": "GAMESS601", "severity": "error", "message": "missing"},
        {"code": "GAMESS606", "severity": "warning", "message": "low mwords"},
    ]
    result = _dedupe_preflight(legacy, preflight)
    codes = {item["code"] for item in result}
    assert codes == {"GAMESS601", "GAMESS606"}


def test_looks_like_workspace_requires_gamess_input(tmp_path: Path) -> None:
    # Empty directory is not a GAMESS workspace.
    assert _looks_like_workspace(tmp_path) is False
    # A directory containing a real $CONTRL ... $END input is a workspace.
    real = tmp_path / "input.inp"
    real.write_text(
        " $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n", encoding="utf-8"
    )
    assert _looks_like_workspace(tmp_path) is True
    assert _looks_like_workspace(real) is True


def test_check_on_workspace_input_merges_preflight(capsys) -> None:
    # Without --fail-on-blocking the CLI exits 0 even though preflight found a
    # blocking issue; the contract here is that the preflight code is merged.
    rc = tool.main(["check", str(FIXTURES / "missing_basis" / "input.inp")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    codes = _envelope_codes(payload)
    assert CODE_MISSING_BASIS in codes
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["ok"] is False


def test_artifact_graph_is_json_serializable_for_fleet_report() -> None:
    payload = preflight_path(FIXTURES / "valid_scf" / "input.inp")
    serialized = json.dumps(payload["artifacts"], sort_keys=True)
    assert "primary-input" in serialized
    assert "structure" in serialized


def test_artifact_graph_class_smoke() -> None:
    graph = ArtifactGraph(input_path=Path("/tmp"))
    assert graph.nodes == []
    assert graph.by_role("structure") == []
    assert graph.to_json() == []
