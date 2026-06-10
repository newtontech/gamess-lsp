"""Type-checking validation for GAMESS keyword values.

Validates keyword value types (integer, float, boolean, enum, string),
checks enum membership against the keyword database, validates units where
applicable, and reports missing required sections.

Produces LSP ``Diagnostic`` objects with ``source="gamess-lsp-typecheck"``
so that typecheck diagnostics are clearly distinguishable from syntax and
semantic diagnostics.
"""

from __future__ import annotations

import re
from typing import Any

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)

from ..keywords import GAMESS_KEYWORDS
from ..parser import GAMESSInputFile, GAMESSKeyword

_DIAGNOSTIC_SOURCE = "gamess-lsp-typecheck"

# ---------------------------------------------------------------------------
# Type metadata for keywords that accept numeric / boolean values.
# ---------------------------------------------------------------------------

_NUMERIC_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?(?:[eEdD][+-]?\d+)?$")
_INTEGER_RE = re.compile(r"^[+-]?\d+$")

# Keywords whose values must be integers.
_INTEGER_KEYWORDS: set[tuple[str, str]] = {
    ("CONTRL", "MAXIT"),
    ("CONTRL", "MULT"),
    ("CONTRL", "ICHARG"),
    ("CONTRL", "ISPHER"),
    ("SYSTEM", "MWORDS"),
    ("SYSTEM", "MEMDDI"),
    ("SYSTEM", "TIMLIM"),
    ("BASIS", "NGAUSS"),
    ("BASIS", "NDFUNC"),
    ("BASIS", "NFFUNC"),
    ("SCF", "NWORD"),
    ("DFT", "NRAD"),
    ("STATPT", "NSTEP"),
    ("STATPT", "IFOLOW"),
    ("FORCE", "ANHALG"),
    ("CC", "NCORE"),
    ("CC", "MAXCC"),
    ("CIS", "NSTATE"),
    ("CIS", "IROOT"),
    ("TDDFT", "NSTATE"),
    ("TDDFT", "IROOT"),
    ("TDDFT", "MAXVEC"),
    ("IRC", "NPOINT"),
    ("DRC", "NSTEP"),
    ("SURFACE", "NSURF"),
    ("SURFACE", "IVEC"),
    ("SURFACE", "NVIB"),
    ("MCSCF", "MAXIT"),
    ("MP2", "NACORE"),
    ("CI", "NFZC"),
    ("CI", "NDOC"),
    ("CI", "NALP"),
    ("GUESS", "NORB"),
    ("SYSTEM", "KDIAG"),
}

# Keywords whose values must be positive integers.
_POSITIVE_INTEGER_KEYWORDS: set[tuple[str, str]] = {
    ("CONTRL", "MULT"),
    ("CONTRL", "MAXIT"),
    ("SYSTEM", "MWORDS"),
    ("SYSTEM", "MEMDDI"),
    ("SYSTEM", "TIMLIM"),
    ("BASIS", "NGAUSS"),
    ("STATPT", "NSTEP"),
    ("CC", "MAXCC"),
    ("CIS", "NSTATE"),
    ("CIS", "IROOT"),
    ("TDDFT", "NSTATE"),
    ("TDDFT", "IROOT"),
    ("TDDFT", "MAXVEC"),
    ("IRC", "NPOINT"),
    ("DRC", "NSTEP"),
    ("MCSCF", "MAXIT"),
}

# Keywords whose values must be floats (or scientific notation).
_FLOAT_KEYWORDS: set[tuple[str, str]] = {
    ("CONTRL", "OPTTOL"),
    ("SCF", "CONV"),
    ("SCF", "ETHRSH"),
    ("DFT", "DFTTHR"),
    ("DFT", "LAMBDA"),
    ("STATPT", "OPTTOL"),
    ("STATPT", "TRMAX"),
    ("STATPT", "TRMIN"),
    ("FORCE", "TEMP"),
    ("FORCE", "PRES"),
    ("FORCE", "SCLFAC"),
    ("CC", "CCCONV"),
    ("TDDFT", "CVG"),
    ("MCSCF", "ACURCY"),
    ("IRC", "STRIDE"),
    ("DRC", "TINIT"),
    ("DRC", "DELTAT"),
    ("VIB", "SCLFAC"),
    ("PCM", "EPS"),
    ("PCM", "RSOLV"),
    ("COSM", "EPS"),
    ("COSM", "RSOLV"),
}

