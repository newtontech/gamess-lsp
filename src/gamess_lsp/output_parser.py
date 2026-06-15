"""GAMESS output/log file parser for runtime diagnostics.

See also: wiki/synthesis/Diagnostics_Catalog.md

This module parses GAMESS output files (.log, .out) to extract runtime
diagnostics, warnings, and error information that can be used by the LSP
to provide feedback on calculation issues.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class OutputDiagnostic:
    """A diagnostic extracted from GAMESS output/log files."""

    code: str
    severity: str  # "error", "warning", "information"
    message: str
    line: int
    column: int = 0
    source: str = "gamess-output"
    category: str = "runtime"
    confidence: float = 1.0
    blocking: bool = False
    facts: dict[str, Any] = field(default_factory=dict)
    fix_hints: list[str] = field(default_factory=list)
    source_provenance: dict[str, Any] = field(default_factory=dict)


# Diagnostic codes for output/log parsing
CODE_SCF_CONVERGENCE_FAILURE = "GAMESS-OUT-001"
CODE_MEMORY_ERROR = "GAMESS-OUT-002"
CODE_LOW_MEMORY_WARNING = "GAMESS-OUT-003"
CODE_INPUT_WARNING = "GAMESS-OUT-004"
CODE_CALCULATION_SUCCESS = "GAMESS-OUT-005"


# Patterns for detecting issues in GAMESS output
_SCF_CONVERGENCE_RE = re.compile(
    r"ERROR:\s*SCF\s+DID\s+NOT\s+CONVERGE",
    re.IGNORECASE,
)

_MEMORY_ERROR_RE = re.compile(
    r"ERROR:\s*INSUFFICIENT\s+MEMORY\s+ALLOCATED",
    re.IGNORECASE,
)

_LOW_MEMORY_WARNING_RE = re.compile(
    r"WARNING:\s*MWORDS=\d+\s+MAY\s+BE\s+INSUFFICIENT",
    re.IGNORECASE,
)

_INPUT_WARNING_RE = re.compile(
    r"WARNING:.*",
    re.IGNORECASE,
)

_CALCULATION_SUCCESS_RE = re.compile(
    r"JOB\s+COMPLETED\s+SUCCESSFULLY",
    re.IGNORECASE,
)

_ENERGY_RE = re.compile(
    r"(?:FINAL\s+ENERGY|CURRENT\s+ENERGY):\s*([-\d.]+)\s+HARTREES",
    re.IGNORECASE,
)

_MWORDS_RE = re.compile(
    r"MWORDS=(\d+)",
    re.IGNORECASE,
)

_ITERATIONS_RE = re.compile(
    r"SCF\s+CONVERGENCE\s+ACHIEVED\s+IN\s+(\d+)\s+ITERATIONS",
    re.IGNORECASE,
)


def parse_output_file(path: Path) -> list[OutputDiagnostic]:
    """Parse a GAMESS output/log file and extract diagnostics.

    Args:
        path: Path to the GAMESS output/log file.

    Returns:
        List of OutputDiagnostic objects extracted from the file.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    diagnostics: list[OutputDiagnostic] = []
    lines = text.splitlines()

    for line_no, line in enumerate(lines):
        # Check for SCF convergence failure
        if _SCF_CONVERGENCE_RE.search(line):
            facts = _extract_convergence_facts(lines, line_no)
            diagnostics.append(
                OutputDiagnostic(
                    code=CODE_SCF_CONVERGENCE_FAILURE,
                    severity="error",
                    message="SCF did not converge within the allowed number of iterations",
                    line=line_no + 1,
                    blocking=True,
                    facts=facts,
                    fix_hints=[
                        "Try a different initial guess (MOREAD)",
                        "Check molecular geometry for unreasonable values",
                        "Consider using a different SCF method (UHF or ROHF)",
                    ],
                    source_provenance={
                        "type": "output-log",
                        "pattern": "SCF_CONVERGENCE_FAILURE",
                    },
                )
            )

        # Check for memory errors
        if _MEMORY_ERROR_RE.search(line):
            facts = _extract_memory_facts(lines, line_no)
            diagnostics.append(
                OutputDiagnostic(
                    code=CODE_MEMORY_ERROR,
                    severity="error",
                    message="Insufficient memory allocated for calculation",
                    line=line_no + 1,
                    blocking=True,
                    facts=facts,
                    fix_hints=[
                        f"Increase MWORDS in $SYSTEM to at least "
                        f"{facts.get('required_mwords', 250)}",
                        "Consider using a smaller basis set",
                        "Use symmetry to reduce memory requirements",
                    ],
                    source_provenance={
                        "type": "output-log",
                        "pattern": "MEMORY_ERROR",
                    },
                )
            )

        # Check for low memory warnings
        if _LOW_MEMORY_WARNING_RE.search(line):
            mwords_match = _MWORDS_RE.search(line)
            mwords = int(mwords_match.group(1)) if mwords_match else 0
            diagnostics.append(
                OutputDiagnostic(
                    code=CODE_LOW_MEMORY_WARNING,
                    severity="warning",
                    message=f"MWORDS={mwords} may be insufficient for this calculation",
                    line=line_no + 1,
                    blocking=False,
                    facts={"mwords": mwords},
                    fix_hints=[
                        "Consider increasing MWORDS for better performance",
                        "Monitor memory usage during calculation",
                    ],
                    source_provenance={
                        "type": "output-log",
                        "pattern": "LOW_MEMORY_WARNING",
                    },
                )
            )

        # Check for general warnings
        if _INPUT_WARNING_RE.search(line) and "MWORDS" not in line:
            diagnostics.append(
                OutputDiagnostic(
                    code=CODE_INPUT_WARNING,
                    severity="warning",
                    message=line.strip(),
                    line=line_no + 1,
                    blocking=False,
                    source_provenance={
                        "type": "output-log",
                        "pattern": "INPUT_WARNING",
                    },
                )
            )

        # Check for successful calculation
        if _CALCULATION_SUCCESS_RE.search(line):
            facts = _extract_success_facts(lines, line_no)
            diagnostics.append(
                OutputDiagnostic(
                    code=CODE_CALCULATION_SUCCESS,
                    severity="information",
                    message="Calculation completed successfully",
                    line=line_no + 1,
                    blocking=False,
                    facts=facts,
                    source_provenance={
                        "type": "output-log",
                        "pattern": "CALCULATION_SUCCESS",
                    },
                )
            )

    return diagnostics


