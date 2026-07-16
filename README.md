# GAMESS-LSP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

Language Server Protocol implementation for GAMESS (US) input files (.inp).

## Features

- **Syntax Validation**: Real-time validation of GAMESS input files with warnings for unknown groups and unclosed sections
- **Auto-completion**: Intelligent completion for \$ groups and keywords, including value suggestions after `=`
- **Snippet Completions**: Quick-insert templates for common GAMESS calculations (water molecule, DFT optimization, MP2, frequency, TD-DFT, etc.)
- **Hover Documentation**: Inline documentation for GAMESS keywords and groups
- **Diagnostics**: Warnings for unknown groups, unclosed sections, and syntax issues
- **Document Formatting**: Automatic formatting with consistent indentation
- **Document Symbols**: Navigation support for \$ groups and keywords
- **Go to Definition**: Navigate to group or keyword definitions
- **Find References**: Find all occurrences of groups or keywords
- **Workspace Symbols**: Search for symbols across all open GAMESS files
- **Code Actions**: Quick fixes for common issues:
  - Add missing \$END for unclosed groups
  - Suggest corrections for unknown groups
  - Add required keywords (e.g., RUNTYP for \$CONTRL)
- **Rename Support**: Rename groups and keywords across the document

## Installation

```bash
pip install gamess-lsp
```

### From Source

```bash
git clone https://github.com/newtontech/gamess-lsp.git
cd gamess-lsp
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
gamess-lsp
```

The server communicates via stdio using the LSP protocol.

## OpenQC Alignment

This repository is part of the newtontech computational chemistry LSP family. `newtontech/OpenQC-VSCode` is the VS Code-facing integration layer for this server.

When changing diagnostics, completions, snippets, hover text, file detection, or parser fixtures, also update or open an alignment issue in `OpenQC-VSCode` so the extension behavior stays consistent with `gamess-lsp`.

### Editor Integration

#### VS Code

Add to your `settings.json`:

```json
{
  "languageserver": {
    "gamess": {
      "command": "gamess-lsp",
      "filetypes": ["gamess"],
      "rootPatterns": ["*.inp"]
    }
  }
}
```

Or use with a VS Code extension that supports LSP.

#### Neovim (nvim-lspconfig)

```lua
local lspconfig = require('lspconfig')
lspconfig.gamess.setup {
  cmd = {"gamess-lsp"},
  filetypes = {"gamess"},
  root_dir = lspconfig.util.root_pattern("*.inp"),
}
```

#### Emacs (lsp-mode)

```elisp
(lsp-register-client
 (make-lsp-client :new-connection (lsp-stdio-connection "gamess-lsp")
                  :major-modes '(gamess-mode)
                  :server-id 'gamess-lsp))
```

## Example GAMESS Input File

```gamess
! Water molecule DFT calculation
 \$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE \$END
 \$SYSTEM MWORDS=100 \$END
 \$BASIS GBASIS=CC-PVDZ \$END
 \$STATPT OPTTOL=0.0001 NSTEP=50 \$END
 \$DATA
Water molecule
Cnv 2

O     8.0   0.000000   0.000000   0.117489
H     1.0   0.000000   0.757210  -0.469957
 \$END
```

## Features in Detail

### Completion

- Type `\$` to see all available groups
- Inside a group, type to see available keywords
- After `=`, see allowed values for the keyword
- Type at the start of a line to see snippet completions for common templates

### Snippet Templates

The following snippet templates are available (press Tab to navigate placeholders):

- **Water molecule**: Complete water molecule with DFT optimization
- **DFT optimization**: Standard DFT geometry optimization template
- **HF single point**: Hartree-Fock single point energy calculation
- **MP2 calculation**: MP2 correlation energy calculation
- **Frequency calculation**: Vibrational frequency calculation
- **TD-DFT**: Time-dependent DFT excited states calculation
- **Transition state search**: SADDLE point optimization for transition states
- **IRC calculation**: Intrinsic Reaction Coordinate path following
- **CCSD(T) calculation**: Coupled Cluster with perturbative triples
- **PCM solvation (water)**: DFT with PCM water solvation model

### Hover

Hover over any keyword or group name to see documentation:

```
SCFTYP
Type of SCF wavefunction.
Values: RHF, UHF, ROHF, MCSCF, NONE.
Default: RHF
```

### Go to Definition

- Click on a group name (e.g., `\$CONTRL`) to navigate to its definition
- Click on a keyword to navigate to where it's defined in the current group