# Keywords whose values must be GAMESS booleans (.TRUE./.FALSE./1/0).
_BOOLEAN_KEYWORDS: set[tuple[str, str]] = {
    ("CONTRL", "NOSYM"),
    ("CONTRL", "EFP"),
    ("CONTRL", "PROPS"),
    ("BASIS", "DIFFSP"),
    ("BASIS", "DIFFS"),
    ("BASIS", "EXTFIL"),
    ("SCF", "DIRSCF"),
    ("SCF", "DIIS"),
    ("SCF", "SOSCF"),
    ("STATPT", "HSSEND"),
    ("STATPT", "STPT"),
    ("FORCE", "VIBANL"),
    ("FORCE", "PURIFY"),
    ("FORCE", "PROJCT"),
    ("GUESS", "PRTMO"),
    ("GUESS", "MIX"),
    ("IRC", "FORWRD"),
    ("MCSCF", "FULLNR"),
    ("MP2", "MP2PRP"),
    ("HESSIAN", "PRTIFC"),
    ("HESSIAN", "VIBANL"),
    ("ECP", "PTRAD"),
    ("NBO", "NPA"),
    ("SYSTEM", "PARALL"),
}

_BOOLEAN_VALUES = {".TRUE.", ".FALSE.", "1", "0"}

# Unit annotations for diagnostic messages.
_UNIT_ANNOTATIONS: dict[tuple[str, str], str] = {
    ("SYSTEM", "MWORDS"): "million words (8 bytes each)",
    ("SYSTEM", "MEMDDI"): "million words",
    ("SYSTEM", "TIMLIM"): "minutes",
    ("SCF", "CONV"): "energy change (Hartree)",
    ("FORCE", "TEMP"): "Kelvin",
    ("FORCE", "PRES"): "atm",
    ("FORCE", "SCLFAC"): "dimensionless",
    ("STATPT", "OPTTOL"): "Hartree/Bohr",
    ("IRC", "STRIDE"): "amu^(1/2) * Bohr",
    ("DRC", "TINIT"): "Kelvin",
    ("DRC", "DELTAT"): "femtoseconds",
    ("PCM", "RSOLV"): "Angstroms",
    ("COSM", "RSOLV"): "Angstroms",
}

# Groups that are always required.
_REQUIRED_GROUPS: list[tuple[str, str, DiagnosticSeverity]] = [
    ("CONTRL", "$CONTRL group is required in every GAMESS input", DiagnosticSeverity.Error),
]

# Groups required depending on conditions.
_CONDITIONALLY_REQUIRED: list[dict[str, Any]] = [
    {
        "condition": lambda _parsed: True,
        "group": "DATA",
        "message": "$DATA group is required to specify molecular geometry",
        "severity": DiagnosticSeverity.Error,
    },
]


