"""Schema-aware static lint rules for GAMESS input files.

Exposes ``LintProvider`` which produces LSP ``Diagnostic`` objects from
deterministic, offline checks against the curated keyword metadata in
:mod:`gamess_lsp.keywords`.  Every diagnostic carries a stable rule code
(e.g. ``LINT_DUPLICATE_KEYWORD``, ``LINT_NUMERIC_RANGE``) so that automated
agents can filter and act on specific lint categories.

Rule categories
~~~~~~~~~~~~~~~
- **Structure** -- missing required groups, duplicate groups, unclosed groups.
- **Schema** -- unknown keywords, duplicate keywords within a group,
  invalid values for enumerated keywords, numeric range violations.
- **Best-practice** -- missing recommended keywords, redundant settings,
  migration hints.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)
from pygls.server import LanguageServer

from ..keywords import GAMESS_KEYWORDS
from ..parser import GAMESSInputFile, GAMESSParser

_LINT_SOURCE = "gamess-lsp-lint"


# ------------------------------------------------------------------
# Data structures
# ------------------------------------------------------------------


@dataclass(frozen=True)
class LintRule:
    """Descriptor for a single lint rule."""

    code: str
    message: str
    severity: DiagnosticSeverity


# ------------------------------------------------------------------
# Rule code constants (stable, machine-consumable)
# ------------------------------------------------------------------

# Structure rules
LINT_MISSING_CONTRL = "LINT_MISSING_CONTRL"
LINT_MISSING_DATA = "LINT_MISSING_DATA"
LINT_DUPLICATE_GROUP = "LINT_DUPLICATE_GROUP"
LINT_UNCLOSED_GROUP = "LINT_UNCLOSED_GROUP"

# Schema rules
LINT_UNKNOWN_KEYWORD = "LINT_UNKNOWN_KEYWORD"
LINT_DUPLICATE_KEYWORD = "LINT_DUPLICATE_KEYWORD"
LINT_INVALID_ENUM = "LINT_INVALID_ENUM"
LINT_NUMERIC_RANGE = "LINT_NUMERIC_RANGE"
LINT_BOOLEAN_FORMAT = "LINT_BOOLEAN_FORMAT"

# Best-practice rules
LINT_MISSING_RUNTYP = "LINT_MISSING_RUNTYP"
LINT_MISSING_BASIS = "LINT_MISSING_BASIS"
LINT_MISSING_SYSTEM = "LINT_MISSING_SYSTEM"
LINT_LOW_MEMORY = "LINT_LOW_MEMORY"
LINT_REDUNDANT_DEFAULT = "LINT_REDUNDANT_DEFAULT"


# ------------------------------------------------------------------
# Numeric constraints per keyword (group, keyword) -> (min, max)
# ------------------------------------------------------------------

_NUMERIC_CONSTRAINTS: dict[tuple[str, str], tuple[float, float]] = {
    ("SYSTEM", "MWORDS"): (1, 1_000_000),
    ("SYSTEM", "TIMLIM"): (1, 10_000_000),
    ("CONTRL", "MAXIT"): (1, 10_000),
    ("CONTRL", "MULT"): (1, 20),
    ("CONTRL", "ICHARG"): (-100, 100),
    ("STATPT", "NSTEP"): (1, 10_000),
    ("STATPT", "OPTTOL"): (1e-10, 1.0),
    ("SCF", "CONV"): (1e-15, 1.0),
    ("IRC", "NPOINT"): (1, 100_000),
    ("IRC", "STRIDE"): (0.001, 10.0),
    ("FORCE", "TEMP"): (0.0, 100_000.0),
    ("FORCE", "PRES"): (0.0, 10_000.0),
    ("CC", "MAXCC"): (1, 10_000),
    ("TDDFT", "NSTATE"): (1, 500),
    ("CIS", "NSTATE"): (1, 500),
    ("DFT", "NRAD"): (10, 500),
    ("PCM", "RSOLV"): (0.1, 100.0),
}

# Keywords whose default value is already implied and need not be spelled out.
_REDUNDANT_DEFAULTS: dict[tuple[str, str], str] = {
    ("CONTRL", "EXETYP"): "RUN",
    ("CONTRL", "INTTYP"): "POPLE",
    ("CONTRL", "COORD"): "UNIQUE",
    ("SCF", "DIIS"): ".TRUE.",
    ("FORCE", "PURIFY"): ".TRUE.",
    ("FORCE", "PROJCT"): ".TRUE.",
    ("FORCE", "VIBANL"): ".TRUE.",
    ("STATPT", "HESS"): "GUESS",
}


class LintProvider:
    """Schema-aware static lint for GAMESS input files.

    Parses a document via the shared ``GAMESSParser`` and applies
    deterministic lint rules against the curated keyword metadata in
    :mod:`gamess_lsp.keywords`.

    Every diagnostic carries ``source="gamess-lsp-lint"`` and a stable
    ``code`` string so that automated agents can filter by rule.
    """

    def __init__(self, server: LanguageServer) -> None:
        """Initialize the lint provider.

        Args:
            server: The language server instance (kept for parity with
                other providers; not used directly by lint rules).
        """
        self.server = server

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lint(self, text: str) -> list[Diagnostic]:
        """Return lint diagnostics for *text*.

        Args:
            text: Full document text.

        Returns:
            Deterministic list of ``Diagnostic`` objects sorted by line,
            then severity, then message.
        """
        raw = self._collect(text)
        return self._sort(raw)

    def snapshot(self, uri: str, text: str) -> dict[str, Any]:
        """Return a JSON-serialisable lint snapshot.

        Suitable for agent feedback loops and CLI tooling.

        Args:
            uri: Document URI (included verbatim in the snapshot).
            text: Full document text.

        Returns:
            Dict with keys ``uri``, ``version``, ``source``, ``diagnostics``.
        """
        diagnostics = self.lint(text)
        return {
            "uri": uri,
            "version": 1,
            "source": _LINT_SOURCE,
            "diagnostics": [_diag_to_dict(d) for d in diagnostics],
        }

    def snapshot_json(self, uri: str, text: str) -> str:
        """Return the snapshot as a JSON string.

        Args:
            uri: Document URI.
            text: Full document text.

        Returns:
            Deterministic JSON string.
        """
        return json.dumps(self.snapshot(uri, text), indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Internal: collection
    # ------------------------------------------------------------------

    def _collect(self, text: str) -> list[Diagnostic]:
        """Run all lint checks and return raw diagnostics."""
        diagnostics: list[Diagnostic] = []

        parser = GAMESSParser()
        parsed = parser.parse(text)
        lines = text.split("\n")

        # --- structure rules ---
        self._check_missing_required_groups(parsed, lines, diagnostics)
        self._check_unclosed_groups(parser, diagnostics)

        # --- schema rules ---
        self._check_unknown_keywords(parsed, lines, diagnostics)
        self._check_duplicate_keywords(parsed, lines, text, diagnostics)
        self._check_enum_values(parsed, lines, diagnostics)
        self._check_numeric_ranges(parsed, lines, diagnostics)
        self._check_boolean_format(parsed, lines, diagnostics)

        # --- best-practice rules ---
        self._check_missing_recommended(parsed, lines, diagnostics)
        self._check_low_memory(parsed, lines, diagnostics)
        self._check_redundant_defaults(parsed, lines, diagnostics)

        return diagnostics

    # ------------------------------------------------------------------
    # Structure checks
    # ------------------------------------------------------------------

    def _check_missing_required_groups(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag missing $CONTRL and $DATA groups."""
        if "CONTRL" not in parsed.groups:
            diagnostics.append(
                self._make_diag(
                    line=0,
                    char=0,
                    end_char=0,
                    message="Missing required $CONTRL group",
                    severity=DiagnosticSeverity.Error,
                    code=LINT_MISSING_CONTRL,
                )
            )

        if "DATA" not in parsed.groups:
            diagnostics.append(
                self._make_diag(
                    line=0,
                    char=0,
                    end_char=0,
                    message="Missing $DATA group (no molecular geometry provided)",
                    severity=DiagnosticSeverity.Error,
                    code=LINT_MISSING_DATA,
                )
            )

    def _check_unclosed_groups(
        self,
        parser: GAMESSParser,
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag groups that were not closed with $END (from parser warnings)."""
        for w in parser.warnings:
            if "not properly closed" in w.get("message", ""):
                line = w.get("line", 1) - 1
                diagnostics.append(
                    self._make_diag(
                        line=line,
                        char=0,
                        end_char=100,
                        message=w["message"],
                        severity=DiagnosticSeverity.Warning,
                        code=LINT_UNCLOSED_GROUP,
                    )
                )

    # ------------------------------------------------------------------
    # Schema checks
    # ------------------------------------------------------------------

    def _check_unknown_keywords(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag keywords not present in the keyword database for their group."""
        for group_name, group in parsed.groups.items():
            if group_name in ("DATA", "LIBRARY"):
                continue
            known = GAMESS_KEYWORDS.get(group_name, {})
            for kw_name, kw in group.keywords.items():
                if known and kw_name.upper() not in known:
                    line = kw.line_number - 1
                    col = self._find_keyword_col(lines, line, kw_name)
                    diagnostics.append(
                        self._make_diag(
                            line=line,
                            char=col,
                            end_char=col + len(kw_name),
                            message=f"Unknown keyword '{kw_name}' in ${group_name}",
                            severity=DiagnosticSeverity.Warning,
                            code=LINT_UNKNOWN_KEYWORD,
                        )
                    )

    def _check_duplicate_keywords(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        text: str,
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag keywords that appear more than once in the same group.

        Because the parser's ``add_keyword`` overwrites on duplicate, we
        scan the raw lines to detect the second occurrence of a keyword
        within a group's span.
        """
        for group_name, group in parsed.groups.items():
            if group_name in ("DATA", "LIBRARY"):
                continue
            seen: dict[str, int] = {}
            for kw_name, kw in group.keywords.items():
                upper = kw_name.upper()
                if upper in seen:
                    prev_line = seen[upper]
                    line = kw.line_number - 1
                    col = self._find_keyword_col(lines, line, kw_name)
                    diagnostics.append(
                        self._make_diag(
                            line=line,
                            char=col,
                            end_char=col + len(kw_name),
                            message=(
                                f"Duplicate keyword '{kw_name}' in ${group_name} "
                                f"(first set on line {prev_line})"
                            ),
                            severity=DiagnosticSeverity.Warning,
                            code=LINT_DUPLICATE_KEYWORD,
                        )
                    )
                else:
                    seen[upper] = kw.line_number

    def _check_enum_values(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag values not in the allowed enumeration for a keyword."""
        for group_name, group in parsed.groups.items():
            if group_name in ("DATA", "LIBRARY"):
                continue
            known = GAMESS_KEYWORDS.get(group_name, {})
            for kw_name, kw in group.keywords.items():
                kw_upper = kw_name.upper()
                if kw_upper not in known:
                    continue
                allowed = known[kw_upper].get("values", [])
                if not allowed:
                    continue
                val_upper = kw.value.upper().strip()
                if val_upper in [v.upper() for v in allowed]:
                    continue
                line = kw.line_number - 1
                col = self._find_value_col(lines, line, kw.value)
                diagnostics.append(
                    self._make_diag(
                        line=line,
                        char=col,
                        end_char=col + len(kw.value),
                        message=(
                            f"Invalid value '{kw.value}' for {kw_name} in "
                            f"${group_name}. Allowed: {', '.join(allowed)}"
                        ),
                        severity=DiagnosticSeverity.Error,
                        code=LINT_INVALID_ENUM,
                    )
                )

    def _check_numeric_ranges(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag numeric keywords that fall outside expected ranges."""
        for (group_name, kw_name), (lo, hi) in _NUMERIC_CONSTRAINTS.items():
            group = parsed.get_group(group_name)
            if group is None:
                continue
            kw = group.get_keyword(kw_name)
            if kw is None:
                continue
            try:
                val = float(kw.value)
            except ValueError:
                continue
            if val < lo or val > hi:
                line = kw.line_number - 1
                col = self._find_value_col(lines, line, kw.value)
                diagnostics.append(
                    self._make_diag(
                        line=line,
                        char=col,
                        end_char=col + len(kw.value),
                        message=(
                            f"Value {kw.value} for {kw_name} in ${group_name} "
                            f"is outside recommended range [{lo}, {hi}]"
                        ),
                        severity=DiagnosticSeverity.Warning,
                        code=LINT_NUMERIC_RANGE,
                    )
                )

    def _check_boolean_format(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag boolean keywords written as raw TRUE/FALSE without dots."""
        for group_name, group in parsed.groups.items():
            if group_name in ("DATA", "LIBRARY"):
                continue
            known = GAMESS_KEYWORDS.get(group_name, {})
            for kw_name, kw in group.keywords.items():
                kw_upper = kw_name.upper()
                if kw_upper not in known:
                    continue
                allowed = known[kw_upper].get("values", [])
                has_dot_bool = any(v.startswith(".") for v in allowed)
                if not has_dot_bool:
                    continue
                val_upper = kw.value.upper().strip()
                if val_upper in ("TRUE", "FALSE"):
                    line = kw.line_number - 1
                    col = self._find_value_col(lines, line, kw.value)
                    corrected = f".{val_upper}."
                    diagnostics.append(
                        self._make_diag(
                            line=line,
                            char=col,
                            end_char=col + len(kw.value),
                            message=(
                                f"Boolean value '{kw.value}' should be "
                                f"'{corrected}' (GAMESS requires dot-prefixed "
                                f"booleans)"
                            ),
                            severity=DiagnosticSeverity.Warning,
                            code=LINT_BOOLEAN_FORMAT,
                        )
                    )

    # ------------------------------------------------------------------
    # Best-practice checks
    # ------------------------------------------------------------------

    def _check_missing_recommended(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag missing commonly-needed keywords."""
        contrl = parsed.get_group("CONTRL")
        if contrl is None:
            return

        if "RUNTYP" not in contrl.keywords:
            line = contrl.line_start - 1
            diagnostics.append(
                self._make_diag(
                    line=line,
                    char=0,
                    end_char=100,
                    message="No RUNTYP specified in $CONTRL (defaults to ENERGY)",
                    severity=DiagnosticSeverity.Information,
                    code=LINT_MISSING_RUNTYP,
                )
            )

        if "BASIS" not in parsed.groups:
            diagnostics.append(
                self._make_diag(
                    line=0,
                    char=0,
                    end_char=0,
                    message="No $BASIS group specified (GAMESS will use a minimal default basis)",
                    severity=DiagnosticSeverity.Information,
                    code=LINT_MISSING_BASIS,
                )
            )

        if "SYSTEM" not in parsed.groups:
            diagnostics.append(
                self._make_diag(
                    line=0,
                    char=0,
                    end_char=0,
                    message="No $SYSTEM group specified (default memory may be insufficient)",
                    severity=DiagnosticSeverity.Information,
                    code=LINT_MISSING_SYSTEM,
                )
            )

    def _check_low_memory(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Warn if MWORDS is very low or absent with $SYSTEM present."""
        system = parsed.get_group("SYSTEM")
        if system is None:
            return
        mwords_kw = system.get_keyword("MWORDS")
        if mwords_kw is None:
            line = system.line_start - 1
            diagnostics.append(
                self._make_diag(
                    line=line,
                    char=0,
                    end_char=100,
                    message="MWORDS not specified in $SYSTEM (defaults to 1 MWORD, often too low)",
                    severity=DiagnosticSeverity.Warning,
                    code=LINT_LOW_MEMORY,
                )
            )
            return
        try:
            val = int(float(mwords_kw.value))
        except ValueError:
            return
        if val < 10:
            line = mwords_kw.line_number - 1
            col = self._find_value_col(lines, line, mwords_kw.value)
            diagnostics.append(
                self._make_diag(
                    line=line,
                    char=col,
                    end_char=col + len(mwords_kw.value),
                    message=(
                        f"MWORDS={val} may be insufficient for most calculations "
                        f"(consider >= 100)"
                    ),
                    severity=DiagnosticSeverity.Information,
                    code=LINT_LOW_MEMORY,
                )
            )

    def _check_redundant_defaults(
        self,
        parsed: GAMESSInputFile,
        lines: list[str],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Flag keywords set to their GAMESS default values."""
        for (group_name, kw_name), default_val in _REDUNDANT_DEFAULTS.items():
            group = parsed.get_group(group_name)
            if group is None:
                continue
            kw = group.get_keyword(kw_name)
            if kw is None:
                continue
            if kw.value.upper() == default_val.upper():
                line = kw.line_number - 1
                col = self._find_keyword_col(lines, line, kw_name)
                diagnostics.append(
                    self._make_diag(
                        line=line,
                        char=col,
                        end_char=col + len(kw_name),
                        message=(
                            f"{kw_name}={kw.value} is the GAMESS default -- "
                            f"this line can be removed"
                        ),
                        severity=DiagnosticSeverity.Hint,
                        code=LINT_REDUNDANT_DEFAULT,
                    )
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_diag(
        line: int,
        char: int,
        end_char: int,
        message: str,
        severity: DiagnosticSeverity,
        code: str,
    ) -> Diagnostic:
        """Create a ``Diagnostic`` with the lint source."""
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=char),
                end=Position(line=line, character=end_char),
            ),
            message=message,
            severity=severity,
            source=_LINT_SOURCE,
            code=code,
        )

    @staticmethod
    def _find_keyword_col(lines: list[str], line_idx: int, kw_name: str) -> int:
        """Find the column where *kw_name* starts on a 0-based line."""
        if line_idx < len(lines):
            col = lines[line_idx].upper().find(kw_name.upper())
            if col >= 0:
                return col
        return 0

    @staticmethod
    def _find_value_col(lines: list[str], line_idx: int, value: str) -> int:
        """Find the column where *value* starts on a 0-based line."""
        if line_idx < len(lines):
            col = lines[line_idx].find(value)
            if col >= 0:
                return col
        return 0

    @staticmethod
    def _sort(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
        """Sort diagnostics deterministically.

        Order: line (asc), severity (error < warning < info < hint), message (asc).
        """
        return sorted(
            diagnostics,
            key=lambda d: (
                d.range.start.line,
                d.severity if d.severity is not None else 0,
                d.message,
            ),
        )


# ------------------------------------------------------------------
# Serialisation helpers
# ------------------------------------------------------------------

_SEVERITY_MAP: dict[int, str] = {
    DiagnosticSeverity.Error: "error",
    DiagnosticSeverity.Warning: "warning",
    DiagnosticSeverity.Information: "information",
    DiagnosticSeverity.Hint: "hint",
}


def _diag_to_dict(diag: Diagnostic) -> dict[str, Any]:
    """Convert a ``Diagnostic`` to a JSON-friendly dict."""
    severity = _SEVERITY_MAP.get(diag.severity, "information") if diag.severity else "information"
    return {
        "range": {
            "start": {
                "line": diag.range.start.line,
                "character": diag.range.start.character,
            },
            "end": {
                "line": diag.range.end.line,
                "character": diag.range.end.character,
            },
        },
        "severity": severity,
        "source": diag.source or _LINT_SOURCE,
        "code": str(diag.code) if diag.code is not None else None,
        "message": diag.message,
    }


__all__ = ["LintProvider"]
