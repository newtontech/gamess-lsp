#!/usr/bin/env python3
"""CLI entry point for gamess-lsp."""

import argparse
import json
import sys
from pathlib import Path

from gamess_lsp.server import server
from gamess_lsp.parser import GamessParser
from gamess_lsp.diagnostics import GamessDiagnostics
from gamess_lsp import __version__


def validate_file(filepath: str, json_output: bool = False) -> int:
    """Validate a GAMESS input file.
    
    Args:
        filepath: Path to the input file
        json_output: Output results as JSON
        
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return 1
    
    try:
        content = path.read_text()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1
    
    # Parse
    parser = GamessParser()
    groups, parse_errors = parser.parse(content)
    
    # Validate
    diagnostics = GamessDiagnostics()
    diag_results = diagnostics.validate(content)
    
    errors = [e for e in parse_errors if e.severity == "error"]
    warnings = [e for e in parse_errors if e.severity == "warning"]
    diag_errors = [d for d in diag_results if d.severity.value == 1]
    diag_warnings = [d for d in diag_results if d.severity.value == 2]
    
    if json_output:
        result = {
            "valid": len(errors) == 0 and len(diag_errors) == 0,
            "groups_found": len(groups),
            "parse_errors": [
                {"message": e.message, "line": e.line, "column": e.column, "severity": e.severity}
                for e in parse_errors
            ],
            "diagnostics": [
                {"message": d.message, "line": d.range.start.line + 1, "severity": d.severity.value}
                for d in diag_results
            ]
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"File: {filepath}")
        print(f"Groups found: {len(groups)}")
        
        if groups:
            print("\nGroups:")
            for group in groups:
                params = f" ({len(group.parameters)} parameters)" if group.parameters else ""
                print(f"  ${group.name}{params}")
        
        if parse_errors or diag_results:
            print()
        
        if errors:
            print(f"Parse Errors ({len(errors)}):")
            for error in errors:
                print(f"  Line {error.line}: {error.message}")
        
        if warnings:
            print(f"Parse Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"  Line {warning.line}: {warning.message}")
        
        if diag_errors:
            print(f"Validation Errors ({len(diag_errors)}):")
            for diag in diag_errors:
                print(f"  Line {diag.range.start.line + 1}: {diag.message}")
        
        if diag_warnings:
            print(f"Validation Warnings ({len(diag_warnings)}):")
            for diag in diag_warnings:
                print(f"  Line {diag.range.start.line + 1}: {diag.message}")
        
        if not errors and not warnings and not diag_errors and not diag_warnings:
            print("\n✓ No issues found")
        
        print()
    
    return 1 if (errors or diag_errors) else 0


def parse_file(filepath: str, json_output: bool = False) -> int:
    """Parse a GAMESS input file and show structure.
    
    Args:
        filepath: Path to the input file
        json_output: Output results as JSON
        
    Returns:
        Exit code
    """
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return 1
    
    try:
        content = path.read_text()
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1
    
    parser = GamessParser()
    groups, errors = parser.parse(content)
    
    if json_output:
        result = {
            "groups": [
                {
                    "name": group.name,
                    "start_line": group.start_line,
                    "end_line": group.end_line,
                    "parameters": [
                        {"name": p.name, "value": p.value, "line": p.line}
                        for p in group.parameters
                    ]
                }
                for group in groups
            ],
            "errors": [
                {"message": e.message, "line": e.line, "column": e.column, "severity": e.severity}
                for e in errors
            ]
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"File: {filepath}")
        print(f"Groups: {len(groups)}")
        print()
        
        for group in groups:
            print(f"${group.name} (lines {group.start_line}-{group.end_line})")
            for param in group.parameters:
                print(f"  {param.name} = {param.value}")
            print()
        
        if errors:
            print(f"Errors ({len(errors)}):")
            for error in errors:
                print(f"  Line {error.line}: {error.message}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="GAMESS Language Server Protocol implementation",
        prog="gamess-lsp"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command (default)
    server_parser = subparsers.add_parser(
        "server",
        help="Start the LSP server (default)"
    )
    server_parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio for communication (required by LSP clients)"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a GAMESS input file"
    )
    validate_parser.add_argument(
        "file",
        help="Path to the input file"
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    # Parse command
    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse a GAMESS input file and show structure"
    )
    parse_parser.add_argument(
        "file",
        help="Path to the input file"
    )
    parse_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    if args.command == "server" or args.command is None:
        if args.command == "server" and args.stdio:
            server.start_io()
        elif args.command is None:
            # Check for legacy --stdio flag
            if "--stdio" in sys.argv:
                server.start_io()
            else:
                parser.print_help()
                sys.exit(1)
        else:
            server.start_io()
    elif args.command == "validate":
        sys.exit(validate_file(args.file, args.json))
    elif args.command == "parse":
        sys.exit(parse_file(args.file, args.json))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