def _extract_convergence_facts(lines: list[str], error_line: int) -> dict[str, Any]:
    """Extract facts about convergence failure from surrounding lines."""
    facts: dict[str, Any] = {}

    # Look backwards for energy information
    for i in range(error_line, max(0, error_line - 20), -1):
        energy_match = _ENERGY_RE.search(lines[i])
        if energy_match:
            facts["final_energy"] = float(energy_match.group(1))
            break

    # Look for iteration count
    for i in range(max(0, error_line - 50), error_line):
        iter_match = _ITERATIONS_RE.search(lines[i])
        if iter_match:
            facts["iterations"] = int(iter_match.group(1))
            break

    return facts


def _extract_memory_facts(lines: list[str], error_line: int) -> dict[str, Any]:
    """Extract facts about memory error from surrounding lines."""
    facts: dict[str, Any] = {}

    # Look for memory numbers in nearby lines
    for i in range(error_line, min(len(lines), error_line + 10)):
        line = lines[i]

        # Look for required memory
        required_match = re.search(r"REQUIRED:\s*([\d,]+)\s+WORDS", line)
        if required_match:
            required = int(required_match.group(1).replace(",", ""))
            facts["required_words"] = required
            facts["required_mwords"] = required // 1_000_000

        # Look for requested memory
        requested_match = re.search(r"REQUESTED:\s*([\d,]+)\s+WORDS", line)
        if requested_match:
            facts["requested_words"] = int(requested_match.group(1).replace(",", ""))

    return facts


def _extract_success_facts(lines: list[str], success_line: int) -> dict[str, Any]:
    """Extract facts about successful calculation from surrounding lines."""
    facts: dict[str, Any] = {}

    # Look for energy
    for i in range(max(0, success_line - 20), success_line):
        energy_match = _ENERGY_RE.search(lines[i])
        if energy_match:
            facts["final_energy"] = float(energy_match.group(1))
            break

    # Look for iteration count
    for i in range(max(0, success_line - 50), success_line):
        iter_match = _ITERATIONS_RE.search(lines[i])
        if iter_match:
            facts["iterations"] = int(iter_match.group(1))
            break

    # Look for execution time
    time_match = re.search(r"EXECUTION\s+TIME:\s*([\d.]+)\s+SECONDS", lines[success_line])
    if time_match:
        facts["execution_time_seconds"] = float(time_match.group(1))

    return facts


def diagnostic_to_dict(diagnostic: OutputDiagnostic) -> dict[str, Any]:
    """Convert an OutputDiagnostic to a dictionary."""
    return {
        "code": diagnostic.code,
        "severity": diagnostic.severity,
        "message": diagnostic.message,
        "line": diagnostic.line,
        "column": diagnostic.column,
        "source": diagnostic.source,
        "category": diagnostic.category,
        "confidence": diagnostic.confidence,
        "blocking": diagnostic.blocking,
        "facts": diagnostic.facts,
        "fix_hints": diagnostic.fix_hints,
        "source_provenance": diagnostic.source_provenance,
        "range": {
            "start": {"line": diagnostic.line - 1, "character": diagnostic.column},
            "end": {"line": diagnostic.line - 1, "character": diagnostic.column + 1},
        },
    }