class TypecheckProvider:
    """Validates GAMESS keyword value types, enums, units, and required sections.

    This provider is intentionally separate from the semantic validator so
    that typecheck diagnostics carry their own ``source`` tag and can be
    enabled/disabled independently.
    """

    def validate(self, parsed_input: GAMESSInputFile) -> list[Diagnostic]:
        """Run typecheck validation on a parsed GAMESS input.

        Args:
            parsed_input: Parsed GAMESS input file.

        Returns:
            List of LSP Diagnostic objects with source ``gamess-lsp-typecheck``.
        """
        diagnostics: list[Diagnostic] = []

        # 1. Required groups
        self._check_required_groups(parsed_input, diagnostics)

        # 2. Per-keyword type + enum validation
        for group_name, group in parsed_input.groups.items():
            known_keywords = GAMESS_KEYWORDS.get(group_name, {})
            for kw_name, keyword in group.keywords.items():
                kw_upper = kw_name.upper()
                # Skip non-keyword groups
                if group_name in ("DATA", "LIBRARY"):
                    continue
                # Enum validation (if the keyword has restricted values)
                if kw_upper in known_keywords:
                    self._check_enum(
                        group_name, kw_upper, keyword, known_keywords[kw_upper], diagnostics
                    )
                # Type validation
                self._check_type(group_name, kw_upper, keyword, diagnostics)

        return diagnostics

    # ------------------------------------------------------------------
    # Required groups
    # ------------------------------------------------------------------

    def _check_required_groups(
        self, parsed_input: GAMESSInputFile, diagnostics: list[Diagnostic]
    ) -> None:
        """Report missing required groups."""
        present = set(parsed_input.groups.keys())

        for group_name, message, severity in _REQUIRED_GROUPS:
            if group_name not in present:
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=0, character=0),
                            end=Position(line=0, character=1),
                        ),
                        message=message,
                        severity=severity,
                        source=_DIAGNOSTIC_SOURCE,
                        code="MISSING_REQUIRED_GROUP",
                    )
                )

        for rule in _CONDITIONALLY_REQUIRED:
            if rule["condition"](parsed_input) and rule["group"] not in present:
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=0, character=0),
                            end=Position(line=0, character=1),
                        ),
                        message=rule["message"],
                        severity=rule["severity"],
                        source=_DIAGNOSTIC_SOURCE,
                        code="MISSING_REQUIRED_GROUP",
                    )
                )

    # ------------------------------------------------------------------
    # Enum validation
    # ------------------------------------------------------------------

    def _check_enum(
        self,
        group_name: str,
        kw_upper: str,
        keyword: GAMESSKeyword,
        kw_info: dict[str, Any],
        diagnostics: list[Diagnostic],
    ) -> None:
        """Validate that a keyword value is in its allowed enum set."""
        allowed_values = kw_info.get("values", [])
        if not allowed_values:
            return

        value_upper = keyword.value.upper()
        allowed_upper = [v.upper() for v in allowed_values]
        if value_upper in allowed_upper:
            return

        line = keyword.line_number - 1
        col_start = self._value_column(keyword)
        col_end = col_start + len(keyword.value)

        diagnostics.append(
            Diagnostic(
                range=Range(
                    start=Position(line=line, character=col_start),
                    end=Position(line=line, character=col_end),
                ),
                message=(
                    f"Invalid value '{keyword.value}' for {kw_upper} in "
                    f"${group_name}. Allowed values: {', '.join(allowed_values)}"
                ),
                severity=DiagnosticSeverity.Error,
                source=_DIAGNOSTIC_SOURCE,
                code="INVALID_ENUM",
            )
        )

    # ------------------------------------------------------------------
    # Type validation
    # ------------------------------------------------------------------

    def _check_type(
        self,
        group_name: str,
        kw_upper: str,
        keyword: GAMESSKeyword,
        diagnostics: list[Diagnostic],
    ) -> None:
        """Validate the type of a keyword value."""
        key = (group_name, kw_upper)
        value = keyword.value.strip()

        if not value:
            return

        line = keyword.line_number - 1
        col_start = self._value_column(keyword)
        col_end = col_start + len(value)

        # Boolean check (takes precedence)
        if key in _BOOLEAN_KEYWORDS:
            if value.upper() not in _BOOLEAN_VALUES:
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line, character=col_start),
                            end=Position(line=line, character=col_end),
                        ),
                        message=(
                            f"Expected boolean for {kw_upper} in ${group_name}, "
                            f"got '{value}'. Use .TRUE. or .FALSE."
                        ),
                        severity=DiagnosticSeverity.Error,
                        source=_DIAGNOSTIC_SOURCE,
                        code="TYPE_BOOLEAN",
                    )
                )
            return

        # Positive integer check (stricter than general integer)
        if key in _POSITIVE_INTEGER_KEYWORDS:
            if not _INTEGER_RE.match(value):
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line, character=col_start),
                            end=Position(line=line, character=col_end),
                        ),
                        message=(
                            f"Expected positive integer for {kw_upper} in "
                            f"${group_name}, got '{value}'." + self._unit_hint(key)
                        ),
                        severity=DiagnosticSeverity.Error,
                        source=_DIAGNOSTIC_SOURCE,
                        code="TYPE_INTEGER",
                    )
                )
                return
            int_val = int(value)
            if int_val <= 0:
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line, character=col_start),
                            end=Position(line=line, character=col_end),
                        ),
                        message=(
                            f"Expected positive integer for {kw_upper} in "
                            f"${group_name}, got {int_val}." + self._unit_hint(key)
                        ),
                        severity=DiagnosticSeverity.Error,
                        source=_DIAGNOSTIC_SOURCE,
                        code="TYPE_POSITIVE_INTEGER",
                    )
                )
            return

        # General integer check
        if key in _INTEGER_KEYWORDS:
            if not _INTEGER_RE.match(value):
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line, character=col_start),
                            end=Position(line=line, character=col_end),
                        ),
                        message=(
                            f"Expected integer for {kw_upper} in ${group_name}, "
                            f"got '{value}'." + self._unit_hint(key)
                        ),
                        severity=DiagnosticSeverity.Error,
                        source=_DIAGNOSTIC_SOURCE,
                        code="TYPE_INTEGER",
                    )
                )
            return

        # Float check
        if key in _FLOAT_KEYWORDS:
            if not _NUMERIC_RE.match(value):
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line, character=col_start),
                            end=Position(line=line, character=col_end),
                        ),
                        message=(
                            f"Expected numeric value for {kw_upper} in "
                            f"${group_name}, got '{value}'." + self._unit_hint(key)
                        ),
                        severity=DiagnosticSeverity.Error,
                        source=_DIAGNOSTIC_SOURCE,
                        code="TYPE_NUMERIC",
                    )
                )
            return

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _value_column(keyword: GAMESSKeyword) -> int:
        """Estimate the column where the value starts on the keyword's line.

        GAMESS keyword lines look like ``KEY=VALUE`` or `` KEY=VALUE``.
        We look for the ``=`` and advance past it.
        """
        return len(keyword.name) + 1  # len(key) + "="

    @staticmethod
    def _unit_hint(key: tuple[str, str]) -> str:
        """Return a unit annotation string if one is defined for *key*."""
        unit = _UNIT_ANNOTATIONS.get(key)
        if unit:
            return f" Unit: {unit}."
        return ""


__all__ = ["TypecheckProvider"]
