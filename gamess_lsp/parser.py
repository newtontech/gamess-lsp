"""GAMESS input file parser."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class GroupParameter:
    """Represents a parameter within a $GROUP."""
    name: str
    value: str
    line: int
    column: int


@dataclass
class Group:
    """Represents a $GROUP in GAMESS input."""
    name: str
    parameters: List[GroupParameter]
    start_line: int
    end_line: int


@dataclass
class ParseError:
    """Represents a parsing error."""
    message: str
    line: int
    column: int
    severity: str = "error"


class GamessParser:
    """Parser for GAMESS input files."""
    
    # All valid $GROUP names in GAMESS
    VALID_GROUPS = {
        "CONTRL", "BASIS", "DATA", "SYSTEM", "SCF", "DFT", "MP2", "CC",
        "CIS", "TDHF", "TDDFT", "EOM", "GF", "PROP", "FORCE", "HESS",
        "IRC", "DRC", "STATPT", "TRUDGE", "TRANST", "SURF", "LOCH",
        "ELMOM", "ELPOT", "ELDENS", "ELFLDG", "POINTS", "GRID", "PDC",
        "MOLGRF", "PLTORB", "MOS", "AIMPAC", "RHFPROP", "ONEEL", "WFN",
        "SCRF", "COSMO", "PCM", "SMD", "ISOTOPES", "MASS", "INTGRL",
        "COORD", "LOCAL", "QUANPO", "CUBE", "SVIB", "RAMAN", "VSCF",
        "FMOPRP", "FMOXYZ", "FMOBND", "FMOLMO", "FMOFRG", "OPTMIZ",
        "GUESS", "VEC", "POP", "MIX", "DAMP", "DIIS", "SOSCF", "DIRSCF",
        "MICCG", "NEO", "NMR", "EPR", "MOSYM", "DCC", "CRYS", "EFP",
        "FRAGNAME", "FRGRPL", "EFPOT", "ELG", "LMOEDA", "BSSE", "MCCI",
        "FSOCI", "CISGRD", "IVO", "ORMAS", "GENCI", "CIM", "VB", "LOCIST",
        "CISVEC", "HEFF", "RXNCRD", "MCP", "NR", "EFIELD", "MM", "PRTURB",
        "COSGMS", "DIEPTS", "DYN", "MEX", "STEP", "GEO", "GRAD", "BRANCH",
        "NUMGRD", "VIB", "VIB2", "VSCF", "MULT", "RDM", "RS", "SAC", "SET",
        "TCE", "MRPT", "SEW", "SHELL", "SOLVNT", "STEP", "STO", "TRUNCN",
        "UNIQUE", "VIBANL", "WFN", "XYZ", "ZMAT"
    }
    
    def __init__(self):
        self.errors: List[ParseError] = []
        self.groups: List[Group] = []
    
    def parse(self, content: str) -> Tuple[List[Group], List[ParseError]]:
        """Parse GAMESS input file content.
        
        Args:
            content: The input file content
            
        Returns:
            Tuple of (groups, errors)
        """
        self.errors = []
        self.groups = []
        
        lines = content.split('\n')
        current_group: Optional[Group] = None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('!'):
                continue
            
            # Check for group start
            if stripped.startswith('$'):
                # Check if this is the end of a group
                if stripped.upper() == '$END':
                    if current_group:
                        current_group.end_line = line_num
                        self.groups.append(current_group)
                        current_group = None
                    else:
                        self.errors.append(ParseError(
                            message="$END without matching $GROUP start",
                            line=line_num,
                            column=line.index('$'),
                            severity="error"
                        ))
                    continue
                
                # New group start
                group_name = self._extract_group_name(stripped)
                if group_name:
                    # Validate group name
                    if group_name.upper() not in self.VALID_GROUPS:
                        self.errors.append(ParseError(
                            message=f"Unknown group: ${group_name}",
                            line=line_num,
                            column=line.index('$'),
                            severity="warning"
                        ))
                    
                    # If we were already in a group, close it
                    if current_group:
                        current_group.end_line = line_num - 1
                        self.groups.append(current_group)
                    
                    current_group = Group(
                        name=group_name.upper(),
                        parameters=[],
                        start_line=line_num,
                        end_line=line_num
                    )
                    
                    # Parse parameters on same line
                    params = self._parse_parameters(stripped, line_num)
                    if current_group:
                        current_group.parameters.extend(params)
                else:
                    self.errors.append(ParseError(
                        message="Invalid group name",
                        line=line_num,
                        column=line.index('$'),
                        severity="error"
                    ))
            
            # Parse parameters if inside a group
            elif current_group and '=' in stripped:
                params = self._parse_parameters(stripped, line_num)
                current_group.parameters.extend(params)
        
        # Check for unclosed group
        if current_group:
            self.errors.append(ParseError(
                message=f"Unclosed group: ${current_group.name}",
                line=current_group.start_line,
                column=0,
                severity="error"
            ))
            current_group.end_line = len(lines)
            self.groups.append(current_group)
        
        return self.groups, self.errors
    
    def _extract_group_name(self, line: str) -> Optional[str]:
        """Extract group name from a line starting with $."""
        match = re.match(r'\$([A-Za-z][A-Za-z0-9_]*)', line)
        return match.group(1) if match else None
    
    def _parse_parameters(self, line: str, line_num: int) -> List[GroupParameter]:
        """Parse parameters from a line."""
        params = []
        
        # Remove leading $GROUPNAME if present
        if line.strip().startswith('$'):
            line = re.sub(r'^\$[A-Za-z][A-Za-z0-9_]*\s*', '', line.strip())
        
        # Split by spaces, but handle quoted values
        # Pattern: KEY=VALUE or KEY="VALUE" or KEY='VALUE'
        param_pattern = r'([A-Za-z][A-Za-z0-9_]*)\s*=\s*("[^"]*"|\'[^\']*\'|[^\s]+)'
        
        for match in re.finditer(param_pattern, line):
            key = match.group(1)
            value = match.group(2)
            
            # Remove quotes from value
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            params.append(GroupParameter(
                name=key.upper(),
                value=value,
                line=line_num,
                column=match.start()
            ))
        
        return params
    
    def get_group_at_position(self, line: int, column: int) -> Optional[Group]:
        """Get the group at a specific position."""
        for group in self.groups:
            if group.start_line <= line <= group.end_line:
                return group
        return None
    
    def get_parameter_at_position(self, line: int, column: int) -> Optional[GroupParameter]:
        """Get the parameter at a specific position."""
        for group in self.groups:
            for param in group.parameters:
                if param.line == line:
                    # Check if column is within parameter name
                    if param.column <= column <= param.column + len(param.name):
                        return param
        return None