### Find References

- Right-click on a group or keyword and select "Find All References"
- See all locations where the group or keyword is used in the document

### Workspace Symbols

- Search across all open GAMESS files for groups and keywords
- Use your editor's symbol search feature (Ctrl+Shift+O in VS Code)
- Filter by group or keyword names

### Diagnostics

Automatic warnings for:
- Unknown \$GROUPS
- Unclosed groups (missing \$END)
- Invalid keyword values (coming soon)

### Formatting

Automatic formatting with:
- Consistent 2-space indentation
- Standardized spacing around `=`
- Proper \$END placement

### Code Actions

Quick fixes available via your editor's code action menu:

1. **Add missing \$END**: When a group is not properly closed
2. **Change to \$GROUP**: Suggests similar group names when an unknown group is detected
3. **Add RUNTYP=ENERGY**: Adds required RUNTYP keyword to \$CONTRL group

### Rename

Rename symbols across the document:
- Select a group name and rename it
- Select a keyword and rename it
- All references are updated automatically

## Supported \$ Groups

### Core Groups
- `\$CONTRL` - Main control options (RUNTYP, SCFTYP, DFTTYP, etc.)
- `\$SYSTEM` - System settings (memory, time limits)
- `\$BASIS` - Basis set specification (GBASIS, NGAUSS, etc.)
- `\$DATA` - Molecular structure and geometry
- `\$GUESS` - Initial guess options

### Electronic Structure
- `\$SCF` - SCF options (DIIS, SOSCF, CONV)
- `\$DFT` - DFT options (functional, grid)
- `\$MP2` - Møller-Plesset perturbation theory
- `\$CC` - Coupled Cluster (CCSD, CCSD(T))
- `\$CIS` - Configuration Interaction Singles
- `\$TDDFT` - Time-Dependent DFT
- `\$MCSCF` - Multiconfigurational SCF
- `\$CI` - Configuration Interaction

### Geometry and Dynamics
- `\$STATPT` - Geometry optimization
- `\$FORCE` - Force calculations and frequencies
- `\$HESSIAN` - Hessian matrix
- `\$VIB` - Vibrational analysis
- `\$IRC` - Intrinsic Reaction Coordinate
- `\$DRC` - Dynamic Reaction Coordinate

### Solvation and Environment
- `\$PCM` - Polarizable Continuum Model
- `\$COSM` - COSMO solvation
- `\$SMD` - SMD solvation model
- `\$EFRAG` - Effective Fragment Potential
- `\$FFIELD` - Force Field options

### Advanced Options
- `\$ECP` - Effective Core Potentials
- `\$RELWFN` - Relativistic corrections
- `\$LOCAL` - Localized orbitals
- `\$NBO` - Natural Bond Orbital analysis

And many more...

## Development

### Setup

```bash
git clone https://github.com/newtontech/gamess-lsp.git
cd gamess-lsp
pip install -e ".[dev]"
```

### Testing

```bash
pytest tests/ -v
```

### Release verification

Releases are published from `v*` tag pushes by `.github/workflows/release.yml`.
The workflow checks that the tag, Python package, `VERSION`, and OpenQC
capability manifest agree, then builds the distributions and installs the wheel
into a new virtual environment. The isolated smoke verifies
`gamess-lsp --help`, installed version metadata, the agent JSON CLI, and valid,
invalid, and runtime-log fixtures before the OIDC-enabled `pypi` environment
can publish. No long-lived PyPI token is used.

GitHub Release finalization runs independently after the verified wheel smoke
and attaches that exact build artifact. A PyPI outage or trusted-publisher
misconfiguration can therefore fail PyPI without suppressing the native GitHub
Release; the finalizer also proves that the checkout and tag equal
`GITHUB_SHA` before creating the release.

Maintainers can exercise the same artifact smoke before creating a tag:

```bash
python -m pip install build
python -m build
python scripts/verify_release.py --tag v0.1.1
python scripts/smoke_test_wheel.py --wheel dist/gamess_lsp-0.1.1-py3-none-any.whl
```

### Code Quality

```bash
black src tests
isort src tests
flake8 src tests
mypy src
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.

## License

MIT License - see [LICENSE](LICENSE) for details.

## References

- [GAMESS (US) Documentation](https://www.msg.chem.iastate.edu/gamess/documentation.html)
- [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)
- [pygls - Python LSP Library](https://github.com/openlawlibrary/pygls)
