"""GAMESS input file parser."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .constants import ELEMENT_ATOMIC_NUMBERS


@dataclass
class GAMESSKeyword:
    """Represents a GAMESS keyword-value pair."""

    name: str
    value: str
    line_number: int


@dataclass
class GAMESSGroup:
    """Represents a GAMESS $ group."""

    name: str
    keywords: Dict[str, GAMESSKeyword] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0

    def add_keyword(self, keyword: GAMESSKeyword) -> None:
        """Add a keyword to this group."""
        self.keywords[keyword.name.upper()] = keyword

    def get_keyword(self, name: str) -> Optional[GAMESSKeyword]:
        """Get a keyword by name (case-insensitive)."""
        return self.keywords.get(name.upper())


@dataclass
class GAMESSInputFile:
    """Represents a parsed GAMESS input file."""

    groups: Dict[str, GAMESSGroup] = field(default_factory=dict)
    title: str = ""
    geometry: List[Dict[str, Any]] = field(default_factory=list)

    def get_group(self, name: str) -> Optional[GAMESSGroup]:
        """Get a group by name (case-insensitive)."""
        return self.groups.get(name.upper())

    def add_group(self, group: GAMESSGroup) -> None:
        """Add a group to the input file."""
        self.groups[group.name.upper()] = group


class GAMESSParser:
    """Parser for GAMESS input files."""

    # Known GAMESS groups
    KNOWN_GROUPS = {
        "CONTRL",
        "SYSTEM",
        "BASIS",
        "SCF",
        "DFT",
        "MP2",
        "CC",
        "CIS",
        "TDDFT",
        "MCSCF",
        "CI",
        "GREEN",
        "DRT",
        "GUESS",
        "STATPT",
        "TRUDGE",
        "FORCE",
        "HESSIAN",
        "VIB",
        "IRC",
        "DRC",
        "TAMC",
        "SURFACE",
        "MOROKM",
        "FFIELD",
        "EFRAG",
        "PCM",
        "COSM",
        "SMD",
        "EQUIL",
        "DECOMP",
        "MOLCAS",
        "CIM",
        "LOCAL",
        "PMO",
        "GEM",
        "ELMOM",
        "AIMPAC",
        "FRIEND",
        "NBO",
        "MAKVEC",
        "RAMAN",
        "INPUT",
        "PUNCH",
        "BENCH",
        "PARALLEL",
        "ACCURACY",
        "ECP",
        "RELWFN",
        "GUESS",
        "VEC",
        "DATA",
        "LIBRARY",
    }

    def __init__(self) -> None:
        """Initialize the parser."""
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def parse(self, content: str) -> GAMESSInputFile:
        """Parse GAMESS input file content.

        Args:
            content: The input file content.

        Returns:
            Parsed GAMESS input file.
        """
        self.errors = []
        self.warnings = []

        result = GAMESSInputFile()
        lines = content.split("\n")

        current_group: Optional[GAMESSGroup] = None
        in_data_group = False
        data_line_count = 0  # Track lines within $DATA for title/symmetry skip
        geometry_lines: List[Tuple[int, str]] = []

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("!"):
                continue

            # Check for group start/end
            if stripped.startswith("$"):
                # Check for $END first (case insensitive)
                if re.match(r"^\$END\b", stripped, re.IGNORECASE):
                    if current_group:
                        current_group.line_end = line_num
                        result.add_group(current_group)
                        if current_group.name == "DATA":
                            in_data_group = False
                            data_line_count = 0
                        current_group = None
                    continue

                # Check for group start
                group_match = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)", stripped)
                if group_match:
                    group_name = group_match.group(1).upper()

                    # New group - close current if exists
                    if current_group:
                        current_group.line_end = line_num - 1
                        result.add_group(current_group)

                    # Create new group
                    current_group = GAMESSGroup(name=group_name, line_start=line_num)

                    # Track if we're entering $DATA group
                    if group_name == "DATA":
                        in_data_group = True
                        data_line_count = 0

                    # Parse keywords in this line (after the group name)
                    rest_of_line = stripped[len(group_match.group(0)) :].strip()
                    if rest_of_line:
                        self._parse_keywords(rest_of_line, current_group, line_num)

                    # Warn if unknown group
                    if group_name not in self.KNOWN_GROUPS:
                        self.warnings.append(
                            {
                                "line": line_num,
                                "message": f"Unknown group: ${group_name}",
                                "severity": "warning",
                            }
                        )

                    continue

            # Parse keywords if inside a group (but not $DATA)
            if current_group:
                if current_group.name == "DATA":
                    # Inside $DATA group - parse geometry
                    # Skip title (line 1) and symmetry (line 2)
                    data_line_count += 1
                    if data_line_count > 2:
                        # This should be an atom line
                        geometry_lines.append((line_num, stripped))
                elif "=" in stripped:
                    self._parse_keywords(stripped, current_group, line_num)

        # Close any open group at end of file
        if current_group:
            current_group.line_end = len(lines)
            result.add_group(current_group)
            self.warnings.append(
                {
                    "line": current_group.line_start,
                    "message": f"Group ${current_group.name} not properly closed with $END",
                    "severity": "warning",
                }
            )

        # Parse geometry if present
        if geometry_lines:
            result.geometry = self._parse_geometry(geometry_lines)

        return result

    def _parse_keywords(self, line: str, group: GAMESSGroup, line_num: int) -> None:
        """Parse keyword-value pairs from a line."""
        # Split by spaces but handle quoted values
        tokens = self._tokenize(line)

        for token in tokens:
            if "=" in token:
                key_value = token.split("=", 1)
                if len(key_value) == 2:
                    key, value = key_value
                    keyword = GAMESSKeyword(
                        name=key.strip(), value=value.strip().strip("\"'"), line_number=line_num
                    )
                    group.add_keyword(keyword)

    def _tokenize(self, line: str) -> List[str]:
        """Tokenize a line into keyword=value pairs."""
        tokens = []
        current = ""
        in_quotes = False
        quote_char = None

        for char in line:
            if char in "\"'":
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current += char
            elif char == " " and not in_quotes:
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += char

        if current:
            tokens.append(current)

        return tokens

    def _parse_geometry(self, geometry_lines: List[Tuple[int, str]]) -> List[Dict[str, Any]]:
        """Parse geometry lines.

        Supports two formats:
        1. Standard GAMESS format: Symbol Z x y z
           Example: O 8.0 0.0 0.0 0.0
        2. Simplified format: Symbol x y z (Z inferred from symbol)
           Example: O 0.0 0.0 0.0
        """
        atoms = []

        for line_num, line in geometry_lines:
            # Strip comments
            if "!" in line:
                line = line[:line.index("!")].strip()

            parts = line.split()
            if len(parts) < 4:
                continue

            try:
                symbol = parts[0].capitalize()

                # Detect format: try to parse second field as number
                try:
                    val2 = float(parts[1])
                    # Standard format: Symbol Z x y z
                    z = val2
                    x = float(parts[2])
                    y = float(parts[3])
                    z_coord = float(parts[4]) if len(parts) > 4 else 0.0
                except ValueError:
                    # Simplified format: Symbol x y z (no Z)
                    z = ELEMENT_ATOMIC_NUMBERS.get(symbol, 0)
                    x = float(parts[1])
                    y = float(parts[2])
                    z_coord = float(parts[3]) if len(parts) > 3 else 0.0

                atom = {
                    "line": line_num,
                    "symbol": symbol,
                    "z": z,
                    "x": x,
                    "y": y,
                    "z_coord": z_coord,
                }
                atoms.append(atom)
            except (ValueError, IndexError):
                pass

        return atoms

    def get_diagnostics(self) -> List[Dict[str, Any]]:
        """Get parsing errors and warnings."""
        return self.errors + self.warnings

    def get_group_at_position(self, content: str, line: int) -> Optional[str]:
        """Get the group name at a specific line position."""
        lines = content.split("\n")
        current_group = None

        for i, text in enumerate(lines[:line], 1):
            stripped = text.strip()
            if stripped.startswith("$"):
                # Check for $END
                if re.match(r"^\$END\b", stripped, re.IGNORECASE):
                    current_group = None
                    continue

                # Check for group start
                match = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)", stripped)
                if match:
                    group_name = match.group(1).upper()
                    if group_name != "END":
                        current_group = group_name

        return current_group


def parse_gamess_input(content: str) -> GAMESSInputFile:
    """Convenience function to parse GAMESS input."""
    parser = GAMESSParser()
    return parser.parse(content)
