"""GAMESS $DATA group coordinate parser."""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Atom:
    """Represents an atom in the molecule."""
    symbol: str
    atomic_number: float
    x: float
    y: float
    z: float
    line: int


@dataclass
class DataGroupInfo:
    """Information parsed from $DATA group."""
    title: str
    symmetry: str
    atoms: List[Atom]
    start_line: int
    end_line: int


class DataGroupParser:
    """Parser for GAMESS $DATA group containing molecular geometry."""
    
    # Common atom symbols and their atomic numbers
    ATOMIC_NUMBERS = {
        'H': 1, 'HE': 2, 'LI': 3, 'BE': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
        'F': 9, 'NE': 10, 'NA': 11, 'MG': 12, 'AL': 13, 'SI': 14, 'P': 15,
        'S': 16, 'CL': 17, 'AR': 18, 'K': 19, 'CA': 20, 'SC': 21, 'TI': 22,
        'V': 23, 'CR': 24, 'MN': 25, 'FE': 26, 'CO': 27, 'NI': 28, 'CU': 29,
        'ZN': 30, 'GA': 31, 'GE': 32, 'AS': 33, 'SE': 34, 'BR': 35, 'KR': 36,
        'RB': 37, 'SR': 38, 'Y': 39, 'ZR': 40, 'NB': 41, 'MO': 42, 'TC': 43,
        'RU': 44, 'RH': 45, 'PD': 46, 'AG': 47, 'CD': 48, 'IN': 49, 'SN': 50,
        'SB': 51, 'TE': 52, 'I': 53, 'XE': 54, 'CS': 55, 'BA': 56, 'LA': 57,
        'CE': 58, 'PR': 59, 'ND': 60, 'PM': 61, 'SM': 62, 'EU': 63, 'GD': 64,
        'TB': 65, 'DY': 66, 'HO': 67, 'ER': 68, 'TM': 69, 'YB': 70, 'LU': 71,
        'HF': 72, 'TA': 73, 'W': 74, 'RE': 75, 'OS': 76, 'IR': 77, 'PT': 78,
        'AU': 79, 'HG': 80, 'TL': 81, 'PB': 82, 'BI': 83, 'PO': 84, 'AT': 85,
        'RN': 86, 'FR': 87, 'RA': 88, 'AC': 89, 'TH': 90, 'PA': 91, 'U': 92,
        'NP': 93, 'PU': 94, 'AM': 95, 'CM': 96, 'BK': 97, 'CF': 98, 'ES': 99,
        'FM': 100, 'MD': 101, 'NO': 102, 'LR': 103, 'RF': 104, 'DB': 105,
        'SG': 106, 'BH': 107, 'HS': 108, 'MT': 109, 'DS': 110, 'RG': 111,
        'CN': 112, 'NH': 113, 'FL': 114, 'MC': 115, 'LV': 116, 'TS': 117,
        'OG': 118
    }
    
    # Common symmetry groups
    VALID_SYMMETRY_GROUPS = {
        'C1', 'CS', 'CI', 'CN', 'S2', 'S4', 'S6', 'S8', 'SN', 'CNV', 'CNH', 
        'DN', 'DNV', 'DNH', 'T', 'TH', 'TD', 'O', 'OH', 'I', 'IH',
        'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C2V', 'C3V', 'C4V', 
        'C2H', 'C3H', 'C4H', 'D2', 'D3', 'D4', 'D5', 'D6', 'D2D', 'D3D', 
        'D2H', 'D3H', 'D4H', 'D5H', 'D6H',
    }
    
    def __init__(self):
        self.errors: List[Tuple[str, int]] = []
    
    def parse_data_group(self, lines: List[str], start_line: int, end_line: int) -> Optional[DataGroupInfo]:
        """Parse $DATA group content.
        
        Args:
            lines: All lines from the input file
            start_line: Line number where $DATA starts (1-indexed)
            end_line: Line number where $END ends (1-indexed)
            
        Returns:
            DataGroupInfo if parsing successful, None otherwise
        """
        self.errors = []
        
        if start_line >= end_line - 1:
            self.errors.append(("Empty $DATA group", start_line))
            return None
        
        # Get $DATA content (excluding $DATA and $END lines)
        data_lines = lines[start_line:end_line - 1]
        
        if len(data_lines) < 2:
            self.errors.append(("$DATA group must have at least title and symmetry line", start_line))
            return None
        
        # First line: title
        title = data_lines[0].strip()
        
        # Second line: symmetry group and (optionally) symmetry order
        symmetry_line = data_lines[1].strip()
        symmetry_parts = symmetry_line.split()
        symmetry = symmetry_parts[0] if symmetry_parts else "C1"
        
        # Validate symmetry group
        symmetry_upper = symmetry.upper()
        # Direct match check first
        if symmetry_upper in self.VALID_SYMMETRY_GROUPS:
            pass  # Valid
        else:
            # Check if it matches a pattern like C1, C2, C3v, D2h, etc.
            pattern_match = re.match(r'^(C|S|D|T|O|I)(\d+)', symmetry_upper)
            if pattern_match:
                base = pattern_match.group(1)
                n = pattern_match.group(2)
                # Construct base pattern (e.g., C2 -> CN, C2v -> CNV)
                if 'V' in symmetry_upper:
                    base_pattern = base + 'NV'
                elif 'H' in symmetry_upper:
                    base_pattern = base + 'NH'
                elif 'D' in symmetry_upper and base != 'D':
                    base_pattern = base + 'ND'
                else:
                    base_pattern = base + 'N' if n else base
                
                if base_pattern not in self.VALID_SYMMETRY_GROUPS and base not in self.VALID_SYMMETRY_GROUPS:
                    self.errors.append((f"Unknown symmetry group: {symmetry}", start_line + 1))
            elif symmetry_upper not in self.VALID_SYMMETRY_GROUPS:
                # Truly unknown group
                self.errors.append((f"Unknown symmetry group: {symmetry}", start_line + 1))
        
        # Parse atoms (skip empty lines)
        atoms: List[Atom] = []
        for i, line in enumerate(data_lines[2:], start=start_line + 2):
            stripped = line.strip()
            if not stripped or stripped.startswith('!'):
                continue
            
            atom = self._parse_atom_line(stripped, i + 1)
            if atom:
                atoms.append(atom)
            else:
                self.errors.append((f"Invalid atom line format: {line}", i + 1))
        
        return DataGroupInfo(
            title=title,
            symmetry=symmetry,
            atoms=atoms,
            start_line=start_line,
            end_line=end_line
        )
    
    def _parse_atom_line(self, line: str, line_num: int) -> Optional[Atom]:
        """Parse a single atom line.
        
        Format: SYMBOL ATOMIC_NUMBER X Y Z
        or:     SYMBOL X Y Z (atomic number inferred from symbol)
        """
        parts = line.split()
        
        if len(parts) < 4:
            return None
        
        try:
            symbol = parts[0].upper()
            
            # Check if second field is atomic number (integer/float > 10) or coordinate (< 10)
            try:
                val2 = float(parts[1])
                # Heuristic: if 2nd value is > 10, it's likely atomic number
                # otherwise it's likely the first coordinate
                if val2 > 10 or val2 == int(val2) and val2 > 0 and len(parts) >= 5:
                    # Format: SYMBOL ATOMIC_NUMBER X Y Z
                    atomic_number = val2
                    x = float(parts[2])
                    y = float(parts[3])
                    z = float(parts[4]) if len(parts) > 4 else 0.0
                else:
                    # Format: SYMBOL X Y Z
                    atomic_number = self.ATOMIC_NUMBERS.get(symbol, 0.0)
                    x = val2
                    y = float(parts[2])
                    z = float(parts[3])
            except (ValueError, IndexError):
                return None
            
            return Atom(
                symbol=symbol,
                atomic_number=atomic_number,
                x=x,
                y=y,
                z=z,
                line=line_num
            )
        except (ValueError, IndexError):
            return None
    
    def validate_atoms(self, atoms: List[Atom]) -> List[Tuple[str, int]]:
        """Validate atom data.
        
        Returns:
            List of (error_message, line_number) tuples
        """
        errors = []
        
        # Note: GAMESS allows duplicate atom symbols in many coordinate modes
        # (e.g., unique coordinates mode where each atom is unique by position)
        # We only flag true errors, not style warnings
        
        for atom in atoms:
            
            # Check atomic number matches symbol
            expected_z = self.ATOMIC_NUMBERS.get(atom.symbol)
            if expected_z and abs(atom.atomic_number - expected_z) > 0.1:
                errors.append((
                    f"Atomic number mismatch for {atom.symbol}: "
                    f"expected {expected_z}, got {atom.atomic_number}",
                    atom.line
                ))
            
            # Check for reasonable coordinate values
            if abs(atom.x) > 1000 or abs(atom.y) > 1000 or abs(atom.z) > 1000:
                errors.append((f"Unusually large coordinate values for {atom.symbol}", atom.line))
        
        return errors
    
    def get_molecular_formula(self, atoms: List[Atom]) -> str:
        """Generate molecular formula from atoms."""
        from collections import Counter
        
        counts = Counter(atom.symbol for atom in atoms)
        
        # Sort by: C first, H second, then alphabetically
        def sort_key(item):
            symbol = item[0]
            if symbol == 'C':
                return (0, symbol)
            elif symbol == 'H':
                return (1, symbol)
            else:
                return (2, symbol)
        
        parts = []
        for symbol, count in sorted(counts.items(), key=sort_key):
            if count == 1:
                parts.append(symbol)
            else:
                parts.append(f"{symbol}{count}")
        
        return "".join(parts)
    
    def calculate_center_of_mass(self, atoms: List[Atom]) -> Tuple[float, float, float]:
        """Calculate center of mass for the molecule."""
        total_mass = 0.0
        com_x = com_y = com_z = 0.0
        
        for atom in atoms:
            mass = self._get_atomic_mass(atom.symbol)
            total_mass += mass
            com_x += mass * atom.x
            com_y += mass * atom.y
            com_z += mass * atom.z
        
        if total_mass == 0:
            return (0.0, 0.0, 0.0)
        
        return (com_x / total_mass, com_y / total_mass, com_z / total_mass)
    
    def _get_atomic_mass(self, symbol: str) -> float:
        """Get approximate atomic mass for an element."""
        # Simplified atomic masses (most common isotope)
        masses = {
            'H': 1.008, 'HE': 4.003, 'LI': 6.941, 'BE': 9.012, 'B': 10.81,
            'C': 12.01, 'N': 14.01, 'O': 16.00, 'F': 19.00, 'NE': 20.18,
            'NA': 22.99, 'MG': 24.31, 'AL': 26.98, 'SI': 28.09, 'P': 30.97,
            'S': 32.07, 'CL': 35.45, 'AR': 39.95, 'K': 39.10, 'CA': 40.08,
            'SC': 44.96, 'TI': 47.87, 'V': 50.94, 'CR': 52.00, 'MN': 54.94,
            'FE': 55.85, 'CO': 58.93, 'NI': 58.69, 'CU': 63.55, 'ZN': 65.38,
            'GA': 69.72, 'GE': 72.63, 'AS': 74.92, 'SE': 78.96, 'BR': 79.90,
            'KR': 83.80
        }
        return masses.get(symbol.upper(), 20.0)  # Default mass if unknown
