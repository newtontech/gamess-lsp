# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- `VERSION` file and release metadata pointers in `lsp-capabilities.json` for
  OpenQC provenance gates (#92).
- **New Snippet Templates**: Added 4 new GAMESS calculation templates
  - Transition state search (SADPOINT optimization)
  - IRC calculation (Intrinsic Reaction Coordinate)
  - CCSD(T) calculation (Coupled Cluster with perturbative triples)
  - PCM solvation in water (Polarizable Continuum Model)

### Changed
- Enhanced snippet coverage for advanced GAMESS calculations
- CI now enstrict test failures (no longer masks failures)
- Dependency version constraints tightened for stability

## [Unreleased]

### Added
- `raw/assets/manifest.json` with checksums, stable IDs, and official source anchors (#84).
- `scripts/refresh_provenance_manifest.py` to regenerate the provenance manifest without hand-editing pages.
- Expanded `lsp-capabilities.json` `sourceProvenance` and `outputLogPatterns` for traceable diagnostics.
- `tests/test_provenance_manifest.py` for manifest/capabilities contract checks.

### Fixed
- `scripts/test.sh` uses `python3` via `PYTHON_BIN` so CI/local gates work on macOS without a `python` shim.

## [0.2.4] - 2026-03-05

### Fixed
- Added E203 to flake8 ignore list for black compatibility

## [0.2.3] - 2026-03-05

### Fixed
- Fixed black formatting (E203) in parser.py

## [0.2.2] - 2026-03-04

### Fixed
- Fixed E203 whitespace issue in parser.py
- Fixed mypy type error in server.py
- Removed unused imports in test_formatting.py

### Added
- Comprehensive test suite for document_symbol feature
- 4 new tests for document symbols

## [0.2.1] - 2026-03-04

### Fixed
- Fixed Python escape sequence warnings by converting snippet insertText to raw strings
- Fixed broken imports in test_formatting.py and test_document_symbol.py
- Updated coverage configuration files

## [0.2.0] - 2026-03-04

### Added
- **Go to Definition** (textDocument/definition): Navigate to group and keyword definitions
- **Find References** (textDocument/references): Find all occurrences of groups and keywords
- **Snippet Completions**: Quick-insert templates for common GAMESS calculations
  - Water molecule template
  - DFT geometry optimization template
  - Hartree-Fock single point template
  - MP2 calculation template
  - Frequency calculation template
  - TD-DFT excited states template
- **Workspace Symbols** (workspace/symbol): Search symbols across all open GAMESS files
- New test suites:
  - test_definition.py - Go to definition tests
  - test_references.py - Find references tests
  - test_snippets.py - Snippet completion tests
  - test_workspace_symbol.py - Workspace symbols tests

### Changed
- Updated README.md with new features documentation
- Enhanced completion provider to include snippet suggestions

### Fixed
- Fixed escape character issues in snippet templates

## [0.1.0] - 2026-03-02

### Added
- Initial LSP server implementation
- GAMESS input file parser
- Syntax validation with diagnostics
- Auto-completion for groups, keywords, and values
- Hover documentation for keywords and groups
- Document formatting with consistent indentation
- Document symbols for navigation
- Code actions for quick fixes:
  - Add missing \$END for unclosed groups
  - Suggest corrections for unknown groups
  - Add required keywords (e.g., RUNTYP for \$CONTRL)
- Rename support for groups and keywords
- Comprehensive test suite

### Supported Features
- Core GAMESS groups: CONTRL, SYSTEM, BASIS, DATA, SCF, DFT, etc.
- Keyword and value completion with context awareness
- Real-time diagnostics for syntax errors and warnings
- Document formatting with 2-space indentation

## [0.0.1] - 2026-03-01

### Added
- Initial project structure
- Basic GAMESS parser implementation
- Development and testing setup
