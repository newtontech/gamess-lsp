#!/usr/bin/env python3
"""CLI entry point for gamess-lsp."""

import argparse
import sys
from gamess_lsp.server import server


def main():
    parser = argparse.ArgumentParser(
        description="GAMESS Language Server Protocol implementation"
    )
    parser.add_argument(
        "--version", 
        action="version", 
        version="%(prog)s 0.1.0"
    )
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Use stdio for communication (required by LSP clients)"
    )
    
    args = parser.parse_args()
    
    if args.stdio:
        server.start_io()
    else:
        print("GAMESS Language Server v0.1.0")
        print("Use --stdio flag when running from LSP client")
        sys.exit(1)


if __name__ == "__main__":
    main()
