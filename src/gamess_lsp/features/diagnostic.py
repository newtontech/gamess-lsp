"""LSP diagnostic provider for GAMESS input files.

Exposes live diagnostics snapshots suitable for both LSP clients and
machine-readable agent feedback loops.
"""

from __future__ import annotations

import json
from typing import Any

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)
from pygls.server import LanguageServer

from ..keywords import GAMESS_KEYWORDS
from ..parser import GAMESSParser
from ..validator import validate_semantics
from .typecheck import TypecheckProvider

_DIAGNOSTIC_SOURCE = "gamess-lsp"


class DiagnosticProvider:
    """Provider for GAMESS diagnostics.

    Parses a document, runs syntax and semantic validation, and returns
    a deterministic list of ``Diagnostic`` objects.  Also exposes a
    CLI-friendly ``snapshot`` method that returns JSON-serialisable
    diagnostic payloads for agent feedback loops.
    """

    def __init__(self, server: LanguageServer) -> None:
        """Initialize diagnostic provider.

        Args:
            server: The language server instance.
        """
        self.server = server

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_diagnostics(self, text: str) -> list[Diagnostic]:
        """Get LSP diagnostics for *text*.

        Args:
            text: Full document text.

        Returns:
            Deterministic list of ``Diagnostic`` objects sorted by line
            then severity then message.
        """
        raw = self._collect_diagnostics(text)
        return self._sort_diagnostics(raw)

    def snapshot(self, uri: str, text: str) -> dict[str, Any]:
        """Return a JSON-serialisable diagnostics snapshot.

        Suitable for agent feedback loops and CLI tooling that need
        machine-readable diagnostics without going through the LSP wire
        protocol.

        Args:
            uri: Document URI (included verbatim in the snapshot).
            text: Full document text.

        Returns:
            A dict with keys ``uri``, ``version``, and ``diagnostics``.
        """
        diagnostics = self.get_diagnostics(text)
        return {
            "uri": uri,
            "version": 1,
            "diagnostics": [_diagnostic_to_dict(d) for d in diagnostics],
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
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_diagnostics(self, text: str) -> list[Diagnostic]:
        """Run syntax and semantic validation, returning raw diagnostics."""
        diagnostics: list[Diagnostic] = []

        # 1. Syntax-level diagnostics from parser
        parser = GAMESSParser()
        parsed_input = parser.parse(text)

        for item in parser.get_diagnostics():
            severity = DiagnosticSeverity.Warning
            if item.get("severity") == "error":
                severity = DiagnosticSeverity.Error

            line = item.get("line", 1) - 1  # 0-based
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line, character=0),
                        end=Position(line=line, character=100),
                    ),
                    message=item.get("message", ""),
                    severity=severity,
                    source=_DIAGNOSTIC_SOURCE,
                )
            )

        # 2. Semantic-level diagnostics from validator
        semantic_diagnostics = validate_semantics(parsed_input)
        for diag in semantic_diagnostics:
            severity = DiagnosticSeverity.Warning
            if diag.severity == "error":
                severity = DiagnosticSeverity.Error

            line = diag.line - 1  # Convert to 0-based
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line, character=0),
                        end=Position(line=line, character=100),
                    ),
                    message=diag.message,
                    severity=severity,
                    source=_DIAGNOSTIC_SOURCE,
                    code=diag.code,
                )
            )

        # 3. Keyword-level validation against known keywords
        self._validate_keywords(parsed_input, diagnostics)

        # 4. Typecheck diagnostics (enum, type, required sections)
        typecheck_provider = TypecheckProvider()
        diagnostics.extend(typecheck_provider.validate(parsed_input))
        return diagnostics

    def _validate_keywords(
        self,
        parsed_input: Any,
        diagnostics: list[Diagnostic],
    ) -> None:
        """Validate keyword values against the known keyword database.

        Checks for unknown keywords and invalid values within known
        groups.
        """
        for group_name, group in parsed_input.groups.items():
            known_keywords = GAMESS_KEYWORDS.get(group_name, {})

            for kw_name, keyword in group.keywords.items():
                kw_upper = kw_name.upper()

                # Skip $DATA and other non-keyword groups
                if group_name in ("DATA", "LIBRARY"):
                    continue

                # Check for unknown keyword in a known group
                if known_keywords and kw_upper not in known_keywords:
                    line = keyword.line_number - 1  # 0-based
                    diagnostics.append(
                        Diagnostic(
                            range=Range(
                                start=Position(line=line, character=0),
                                end=Position(line=line, character=len(kw_name)),
                            ),
                            message=f"Unknown keyword '{kw_name}' in ${group_name}",
                            severity=DiagnosticSeverity.Warning,
                            source=_DIAGNOSTIC_SOURCE,
                            code="UNKNOWN_KEYWORD",
                        )
                    )
                    continue

                # Validate value if the keyword has a restricted value set
                if kw_upper in known_keywords:
                    kw_info = known_keywords[kw_upper]
                    allowed_values = kw_info.get("values", [])
                    if allowed_values:
                        value_upper = keyword.value.upper()
                        if value_upper not in [v.upper() for v in allowed_values]:
                            line = keyword.line_number - 1  # 0-based
                            diagnostics.append(
                                Diagnostic(
                                    range=Range(
                                        start=Position(line=line, character=0),
                                        end=Position(
                                            line=line,
                                            character=len(keyword.value),
                                        ),
                                    ),
                                    message=(
                                        f"Invalid value '{keyword.value}' for "
                                        f"{kw_name} in ${group_name}. "
                                        f"Allowed: {', '.join(allowed_values)}"
                                    ),
                                    severity=DiagnosticSeverity.Error,
                                    source=_DIAGNOSTIC_SOURCE,
                                    code="INVALID_VALUE",
                                )
                            )

    @staticmethod
    def _sort_diagnostics(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
        """Sort diagnostics deterministically for stable output.

        Order: line (asc), severity (error < warning < info), message (asc).
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

_SEVERITY_MAP = {
    DiagnosticSeverity.Error: "error",
    DiagnosticSeverity.Warning: "warning",
    DiagnosticSeverity.Information: "information",
    DiagnosticSeverity.Hint: "hint",
}


def _diagnostic_to_dict(diag: Diagnostic) -> dict[str, Any]:
    """Convert a ``Diagnostic`` to a JSON-friendly dict."""
    severity = (
        _SEVERITY_MAP.get(
            diag.severity,
            "information",
        )
        if diag.severity
        else "information"
    )

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
        "source": diag.source or _DIAGNOSTIC_SOURCE,
        "code": str(diag.code) if diag.code is not None else None,
        "message": diag.message,
    }


__all__ = ["DiagnosticProvider"]
