"""Universal generated-input preflight capabilities.

This module implements the four fleet-wide preflight capabilities called out in
``newtontech/gamess-lsp#82`` against a *generic artifact-role model*, so the
checks generalize to any backend in the scientific LSP fleet instead of being
wired to MatMaster submission policy:

* ``version-aware-keywords``  - explicit runtime/version assumption metadata and
  keyword/method compatibility validation derived from the GAMESS schema, never
  guessed.
* ``cross-artifact-graph``   - resolves a GAMESS input as a graph of artifacts
  with stable generic roles (primary-input, control, basis, structure,
  scf-control, guess, pseudopotential, optimization, dft). Cross-group checks
  operate on the graph rather than ad-hoc group names, so the same model works
  for VASP/CP2K/ABACUS/GROMACS/etc.
* ``code-actions``           - normalizes repair hints/actions on every
  diagnostic and exposes a blocking gate the agent CLI can run as
  ``check --fail-on-blocking`` plus a dedicated ``preflight`` subcommand.
* ``fleet-regression-fixtures`` - ``fleet_manifest`` returns a machine-readable
  description of the preflight surface (codes, capabilities, fixture
  expectations) so the parent ``bohrium_skills`` probe/report workflow can
  consume regression evidence without re-deriving it.

GAMESS packs its inputs into a single ``.inp`` file made of ``$GROUP ... $END``
blocks, so the cross-artifact graph models the *logical* artifacts (control
deck, basis set, structure, guess, etc.) rather than separate physical files.
The roles are the same generic fleet roles the parent router understands; only
the GAMESS-specific binding (group name -> role) lives here.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .parser import GAMESSInputFile, GAMESSParser

# --- Artifact-role model ---------------------------------------------------

# Generic roles. These are intentionally software-agnostic: every fleet backend
# can map its native inputs onto this same small role set, which is what lets
# the parent router consume cross-group/cross-file checks without learning
# MatMaster specifics.
ROLE_PRIMARY_INPUT = "primary-input"
ROLE_CONTROL = "control"
ROLE_BASIS = "basis"
ROLE_STRUCTURE = "structure"
ROLE_SCF_CONTROL = "scf-control"
ROLE_GUESS = "guess"
ROLE_PSEUDOPOTENTIAL = "pseudopotential"
ROLE_OPTIMIZATION = "optimization"
ROLE_DFT = "dft"

ALL_ROLES = (
    ROLE_PRIMARY_INPUT,
    ROLE_CONTROL,
    ROLE_BASIS,
    ROLE_STRUCTURE,
    ROLE_SCF_CONTROL,
    ROLE_GUESS,
    ROLE_PSEUDOPOTENTIAL,
    ROLE_OPTIMIZATION,
    ROLE_DFT,
)

# Binding from GAMESS $GROUP to the generic fleet role. Multiple groups can
# share a role (e.g. $GUESS/$VEC both realize the guess role). $DATA is the
# structure artifact just like a VASP POSCAR or ABACUS STRU.
GROUP_ROLE_BINDING: dict[str, str] = {
    "CONTRL": ROLE_CONTROL,
    "SYSTEM": ROLE_PRIMARY_INPUT,
    "BASIS": ROLE_BASIS,
    "LIBRARY": ROLE_BASIS,
    "DATA": ROLE_STRUCTURE,
    "SCF": ROLE_SCF_CONTROL,
    "GUESS": ROLE_GUESS,
    "VEC": ROLE_GUESS,
    "ECP": ROLE_PSEUDOPOTENTIAL,
    "STATPT": ROLE_OPTIMIZATION,
    "DFT": ROLE_DFT,
}

# Conservative workflow thresholds used by the warning-level checks. The actual
# cutoffs are overridable via the preflight intent contract; these are only the
# default fleet baselines, not MatMaster policy.
DEFAULT_MWORDS_WARNING = 2.0  # < 2 MWords is often too small for production.
DEFAULT_NSTEP_WARNING_CEIL = 0  # 0 or negative NSTEP disables optimization.

# Codes reserved for the universal preflight surface. They use the ``GAMESS6xx``
# band so they sort after existing rule codes and stay identifiable as
# cross-fleet preflight findings.
CODE_MISSING_GROUP = "GAMESS601"
CODE_STRUCTURE_EMPTY = "GAMESS602"
CODE_MISSING_BASIS = "GAMESS603"
CODE_GUESS_WITHOUT_VEC = "GAMESS604"
CODE_ECP_WITHOUT_BASIS = "GAMESS605"
CODE_LOW_MWORDS = "GAMESS606"
CODE_STATPT_DISABLED = "GAMESS607"
CODE_VERSION_ASSUMPTION = "GAMESS608"
CODE_METHOD_BASIS_MISMATCH = "GAMESS609"
CODE_DFT_WITHOUT_FUNCTIONAL = "GAMESS610"

# RUNTYP values that drive an optimization and therefore make $STATPT relevant.
_RUNTYP_OPTIMIZATION_LIKE = {"OPTIMIZE", "SADPOINT", "TRUDGE", "IRC", "DRC"}


@dataclass(frozen=True)
class ArtifactNode:
    """A node in the cross-artifact graph.

    ``role`` is one of the fleet-generic roles above; ``group`` is the GAMESS
    ``$GROUP`` name that realizes this role (or ``None`` when the role is the
    primary input file itself); ``exists`` records whether the group is present
    in the parsed input; ``source`` records where the binding originated so
    consumers can trace provenance.
    """

    role: str
    group: str | None
    exists: bool
    source: str
    line: int
    detail: dict[str, Any] | None = None


@dataclass
class ArtifactGraph:
    """Generic cross-artifact graph built from a parsed GAMESS input."""

    input_path: Path
    nodes: list[ArtifactNode] = field(default_factory=list)

    def by_role(self, role: str) -> list[ArtifactNode]:
        return [node for node in self.nodes if node.role == role]

    def to_json(self) -> list[dict[str, Any]]:
        """Serialize the graph for the parent probe/report workflow."""

        def _node_json(node: ArtifactNode) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "role": node.role,
                "group": node.group,
                "exists": node.exists,
                "source": node.source,
                "line": node.line,
            }
            if node.detail:
                payload["detail"] = node.detail
            return payload

        return sorted(
            (_node_json(node) for node in self.nodes),
            key=lambda item: (item["role"], item["group"] or "", item["line"]),
        )


def build_artifact_graph(
    input_path: Path,
    parsed: GAMESSInputFile,
) -> ArtifactGraph:
    """Build the cross-artifact graph from a parsed GAMESS input.

    The model is generic: it records roles + the GAMESS group that realizes each
    role + provenance. The same shape generalizes to other fleet backends
    because it never bakes in MatMaster/Bohrium runtime concepts (no image, no
    session, no submission policy).
    """
    graph = ArtifactGraph(input_path=input_path.resolve())
    graph.nodes.append(
        ArtifactNode(
            role=ROLE_PRIMARY_INPUT,
            group=None,
            exists=True,
            source="case-root",
            line=1,
        )
    )
    for group_name, role in GROUP_ROLE_BINDING.items():
        group = parsed.get_group(group_name)
        graph.nodes.append(
            ArtifactNode(
                role=role,
                group=group_name,
                exists=group is not None,
                source=f"$GROUP binding:{group_name}",
                line=group.line_start if group else 1,
            )
        )
    return graph


# --- Preflight diagnostics -------------------------------------------------


def preflight_diagnostics(
    input_path: Path,
    *,
    intent: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], ArtifactGraph]:
    """Run universal generated-input preflight checks.

    Returns a tuple of (diagnostics, artifact_graph). Diagnostics are envelope
    dicts carrying the full ``DiagnosticEnvelope/v1`` field set so the agent
    CLI can emit them directly without re-shaping.
    """
    input_path = input_path.resolve()
    text = input_path.read_text(encoding="utf-8", errors="ignore")
    parser = GAMESSParser()
    parsed = parser.parse(text)
    graph = build_artifact_graph(input_path, parsed)

    version_assumption = resolve_version_assumption(intent)
    diagnostics: list[dict[str, Any]] = []
    diagnostics.extend(_missing_group_diagnostics(graph, parsed))
    diagnostics.extend(_structure_diagnostics(parsed, input_path))
    diagnostics.extend(_basis_diagnostics(parsed, input_path))
    diagnostics.extend(_guess_vec_diagnostics(parsed, input_path))
    diagnostics.extend(_ecp_basis_diagnostics(parsed, input_path))
    diagnostics.extend(_low_mwords_diagnostics(parsed, input_path, intent))
    diagnostics.extend(_statpt_disabled_diagnostics(parsed, input_path))
    diagnostics.extend(_method_basis_mismatch_diagnostics(parsed, input_path, version_assumption))
    diagnostics.extend(_dft_without_functional_diagnostics(parsed, input_path, version_assumption))
    diagnostics.extend(_version_assumption_diagnostic(version_assumption, intent, input_path))

    return (
        sorted(
            diagnostics,
            key=lambda item: (
                item.get("range", {}).get("start", {}).get("line", 0),
                item.get("range", {}).get("start", {}).get("character", 0),
                item["code"],
            ),
        ),
        graph,
    )


def _diag(
    *,
    code: str,
    severity: str,
    message: str,
    path: Path,
    line: int = 1,
    column: int = 1,
    category: str,
    confidence: float,
    blocking: bool,
    source_provenance: dict[str, Any],
    fix_hints: list[str],
    actions: list[dict[str, Any]] | None = None,
    facts: dict[str, Any] | None = None,
    artifact_roles: list[str] | None = None,
    domain_tags: list[str] | None = None,
    version_assumption: dict[str, Any] | None = None,
    manual_ref: str | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single normalized preflight diagnostic.

    Carries every field the issue acceptance criteria require (``code``,
    ``severity``, ``path``/``range``, ``blocking``, ``category``,
    ``source_provenance``, ``fix_hints``/``actions``) plus the richer envelope
    fields (``facts``, ``artifact_roles``, ``domain_tags``,
    ``version_assumption``) used by the parent fleet probe.
    """
    line0 = max(line - 1, 0)
    col0 = max(column - 1, 0)
    payload: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "file": str(path),
        "path": str(path),
        "line": line,
        "column": column,
        "category": category,
        "confidence": confidence,
        "source": "gamess-preflight",
        "range": {
            "start": {"line": line0, "character": col0},
            "end": {"line": line0, "character": col0 + 1},
        },
        "blocking": blocking,
        "fix_hints": fix_hints,
        "source_provenance": source_provenance,
    }
    if actions:
        payload["actions"] = actions
    if facts:
        payload["facts"] = facts
    if artifact_roles:
        payload["artifact_roles"] = artifact_roles
    if domain_tags:
        payload["domain_tags"] = domain_tags
    if version_assumption:
        payload["version_assumption"] = version_assumption
    if manual_ref:
        payload["manual_ref"] = manual_ref
    if intent:
        payload["intent"] = intent
    return payload


