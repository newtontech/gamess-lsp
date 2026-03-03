"""GAMESS input file parser."""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


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
    
    # All valid $GROUP names in GAMESS (expanded list)
    VALID_GROUPS = {
        # Core groups
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
        "NUMGRD", "VIB", "VIB2", "MULT", "RDM", "RS", "SAC", "SET",
        "TCE", "MRPT", "SEW", "SHELL", "SOLVNT", "STO", "TRUNCN",
        "UNIQUE", "VIBANL", "WFN", "XYZ", "ZMAT", "STO", "GHF", "SQRHF",
        "UKN", "UDFT", "RODFT", "MC", "CI", "GREEN", "CPHF", "CPM", 
        "RESP", "CARP", "MOM", "FIELD", "SPIN", "DEM", "DFTDIS",
        "PDEP", "EFSHG", "MOLDEN", "RIC", "P2", "DFTPCM", "PBE", "GEP",
        "MP4", "CCSDT", "T3", "EAP", "DCT", "TD", "DAT", "GLBL", "QMMM",
        "EXAM", "SUR", "DIEL", "HYB", "END", "ENC", "CIS2", "RISM",
        "RSOLV", "RXN", "PRD", "PRP", "DFT", "CP", "GBASIS", "TDDFT1",
        "TDDFT2", "SOCI", "BLUR", "AVIR", "AIND", "DIPM", "DIPOLE",
        "POLAR", "OPT", "PIMC", "FREE", "POTENTIAL", "FFIELD", "CCS",
        "CCT", "CCQ", "CC5", "CC6", "ACC", "G3", "G3B", "CBS", "W1",
        "EXTRAPOL", "BSIZ", "PL",
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
        
        if not content or not content.strip():
            return self.groups, self.errors
        
        lines = content.split('\n')
        current_group: Optional[Group] = None
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('!'):
                continue
            
            # Check for group start
            if stripped.startswith('$'):
                # Check if this is the end of a group
                if stripped.upper().startswith('$END'):
                    if current_group:
                        current_group.end_line = line_num
                        self.groups.append(current_group)
                        current_group = None
                    else:
                        self.errors.append(ParseError(
                            message="$END without matching $GROUP start",
                            line=line_num,
                            column=line.index('$') if '$' in line else 0,
                            severity="error"
                        ))
                    continue
                
                # New group start - check if inline $END on same line
                inline_end_match = re.search(r'\$END\s*$', stripped, re.IGNORECASE)
                
                if inline_end_match:
                    # Inline group: $GROUP params $END
                    group_name = self._extract_group_name(stripped)
                    if group_name:
                        # Validate group name
                        if group_name.upper() not in self.VALID_GROUPS:
                            self.errors.append(ParseError(
                                message=f"Unknown group: ${group_name}",
                                line=line_num,
                                column=line.index('$') if '$' in line else 0,
                                severity="warning"
                            ))
                        
                        # Close any previous unclosed group
                        if current_group:
                            current_group.end_line = line_num - 1
                            self.groups.append(current_group)
                            self.errors.append(ParseError(
                                message=f"Unclosed group: ${current_group.name} (missing $END)",
                                line=current_group.start_line,
                                column=0,
                                severity="error"
                            ))
                            current_group = None
                        
                        # Create inline group
                        group = Group(
                            name=group_name.upper(),
                            parameters=[],
                            start_line=line_num,
                            end_line=line_num
                        )
                        
                        # Parse parameters (excluding $END)
                        params_line = re.sub(r'\$END\s*$', '', stripped, flags=re.IGNORECASE)
                        params = self._parse_parameters(params_line, line_num)
                        group.parameters.extend(params)
                        self.groups.append(group)
                    continue
                
                # Multi-line group start
                group_name = self._extract_group_name(stripped)
                if group_name:
                    # Validate group name
                    if group_name.upper() not in self.VALID_GROUPS:
                        self.errors.append(ParseError(
                            message=f"Unknown group: ${group_name}",
                            line=line_num,
                            column=line.index('$') if '$' in line else 0,
                            severity="warning"
                        ))
                    
                    # If we were already in a group, close it (missing $END)
                    if current_group:
                        current_group.end_line = line_num - 1
                        self.groups.append(current_group)
                        self.errors.append(ParseError(
                            message=f"Unclosed group: ${current_group.name} (missing $END)",
                            line=current_group.start_line,
                            column=0,
                            severity="error"
                        ))
                    
                    current_group = Group(
                        name=group_name.upper(),
                        parameters=[],
                        start_line=line_num,
                        end_line=line_num
                    )
                    
                    # Parse parameters on same line (after group name)
                    params = self._parse_parameters(stripped, line_num)
                    if current_group:
                        current_group.parameters.extend(params)
                else:
                    self.errors.append(ParseError(
                        message="Invalid group name",
                        line=line_num,
                        column=line.index('$') if '$' in line else 0,
                        severity="error"
                    ))
            
            # Parse parameters if inside a group
            elif current_group and '=' in stripped:
                params = self._parse_parameters(stripped, line_num)
                current_group.parameters.extend(params)
        
        # Check for unclosed group at end of file
        if current_group:
            self.errors.append(ParseError(
                message=f"Unclosed group: ${current_group.name} (missing $END at end of file)",
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
        line_content = line
        if line.strip().startswith('$'):
            # Remove group name from the line
            line_content = re.sub(r'^\$[A-Za-z][A-Za-z0-9_]*\s*', '', line.strip())
        
        # Pattern: KEY=VALUE or KEY="VALUE" or KEY='VALUE'
        # KEY must start with a letter and can contain letters, numbers, and underscores
        param_pattern = r'([A-Za-z][A-Za-z0-9_]*)\s*=\s*("[^"]*"|\'[^\']*\'|[^\s]+)'
        
        for match in re.finditer(param_pattern, line_content):
            key = match.group(1)
            value = match.group(2)
            
            # Remove quotes from value
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # Calculate column position in original line
            if line.strip().startswith('$'):
                # Adjust column to account for the group name prefix that was removed
                prefix_match = re.match(r'^(\$[A-Za-z][A-Za-z0-9_]*\s*)', line.strip())
                prefix_len = len(prefix_match.group(1)) if prefix_match else 0
                column = prefix_len + match.start()
            else:
                column = match.start()
            
            params.append(GroupParameter(
                name=key.upper(),
                value=value,
                line=line_num,
                column=column
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
