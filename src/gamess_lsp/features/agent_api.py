"""Machine-readable code-intelligence API for AI coding agents.

Exposes domain language descriptions (#58), section/keyword schema lookup (#59),
minimal examples and next-token guidance (#60), and the OpenQC smoke capability (#76).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from lsprotocol.types import Diagnostic

from ..keywords import GAMESS_GROUPS, GAMESS_KEYWORDS
from ..parser import GAMESSParser


@dataclass
class AgentAPISnapshot:
    uri: str = ""
    version: Optional[int] = None
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    outline: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "uri": self.uri,
                "version": self.version,
                "diagnostics": self.diagnostics,
                "outline": self.outline,
                "metadata": self.metadata,
            },
            indent=2,
        )


def _diag_to_dict(d: Diagnostic) -> Dict[str, Any]:
    return {
        "line": d.range.start.line,
        "character": d.range.start.character,
        "severity": d.severity,
        "message": d.message,
        "code": d.code,
        "source": d.source,
    }


# ------------------------------------------------------------------
# Issue #58: Domain language descriptions
# ------------------------------------------------------------------

_DOMAIN_LANGUAGE = {
    "language": "GAMESS US input",
    "description": (
        "GAMESS US input files use Fortran-style grouped input. "
        "Each section begins with $GROUPNAME and ends with $END. "
        "Keyword=value pairs are specified within each group. "
        "The $DATA group contains the title, symmetry, and molecular geometry."
    ),
    "conventions": [
        "Group names are case-insensitive but conventionally uppercase",
        "Keywords are case-insensitive",
        "Boolean values use dot-prefix: .TRUE. .FALSE.",
        "Groups are terminated with $END",
        "Comments start with !",
        "The $DATA group has a fixed structure: title line, symmetry line, then atoms",
    ],
    "file_extensions": [".inp", ".gamess", ".gms"],
    "common_groups": sorted(GAMESS_GROUPS.keys()),
}


# ------------------------------------------------------------------
# Issue #59: Section and keyword schema
# ------------------------------------------------------------------

def _build_section_schema() -> Dict[str, Any]:
    """Build the full section/keyword schema from the keywords database."""
    sections: Dict[str, Any] = {}
    for group_name, description in GAMESS_GROUPS.items():
        kw_db = GAMESS_KEYWORDS.get(group_name, {})
        keywords: Dict[str, Any] = {}
        for kw_name, kw_info in kw_db.items():
            keywords[kw_name] = {
                "doc": kw_info.get("doc", "").strip(),
                "values": kw_info.get("values", []),
            }
        sections[group_name] = {
            "description": description.strip(),
            "keywords": keywords,
        }
    return sections


_SECTION_SCHEMA: Optional[Dict[str, Any]] = None


def get_section_schema() -> Dict[str, Any]:
    """Return the section/keyword schema, lazily built."""
    global _SECTION_SCHEMA
    if _SECTION_SCHEMA is None:
        _SECTION_SCHEMA = _build_section_schema()
    return _SECTION_SCHEMA


# ------------------------------------------------------------------
# Issue #60: Minimal examples and next-token guidance
# ------------------------------------------------------------------

_MINIMAL_EXAMPLES: Dict[str, str] = {
    "energy": (
        " $CONTRL SCFTYP=RHF RUNTYP=ENERGY COORD=UNIQUE $END\n"
        " $BASIS GBASIS=N31 NGAUSS=6 $END\n"
        " $SYSTEM MWORDS=100 $END\n"
        " $DATA\n"
        "Title\n"
        "C1\n"
        "C     6.0     0.0     0.0     0.0\n"
        " $END"
    ),
    "optimize": (
        " $CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE COORD=UNIQUE $END\n"
        " $BASIS GBASIS=N31 NGAUSS=6 $END\n"
        " $SYSTEM MWORDS=100 $END\n"
        " $STATPT OPTTOL=0.0001 NSTEP=50 $END\n"
        " $DATA\n"
        "Title\n"
        "C1\n"
        "C     6.0     0.0     0.0     0.0\n"
        " $END"
    ),
    "dft": (
        " $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=ENERGY $END\n"
        " $BASIS GBASIS=CC-PVDZ $END\n"
        " $SYSTEM MWORDS=200 $END\n"
        " $DATA\n"
        "Title\n"
        "C1\n"
        "C     6.0     0.0     0.0     0.0\n"
        " $END"
    ),
    "mp2": (
        " $CONTRL SCFTYP=RHF RUNTYP=ENERGY MPLEVL=2 $END\n"
        " $BASIS GBASIS=CC-PVTZ $END\n"
        " $SYSTEM MWORDS=200 $END\n"
        " $DATA\n"
        "Title\n"
        "C1\n"
        "C     6.0     0.0     0.0     0.0\n"
        " $END"
    ),
}

_NEXT_TOKEN_GUIDE: Dict[str, Any] = {
    "after_dollar": {
        "description": "After typing $, suggest group names",
        "suggestions": sorted(GAMESS_GROUPS.keys()),
    },
    "in_contrl": {
        "description": "Keywords for $CONTRL group",
        "suggestions": sorted(GAMESS_KEYWORDS.get("CONTRL", {}).keys()),
    },
    "in_basis": {
        "description": "Keywords for $BASIS group",
        "suggestions": sorted(GAMESS_KEYWORDS.get("BASIS", {}).keys()),
    },
    "in_system": {
        "description": "Keywords for $SYSTEM group",
        "suggestions": sorted(GAMESS_KEYWORDS.get("SYSTEM", {}).keys()),
    },
    "in_scf": {
        "description": "Keywords for $SCF group",
        "suggestions": sorted(GAMESS_KEYWORDS.get("SCF", {}).keys()),
    },
    "scftyp_values": {
        "description": "Allowed SCFTYP values",
        "suggestions": GAMESS_KEYWORDS.get("CONTRL", {}).get("SCFTYP", {}).get("values", []),
    },
    "runtyp_values": {
        "description": "Allowed RUNTYP values",
        "suggestions": GAMESS_KEYWORDS.get("CONTRL", {}).get("RUNTYP", {}).get("values", []),
    },
    "gbasis_values": {
        "description": "Allowed GBASIS values",
        "suggestions": GAMESS_KEYWORDS.get("BASIS", {}).get("GBASIS", {}).get("values", []),
    },
}


class AgentAPIProvider:
    def __init__(self) -> None:
        pass

    def get_snapshot(
        self,
        source: str,
        uri: str = "",
        version: Optional[int] = None,
        diagnostics: Optional[List[Diagnostic]] = None,
    ) -> AgentAPISnapshot:
        diag_dicts = [_diag_to_dict(d) for d in (diagnostics or [])]
        outline = self._build_outline(source)
        return AgentAPISnapshot(
            uri=uri,
            version=version,
            diagnostics=diag_dicts,
            outline=outline,
            metadata={
                "language": "gamess",
                "provider": "gamess_lsp",
                "feature_count": {"diagnostics": len(diag_dicts), "outline_items": len(outline)},
            },
        )

    def _build_outline(self, source: str) -> List[Dict[str, Any]]:
        outline: List[Dict[str, Any]] = []
        lines = source.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("!") and not stripped.startswith("#"):
                outline.append({"line": i, "text": stripped[:80], "type": "content"})
        return outline

    def get_diagnostics_json(
        self, source: str, uri: str = "", diagnostics: Optional[List[Diagnostic]] = None
    ) -> str:
        snap = self.get_snapshot(source, uri, diagnostics=diagnostics)
        return json.dumps(
            {"uri": snap.uri, "diagnostics": snap.diagnostics, "count": len(snap.diagnostics)},
            indent=2,
        )

    def get_outline_json(self, source: str, uri: str = "") -> str:
        snap = self.get_snapshot(source, uri)
        return json.dumps({"uri": snap.uri, "outline": snap.outline}, indent=2)

    # ------------------------------------------------------------------
    # Issue #58: Domain language description API
    # ------------------------------------------------------------------

    def get_domain_description(self) -> Dict[str, Any]:
        """Return a machine-readable description of the GAMESS domain language.

        Covers file format conventions, group structure, and common groups.
        """
        return dict(_DOMAIN_LANGUAGE)

    def get_domain_description_json(self) -> str:
        """Return the domain language description as JSON."""
        return json.dumps(self.get_domain_description(), indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Issue #59: Section and keyword schema lookup
    # ------------------------------------------------------------------

    def get_section_info(self, section_name: str) -> Optional[Dict[str, Any]]:
        """Look up schema information for a specific section.

        Args:
            section_name: The group name (e.g. 'CONTRL', 'BASIS').

        Returns:
            Section schema dict or None if the section is unknown.
        """
        schema = get_section_schema()
        return schema.get(section_name.upper())

    def get_keyword_info(self, section_name: str, keyword_name: str) -> Optional[Dict[str, Any]]:
        """Look up schema information for a keyword within a section.

        Args:
            section_name: The group name (e.g. 'CONTRL').
            keyword_name: The keyword name (e.g. 'SCFTYP').

        Returns:
            Keyword schema dict or None if not found.
        """
        section = self.get_section_info(section_name)
        if section is None:
            return None
        return section.get("keywords", {}).get(keyword_name.upper())

    def get_all_sections_json(self) -> str:
        """Return the full section/keyword schema as JSON."""
        return json.dumps(get_section_schema(), indent=2, sort_keys=True)

    def get_section_info_json(self, section_name: str) -> str:
        """Return section info as JSON."""
        info = self.get_section_info(section_name)
        if info is None:
            return json.dumps({"error": f"Unknown section: {section_name}"})
        return json.dumps(info, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Issue #60: Minimal examples and next-token guidance
    # ------------------------------------------------------------------

    def get_minimal_example(self, calculation_type: str) -> Optional[str]:
        """Return a minimal example for a given calculation type.

        Args:
            calculation_type: One of 'energy', 'optimize', 'dft', 'mp2'.

        Returns:
            Example input string or None if the type is unknown.
        """
        return _MINIMAL_EXAMPLES.get(calculation_type.lower())

    def get_all_examples(self) -> Dict[str, str]:
        """Return all minimal examples."""
        return dict(_MINIMAL_EXAMPLES)

    def get_all_examples_json(self) -> str:
        """Return all minimal examples as JSON."""
        return json.dumps(self.get_all_examples(), indent=2, sort_keys=True)

    def get_next_token_guidance(self, context: str) -> Optional[Dict[str, Any]]:
        """Return next-token suggestions for a given editing context.

        Args:
            context: The editing context (e.g. 'after_dollar', 'in_contrl').

        Returns:
            Guidance dict or None if the context is unknown.
        """
        return _NEXT_TOKEN_GUIDE.get(context.lower())

    def get_all_guidance(self) -> Dict[str, Any]:
        """Return all next-token guidance."""
        return dict(_NEXT_TOKEN_GUIDE)

    def get_all_guidance_json(self) -> str:
        """Return all next-token guidance as JSON."""
        return json.dumps(self.get_all_guidance(), indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Issue #76: OpenQC smoke test capability
    # ------------------------------------------------------------------

    def get_rule_manifest(self) -> Dict[str, Any]:
        """Return a manifest of all diagnostic rules this LSP provides.

        Used by OpenQC smoke tests to verify the LSP is functioning.
        """
        from .lint import (
            GAMESS_CONTROL_INVALID_RUNTYP,
            GAMESS_CONTROL_INVALID_SCFTYP,
            GAMESS_CONTROL_MISSING_CONTRL,
            GAMESS_DATA_CHARGE_MULT_MISMATCH,
            GAMESS_DATA_MISSING_DATA,
            GAMESS_LOG_RUNTIME_ERROR,
            GAMESS_LOG_SCF_NOT_CONVERGED,
            GAMESS_SYNTAX_MISSING_END,
        )

        rules = [
            {
                "code": GAMESS_SYNTAX_MISSING_END,
                "severity": "error",
                "description": "Group missing $END terminator",
            },
            {
                "code": GAMESS_CONTROL_MISSING_CONTRL,
                "severity": "error",
                "description": "Required $CONTRL group is missing",
            },
            {
                "code": GAMESS_CONTROL_INVALID_SCFTYP,
                "severity": "error",
                "description": "Invalid SCFTYP value in $CONTRL",
            },
            {
                "code": GAMESS_CONTROL_INVALID_RUNTYP,
                "severity": "error",
                "description": "Invalid RUNTYP value in $CONTRL",
            },
            {
                "code": GAMESS_DATA_MISSING_DATA,
                "severity": "error",
                "description": "Required $DATA group is missing",
            },
            {
                "code": GAMESS_DATA_CHARGE_MULT_MISMATCH,
                "severity": "warning",
                "description": "Charge/multiplicity mismatch with electron count",
            },
            {
                "code": GAMESS_LOG_SCF_NOT_CONVERGED,
                "severity": "error",
                "description": "SCF convergence failure in log output",
            },
            {
                "code": GAMESS_LOG_RUNTIME_ERROR,
                "severity": "error",
                "description": "Runtime error detected in log output",
            },
        ]
        return {
            "provider": "gamess-lsp",
            "version": "0.1.0",
            "rule_count": len(rules),
            "rules": rules,
        }

    def get_rule_manifest_json(self) -> str:
        """Return the rule manifest as JSON."""
        return json.dumps(self.get_rule_manifest(), indent=2, sort_keys=True)

    def openqc_smoke(self, source: str = "") -> Dict[str, Any]:
        """Run a smoke test for OpenQC integration.

        Parses a minimal GAMESS input, runs lint, and reports status.

        Args:
            source: Optional GAMESS input to test. If empty, uses a built-in
                minimal example.

        Returns:
            Smoke test result dict with 'status', 'diagnostics', and 'manifest'.
        """
        if not source:
            source = (
                " $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
                " $BASIS GBASIS=STO NGAUSS=3 $END\n"
                " $DATA\n"
                "Test molecule\n"
                "C1\n"
                "H     1.0   0.0   0.0   0.0\n"
                " $END"
            )

        # Parse the input
        parser = GAMESSParser()
        parsed = parser.parse(source)

        # Run lint
        from .lint import LintProvider
        from pygls.server import LanguageServer

        server = LanguageServer("smoke", "1.0")
        lint_provider = LintProvider(server)
        diagnostics = lint_provider.lint(source)

        diag_dicts = [_diag_to_dict(d) for d in diagnostics]

        return {
            "status": "ok",
            "parsed_groups": list(parsed.groups.keys()),
            "diagnostic_count": len(diag_dicts),
            "diagnostics": diag_dicts,
            "manifest": self.get_rule_manifest(),
        }

    def openqc_smoke_json(self, source: str = "") -> str:
        """Run OpenQC smoke test and return JSON."""
        return json.dumps(self.openqc_smoke(source), indent=2, sort_keys=True)
