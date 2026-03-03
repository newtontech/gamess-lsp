"""GAMESS LSP Diagnostics implementation."""

import re
from typing import Dict, List, Optional, Set, Tuple

from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from .groups import (
    GAMESS_GROUPS,
    get_group_documentation,
    get_parameter_documentation,
)
from .parser import GamessParser, ParseError
from .data_parser import DataGroupParser


class GamessDiagnostics:
    """Provides diagnostics for GAMESS input files."""
    
    def __init__(self):
        self.parser = GamessParser()
        self.data_parser = DataGroupParser()
    
    def validate(self, content: str) -> List[Diagnostic]:
        """Validate GAMESS input file and return diagnostics.
        
        Args:
            content: The input file content
            
        Returns:
            List of Diagnostic objects
        """
        diagnostics: List[Diagnostic] = []
        
        # Skip validation for empty or whitespace-only content
        if not content or not content.strip():
            return diagnostics
            
        lines = content.split('\n')
        
        # Step 1: Parse and get basic errors
        groups, parse_errors = self.parser.parse(content)
        for error in parse_errors:
            severity = DiagnosticSeverity.Error if error.severity == "error" else DiagnosticSeverity.Warning
            diagnostics.append(self._create_diagnostic(
                error.line - 1, error.column,
                error.line - 1, error.column + 10,
                error.message, severity
            ))
        
        # Step 2: Validate groups
        for group in groups:
            group_diagnostics = self._validate_group(group, lines)
            diagnostics.extend(group_diagnostics)
        
        # Step 3: Validate required groups
        required_diagnostics = self._validate_required_groups(groups, lines)
        diagnostics.extend(required_diagnostics)
        
        # Step 4: Validate $DATA group coordinates
        data_diagnostics = self._validate_data_group(lines, groups)
        diagnostics.extend(data_diagnostics)
        
        # Step 5: Validate parameter types and values
        type_diagnostics = self._validate_parameter_types(groups, lines)
        diagnostics.extend(type_diagnostics)
        
        return diagnostics
    
    def _validate_group(self, group, lines: List[str]) -> List[Diagnostic]:
        """Validate a single group."""
        diagnostics = []
        group_doc = get_group_documentation(group.name)
        
        if not group_doc:
            # Unknown group - already reported in parse errors
            return diagnostics
        
        # Validate parameters
        for param in group.parameters:
            param_doc = get_parameter_documentation(group.name, param.name)
            
            if not param_doc:
                # Unknown parameter
                diagnostics.append(self._create_diagnostic(
                    param.line - 1, param.column,
                    param.line - 1, param.column + len(param.name),
                    f"Unknown parameter '{param.name}' in ${group.name}",
                    DiagnosticSeverity.Warning
                ))
            else:
                # Validate parameter value
                value_diagnostic = self._validate_parameter_value(
                    param, param_doc, group.name
                )
                if value_diagnostic:
                    diagnostics.append(value_diagnostic)
        
        return diagnostics
    
    def _validate_required_groups(self, groups, lines: List[str]) -> List[Diagnostic]:
        """Validate that required groups are present."""
        diagnostics = []
        
        group_names = {g.name.upper() for g in groups}
        
        for group_name, group_doc in GAMESS_GROUPS.items():
            if group_doc.required and group_name not in group_names:
                diagnostics.append(self._create_diagnostic(
                    0, 0, 0, 0,
                    f"Required group ${group_name} is missing",
                    DiagnosticSeverity.Error
                ))
        
        return diagnostics
    
    def _validate_data_group(self, lines: List[str], groups) -> List[Diagnostic]:
        """Validate $DATA group coordinates."""
        diagnostics = []
        
        for group in groups:
            if group.name == "DATA":
                data_info = self.data_parser.parse_data_group(
                    lines, group.start_line, group.end_line
                )
                
                if data_info:
                    # Validate atoms
                    atom_errors = self.data_parser.validate_atoms(data_info.atoms)
                    for error_msg, line_num in atom_errors:
                        # Find column position
                        line = lines[line_num - 1] if line_num - 1 < len(lines) else ""
                        col = len(line) - len(line.lstrip())
                        
                        diagnostics.append(self._create_diagnostic(
                            line_num - 1, col,
                            line_num - 1, len(line),
                            error_msg,
                            DiagnosticSeverity.Warning
                        ))
                    
                    # Report data parser errors
                    for error_msg, line_num in self.data_parser.errors:
                        line = lines[line_num - 1] if line_num - 1 < len(lines) else ""
                        col = len(line) - len(line.lstrip())
                        
                        diagnostics.append(self._create_diagnostic(
                            line_num - 1, col,
                            line_num - 1, len(line),
                            error_msg,
                            DiagnosticSeverity.Error
                        ))
                
                break  # Only process first $DATA group
        
        return diagnostics
    
    def _validate_parameter_types(self, groups, lines: List[str]) -> List[Diagnostic]:
        """Validate parameter value types."""
        diagnostics = []
        
        for group in groups:
            for param in group.parameters:
                param_doc = get_parameter_documentation(group.name, param.name)
                if param_doc:
                    type_diagnostic = self._validate_parameter_value(
                        param, param_doc, group.name
                    )
                    if type_diagnostic:
                        diagnostics.append(type_diagnostic)
        
        return diagnostics
    
    def _validate_parameter_value(
        self, param, param_doc, group_name: str
    ) -> Optional[Diagnostic]:
        """Validate a single parameter value."""
        value = param.value
        param_type = param_doc.type
        
        # Find value position in line (approximate)
        value_start = param.column + len(param.name) + 1  # +1 for '='
        
        # Check valid values first
        if param_doc.valid_values:
            value_upper = value.upper()
            valid_values_upper = [v.upper() for v in param_doc.valid_values]
            
            # For logicals, accept both .TRUE./.FALSE. and T/F
            if param_type == "logical":
                if value_upper not in valid_values_upper and \
                   value_upper not in ['.T.', '.F.', 'T', 'F', 'TRUE', 'FALSE']:
                    return self._create_diagnostic(
                        param.line - 1, value_start,
                        param.line - 1, value_start + len(value),
                        f"Invalid value '{value}' for {param.name}. "
                        f"Valid values: {', '.join(param_doc.valid_values)}",
                        DiagnosticSeverity.Error
                    )
            else:
                if value_upper not in valid_values_upper:
                    # Check if it's a prefix match (for completion purposes)
                    matching = [v for v in valid_values_upper if v.startswith(value_upper)]
                    if not matching:
                        return self._create_diagnostic(
                            param.line - 1, value_start,
                            param.line - 1, value_start + len(value),
                            f"Invalid value '{value}' for {param.name}. "
                            f"Valid values: {', '.join(param_doc.valid_values)}",
                            DiagnosticSeverity.Error
                        )
        
        # Validate by type
        if param_type == "integer":
            if not self._is_valid_integer(value):
                return self._create_diagnostic(
                    param.line - 1, value_start,
                    param.line - 1, value_start + len(value),
                    f"{param.name} requires an integer value",
                    DiagnosticSeverity.Error
                )
        
        elif param_type == "real":
            if not self._is_valid_real(value):
                return self._create_diagnostic(
                    param.line - 1, value_start,
                    param.line - 1, value_start + len(value),
                    f"{param.name} requires a real number value",
                    DiagnosticSeverity.Error
                )
        
        elif param_type == "logical":
            if not self._is_valid_logical(value):
                return self._create_diagnostic(
                    param.line - 1, value_start,
                    param.line - 1, value_start + len(value),
                    f"{param.name} requires a logical value (.TRUE. or .FALSE.)",
                    DiagnosticSeverity.Error
                )
        
        return None
    
    def _is_valid_integer(self, value: str) -> bool:
        """Check if value is a valid integer."""
        try:
            int(value)
            return True
        except ValueError:
            return False
    
    def _is_valid_real(self, value: str) -> bool:
        """Check if value is a valid real number."""
        try:
            float(value)
            return True
        except ValueError:
            # Check for scientific notation with 'D' (FORTRAN style)
            if 'D' in value.upper():
                try:
                    float(value.upper().replace('D', 'E'))
                    return True
                except ValueError:
                    return False
            return False
    
    def _is_valid_logical(self, value: str) -> bool:
        """Check if value is a valid logical."""
        valid = ['.TRUE.', '.FALSE.', '.T.', '.F.', 'T', 'F', 'TRUE', 'FALSE']
        return value.upper() in valid
    
    def _create_diagnostic(
        self, start_line: int, start_char: int,
        end_line: int, end_char: int,
        message: str, severity: DiagnosticSeverity
    ) -> Diagnostic:
        """Create a Diagnostic object."""
        return Diagnostic(
            range=Range(
                start=Position(line=start_line, character=start_char),
                end=Position(line=end_line, character=end_char)
            ),
            message=message,
            severity=severity,
            source="gamess-lsp"
        )
    
    def get_quick_fixes(self, diagnostic: Diagnostic, line: str) -> List[Tuple[str, str]]:
        """Get quick fix suggestions for a diagnostic.
        
        Returns:
            List of (fix_description, replacement_text) tuples
        """
        fixes = []
        message = diagnostic.message
        
        # Suggest fixes for invalid values
        if "Invalid value" in message and "Valid values:" in message:
            # Extract valid values from message
            import re
            match = re.search(r"Valid values: ([^$]+)$", message)
            if match:
                valid_values = [v.strip() for v in match.group(1).split(',')]
                for value in valid_values[:3]:  # Suggest top 3
                    fixes.append((f"Change to {value}", value))
        
        # Suggest fix for missing $END
        if "Unclosed group" in message:
            fixes.append(("Add $END", line + "\n$END"))
        
        return fixes