def _group_line(parsed: GAMESSInputFile, group_name: str) -> int:
    group = parsed.get_group(group_name)
    return group.line_start if group else 1


def _missing_group_diagnostics(
    graph: ArtifactGraph, parsed: GAMESSInputFile
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    # $CONTRL is the mandatory control deck; without it GAMESS cannot decide
    # what to compute. $DATA is required for any molecular calculation.
    for role, group_name in ((ROLE_CONTROL, "CONTRL"), (ROLE_STRUCTURE, "DATA")):
        node_iter = graph.by_role(role)
        node = next(iter(node_iter), None)
        if node is not None and not node.exists:
            out.append(
                _diag(
                    code=CODE_MISSING_GROUP,
                    severity="error",
                    message=(
                        f"${group_name} group is missing; GAMESS requires it for "
                        f"the {role} artifact"
                    ),
                    path=graph.input_path,
                    line=1,
                    category="cross-file reference",
                    confidence=0.97,
                    blocking=True,
                    source_provenance={
                        "role": role,
                        "expected_group": group_name,
                        "present_groups": sorted(parsed.groups.keys()),
                    },
                    fix_hints=[
                        f"Add a ${group_name} ... $END block to the input",
                        "Or restore the group from the original template",
                    ],
                    actions=[
                        {
                            "kind": "insert_group",
                            "group": group_name,
                            "target": str(graph.input_path),
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={
                        "missing_group": group_name,
                        "present_groups": sorted(parsed.groups.keys()),
                    },
                    artifact_roles=[role, ROLE_PRIMARY_INPUT],
                    domain_tags=["cross-group", "blocking"],
                )
            )
    return out


def _structure_diagnostics(parsed: GAMESSInputFile, path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    data = parsed.get_group("DATA")
    if data is None:
        return out  # missing-group diagnostic already covers this.
    # GAMESS $DATA must contain geometry atoms after the title + symmetry lines.
    if not parsed.geometry:
        out.append(
            _diag(
                code=CODE_STRUCTURE_EMPTY,
                severity="error",
                message="$DATA group has no atom lines; geometry is empty",
                path=path,
                line=data.line_start,
                category="cross-file reference",
                confidence=0.9,
                blocking=True,
                source_provenance={
                    "role": ROLE_STRUCTURE,
                    "group": "DATA",
                    "atom_count": 0,
                },
                fix_hints=[
                    "Add atom records (Symbol Z x y z) after the symmetry line",
                    "Or import the geometry from an external coordinate source",
                ],
                actions=[
                    {
                        "kind": "insert_section",
                        "section": "atoms",
                        "target": str(path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"atom_count": 0},
                artifact_roles=[ROLE_STRUCTURE],
                domain_tags=["cross-group", "blocking"],
            )
        )
    return out


def _basis_diagnostics(parsed: GAMESSInputFile, path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    contrl = parsed.get_group("CONTRL")
    basis = parsed.get_group("BASIS")
    library = parsed.get_group("LIBRARY")
    # When $CONTRL does not request an externally supplied basis (GBASIS=USER
    # with a $DATA inline basis is a legitimate GAMESS path), the standard
    # $BASIS group is mandatory.
    user_basis = False
    if contrl is not None:
        gbasis_kw = contrl.get_keyword("GBASIS")
        if gbasis_kw is not None and gbasis_kw.value.upper() == "USER":
            user_basis = True
    if basis is None and library is None and not user_basis:
        out.append(
            _diag(
                code=CODE_MISSING_BASIS,
                severity="error",
                message="$BASIS group is missing and no $LIBRARY or inline USER basis was declared",
                path=path,
                line=_group_line(parsed, "CONTRL"),
                category="cross-file reference",
                confidence=0.95,
                blocking=True,
                source_provenance={
                    "role": ROLE_BASIS,
                    "control_runtyp": _keyword_value(parsed, "CONTRL", "RUNTYP"),
                    "library_present": library is not None,
                    "user_basis": user_basis,
                },
                fix_hints=[
                    "Add a $BASIS GBASIS=... group",
                    "Or reference a $LIBRARY basis set file",
                    "Or set GBASIS=USER in $CONTRL with an inline basis",
                ],
                actions=[
                    {
                        "kind": "insert_group",
                        "group": "BASIS",
                        "target": str(path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={
                    "basis_present": basis is not None,
                    "library_present": library is not None,
                    "user_basis": user_basis,
                },
                artifact_roles=[ROLE_BASIS, ROLE_CONTROL],
                domain_tags=["cross-group", "blocking"],
            )
        )
    return out


def _guess_vec_diagnostics(parsed: GAMESSInputFile, path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    guess = parsed.get_group("GUESS")
    vec = parsed.get_group("VEC")
    if guess is None:
        return out
    # $GUESS GUESS=MOREAD reads molecular orbitals from $VEC; without it the
    # restart will fail at SCF startup.
    guess_kw = guess.get_keyword("GUESS")
    if guess_kw is not None and guess_kw.value.upper() == "MOREAD" and vec is None:
        out.append(
            _diag(
                code=CODE_GUESS_WITHOUT_VEC,
                severity="error",
                message="$GUESS GUESS=MOREAD requires a matching $VEC group with restart orbitals",
                path=path,
                line=guess.line_start,
                category="cross-file reference",
                confidence=0.92,
                blocking=True,
                source_provenance={
                    "role": ROLE_GUESS,
                    "control_keyword": "GUESS=MOREAD",
                    "vec_present": False,
                },
                fix_hints=[
                    "Provide a $VEC group containing the restart MO coefficients",
                    "Or change $GUESS to a self-consistent guess (HUCKEL/CORE)",
                ],
                actions=[
                    {
                        "kind": "insert_group",
                        "group": "VEC",
                        "target": str(path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"guess_value": "MOREAD", "vec_present": False},
                artifact_roles=[ROLE_GUESS],
                domain_tags=["cross-group", "blocking"],
            )
        )
    return out


def _ecp_basis_diagnostics(parsed: GAMESSInputFile, path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    ecp = parsed.get_group("ECP")
    basis = parsed.get_group("BASIS")
    if ecp is None:
        return out
    if basis is None:
        return out  # missing-basis diagnostic already covers the absence.
    # An ECP must be paired with an all-electron-like basis choice; declaring
    # $ECP while keeping the default tiny basis is a common silent mistake.
    gbasis_kw = basis.get_keyword("GBASIS")
    gbasis = gbasis_kw.value.upper() if gbasis_kw is not None else ""
    if gbasis in {"STO", "MNDO", "AM1", "PM3"}:
        out.append(
            _diag(
                code=CODE_ECP_WITHOUT_BASIS,
                severity="warning",
                message=(
                    f"$ECP declared but $BASIS GBASIS={gbasis} is a minimal/semiempirical "
                    "set; pair the ECP with a correlation-consistent basis"
                ),
                path=path,
                line=basis.line_start,
                category="semantic consistency",
                confidence=0.8,
                blocking=False,
                source_provenance={
                    "role": ROLE_PSEUDOPOTENTIAL,
                    "cross_referenced_role": ROLE_BASIS,
                    "gbasis": gbasis,
                },
                fix_hints=[
                    "Switch GBASIS to a correlation-consistent family (CC-PVDZ etc.)",
                    "Or remove $ECP if a minimal basis is intentional",
                ],
                actions=[
                    {
                        "kind": "set_keyword",
                        "keyword": "GBASIS",
                        "value": "CC-PVDZ",
                        "target": str(path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"gbasis": gbasis, "ecp_present": True},
                artifact_roles=[ROLE_PSEUDOPOTENTIAL, ROLE_BASIS],
                domain_tags=["semantic", "non-blocking"],
            )
        )
    return out


def _low_mwords_diagnostics(
    parsed: GAMESSInputFile, path: Path, intent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    system = parsed.get_group("SYSTEM")
    if system is None:
        return out
    mwords_kw = system.get_keyword("MWORDS")
    if mwords_kw is None:
        return out
    try:
        mwords = float(str(mwords_kw.value).split()[0])
    except (ValueError, IndexError):
        return out
    threshold = float((intent or {}).get("mwords_warning", DEFAULT_MWORDS_WARNING))
    if mwords < threshold:
        out.append(
            _diag(
                code=CODE_LOW_MWORDS,
                severity="warning",
                message=(
                    f"MWORDS={mwords} is below the conservative workflow threshold "
                    f"({threshold}); SCF/MP2/CC runs may exhaust memory"
                ),
                path=path,
                line=system.line_start,
                category="preflight/runtime-risk",
                confidence=0.75,
                blocking=False,
                source_provenance={
                    "role": ROLE_PRIMARY_INPUT,
                    "keyword": "MWORDS",
                    "threshold_source": (
                        "intent" if "mwords_warning" in (intent or {}) else "default"
                    ),
                },
                fix_hints=[
                    f"Raise MWORDS to at least {threshold:g}",
                    "Or document the smaller allocation in the intent contract",
                ],
                actions=[
                    {
                        "kind": "set_keyword",
                        "keyword": "MWORDS",
                        "value": f"{threshold:g}",
                        "target": str(path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"mwords": mwords, "threshold": threshold},
                artifact_roles=[ROLE_PRIMARY_INPUT],
                domain_tags=["preflight", "runtime-risk"],
            )
        )
    return out


def _statpt_disabled_diagnostics(
    parsed: GAMESSInputFile, path: Path
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    runtyp = _keyword_value(parsed, "CONTRL", "RUNTYP")
    if runtyp is None or runtyp.upper() not in _RUNTYP_OPTIMIZATION_LIKE:
        return out
    statpt = parsed.get_group("STATPT")
    if statpt is None:
        return out
    nstep_kw = statpt.get_keyword("NSTEP")
    if nstep_kw is None:
        return out
    try:
        nstep = int(str(nstep_kw.value).split()[0])
    except (ValueError, IndexError):
        return out
    if nstep <= DEFAULT_NSTEP_WARNING_CEIL:
        out.append(
            _diag(
                code=CODE_STATPT_DISABLED,
                severity="warning",
                message=(
                    f"RUNTYP={runtyp} but $STATPT NSTEP={nstep} disables optimization steps"
                ),
                path=path,
                line=statpt.line_start,
                category="semantic consistency",
                confidence=0.85,
                blocking=False,
                source_provenance={
                    "role": ROLE_OPTIMIZATION,
                    "control_runtyp": runtyp,
                    "nstep": nstep,
                },
                fix_hints=[
                    "Raise NSTEP to a positive number of allowed steps",
                    "Or change RUNTYP to a single-point calculation",
                ],
                actions=[
                    {
                        "kind": "set_keyword",
                        "keyword": "NSTEP",
                        "value": "50",
                        "target": str(path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"runtyp": runtyp, "nstep": nstep},
                artifact_roles=[ROLE_OPTIMIZATION, ROLE_CONTROL],
                domain_tags=["semantic", "non-blocking"],
            )
        )
    return out


def _method_basis_mismatch_diagnostics(
    parsed: GAMESSInputFile, path: Path, version_assumption: dict[str, Any]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    contrl = parsed.get_group("CONTRL")
    if contrl is None:
        return out
    mplev_kw = contrl.get_keyword("MPLEVL")
    cctyp_kw = contrl.get_keyword("CCTYP")
    basis = parsed.get_group("BASIS")
    if basis is None:
        return out
    gbasis_kw = basis.get_keyword("GBASIS")
    gbasis = gbasis_kw.value.upper() if gbasis_kw is not None else ""
    # Correlated methods (MP2/CC) on a minimal basis produce noise; surface this
    # as a version/method compatibility finding the parent probe can act on.
    correlated = False
    method = ""
    if mplev_kw is not None and str(mplev_kw.value).strip() in {"2", "3", "4"}:
        correlated = True
        method = f"MP{mplev_kw.value}"
    if cctyp_kw is not None and cctyp_kw.value.upper() in {"CCSD", "CCSD(T)", "RCCSD", "UCCSD"}:
        correlated = True
        method = cctyp_kw.value.upper()
    if correlated and gbasis in {"STO", "SBKJC", "HAY", "HW"}:
        out.append(
            _diag(
                code=CODE_METHOD_BASIS_MISMATCH,
                severity="error",
                message=(
                    f"Correlated method {method} is not meaningful with the minimal "
                    f"basis GBASIS={gbasis}"
                ),
                path=path,
                line=basis.line_start,
                category="schema",
                confidence=0.9,
                blocking=True,
                source_provenance={
                    "role": ROLE_BASIS,
                    "method": method,
                    "gbasis": gbasis,
                    "schema_source": "gamess-lsp builtin method/basis matrix",
                },
                fix_hints=[
                    f"Switch GBASIS to a polarized basis for {method}",
                    "Or downgrade to a single-point SCF calculation",
                ],
                actions=[
                    {
                        "kind": "set_keyword",
                        "keyword": "GBASIS",
                        "value": "N31",
                        "target": str(path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"method": method, "gbasis": gbasis},
                artifact_roles=[ROLE_BASIS, ROLE_CONTROL],
                domain_tags=["schema", "version-aware", "blocking"],
                version_assumption=version_assumption,
            )
        )
    return out


def _dft_without_functional_diagnostics(
    parsed: GAMESSInputFile, path: Path, version_assumption: dict[str, Any]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    contrl = parsed.get_group("CONTRL")
    if contrl is None:
        return out
    dfttyp_kw = contrl.get_keyword("DFTTYP")
    if dfttyp_kw is None:
        return out
    if dfttyp_kw.value.strip() == "":
        out.append(
            _diag(
                code=CODE_DFT_WITHOUT_FUNCTIONAL,
                severity="error",
                message="$CONTRL declares DFTTYP but no functional value was supplied",
                path=path,
                line=contrl.line_start,
                category="schema",
                confidence=0.9,
                blocking=True,
                source_provenance={
                    "role": ROLE_DFT,
                    "keyword": "DFTTYP",
                    "schema_source": "gamess-lsp builtin keyword schema",
                },
                fix_hints=[
                    "Set DFTTYP to a functional such as B3LYP or PBE",
                    "Or remove DFTTYP for a pure Hartree-Fock run",
                ],
                actions=[
                    {
                        "kind": "set_keyword",
                        "keyword": "DFTTYP",
                        "value": "B3LYP",
                        "target": str(path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"dfttyp": ""},
                artifact_roles=[ROLE_DFT, ROLE_CONTROL],
                domain_tags=["schema", "version-aware", "blocking"],
                version_assumption=version_assumption,
            )
        )
    return out


# --- version-aware-keywords ------------------------------------------------


def resolve_version_assumption(intent: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve the explicit runtime/version assumption for this preflight run.

    When the exact runtime/image version is unknown we record that fact
    explicitly rather than guessing, per the issue's version-assumptions
    acceptance criterion. The intent contract can override ``software_version``
    (e.g. ``gamess >=2023``); otherwise we fall back to the schema version the
    builtin keyword set was authored against.
    """
    intent = intent or {}
    software_version = intent.get("software_version")
    runtime_image = intent.get("runtime_image")
    assumption: dict[str, Any] = {
        "software": "gamess",
        "software_version": software_version or "unknown",
        "runtime_image": runtime_image or "unknown",
        "schema_source": intent.get("schema_source", "gamess-lsp builtin"),
        # The fallback is intentional and explicit so consumers never have to
        # guess whether ``unknown`` means "not checked" or "could not determine".
        "exact_runtime_known": bool(software_version or runtime_image),
    }
    if software_version or runtime_image:
        assumption["declared_by"] = "intent"
    else:
        assumption["declared_by"] = "fallback"
    return assumption


def _version_assumption_diagnostic(
    version_assumption: dict[str, Any],
    intent: dict[str, Any] | None,
    path: Path,
) -> list[dict[str, Any]]:
    """Emit an explicit information diagnostic when the runtime version is unknown.

    This makes the version assumption machine-readable in the diagnostic stream
    itself (not just metadata) so the parent probe can surface it without
    parsing the envelope top-level.
    """
    if version_assumption["exact_runtime_known"]:
        return []
    return [
        _diag(
            code=CODE_VERSION_ASSUMPTION,
            severity="information",
            message=(
                "Exact GAMESS runtime/image version is unknown; preflight "
                "validated against the builtin keyword set"
            ),
            path=path,
            line=1,
            category="preflight/runtime-risk",
            confidence=1.0,
            blocking=False,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "reason": "software_version and runtime_image not declared in intent",
            },
            fix_hints=[
                "Declare software_version/runtime_image in the intent contract",
            ],
            actions=[],
            facts={
                "software_version": version_assumption["software_version"],
                "runtime_image": version_assumption["runtime_image"],
                "schema_source": version_assumption["schema_source"],
            },
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["version-aware", "assumption"],
            version_assumption=version_assumption,
            intent=dict(intent) if intent else None,
        )
    ]


# --- fleet-regression-fixtures --------------------------------------------


def fleet_manifest(
    *,
    fixtures: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a machine-readable preflight manifest for the parent fleet.

    The parent ``bohrium_skills`` probe/report workflow consumes this to know
    which preflight codes exist, which capabilities are implemented, and which
    fixtures exercise them. Keeping it as data (not README prose) means the
    fleet regression evidence stays in sync with the implementation.
    """
    codes = {
        CODE_MISSING_GROUP: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "mandatory $CONTRL/$DATA group absent from input",
        },
        CODE_STRUCTURE_EMPTY: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "$DATA group has no atom geometry lines",
        },
        CODE_MISSING_BASIS: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "no $BASIS/$LIBRARY/inline USER basis declared",
        },
        CODE_GUESS_WITHOUT_VEC: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "$GUESS GUESS=MOREAD without matching $VEC",
        },
        CODE_ECP_WITHOUT_BASIS: {
            "severity": "warning",
            "category": "semantic consistency",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "$ECP paired with a minimal/semiempirical basis",
        },
        CODE_LOW_MWORDS: {
            "severity": "warning",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "MWORDS allocation below conservative threshold",
        },
        CODE_STATPT_DISABLED: {
            "severity": "warning",
            "category": "semantic consistency",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "optimization RUNTYP but $STATPT NSTEP<=0",
        },
        CODE_METHOD_BASIS_MISMATCH: {
            "severity": "error",
            "category": "schema",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "correlated method on a minimal basis",
        },
        CODE_DFT_WITHOUT_FUNCTIONAL: {
            "severity": "error",
            "category": "schema",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "DFTTYP declared without a functional value",
        },
        CODE_VERSION_ASSUMPTION: {
            "severity": "information",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "exact runtime version unknown; fallback schema used",
        },
    }
    capabilities = {
        "version-aware-keywords": {
            "status": "available",
            "evidence_codes": [
                CODE_METHOD_BASIS_MISMATCH,
                CODE_DFT_WITHOUT_FUNCTIONAL,
                CODE_VERSION_ASSUMPTION,
                CODE_LOW_MWORDS,
            ],
        },
        "cross-artifact-graph": {
            "status": "available",
            "roles": list(ALL_ROLES),
            "evidence_codes": [
                CODE_MISSING_GROUP,
                CODE_STRUCTURE_EMPTY,
                CODE_MISSING_BASIS,
                CODE_GUESS_WITHOUT_VEC,
                CODE_ECP_WITHOUT_BASIS,
                CODE_STATPT_DISABLED,
            ],
        },
        "code-actions": {
            "status": "available",
            "blocking_gate": "gamess-lsp-tool check --fail-on-blocking",
            "evidence_codes": list(codes.keys()),
        },
        "fleet-regression-fixtures": {
            "status": "available",
            "fixtures": list(fixtures) if fixtures else [],
        },
    }
    return {
        "software": "gamess",
        "preflight_envelope": "DiagnosticEnvelope/v1",
        "artifact_roles": list(ALL_ROLES),
        "capabilities": capabilities,
        "codes": codes,
    }


# --- helpers ---------------------------------------------------------------


def _keyword_value(parsed: GAMESSInputFile, group_name: str, keyword: str) -> str | None:
    group = parsed.get_group(group_name)
    if group is None:
        return None
    kw = group.get_keyword(keyword)
    return kw.value if kw is not None else None


# Used by the tool layer to detect a $END terminator without parsing the whole
# file, so a single-line probe stays cheap.
_END_GROUP_RE = re.compile(r"\$END\b", re.IGNORECASE)


def looks_like_gamess_workspace(path: Path) -> bool:
    """True when a path is a real GAMESS generated-input artifact.

    Preflight accepts either a ``.inp`` file or a directory containing one; a
    directory with no GAMESS input falls back to the legacy single-file lint
    path so callers that progressively build inputs are not flooded with
    blocking missing-group errors before the input exists.
    """
    if path.is_file():
        return path.suffix.lower() == ".inp" or _has_gamess_group(path)
    if not path.is_dir():
        return False
    return any(_has_gamess_entry(child) for child in path.iterdir())


def _has_gamess_entry(child: Path) -> bool:
    if child.is_file() and (child.suffix.lower() == ".inp" or _has_gamess_group(child)):
        return True
    return False


def _has_gamess_group(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return bool(re.search(r"^\s*\$[A-Za-z]", text, re.MULTILINE)) and bool(
        _END_GROUP_RE.search(text)
    )
