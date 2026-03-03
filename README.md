# GAMESS Language Server

Language Server Protocol (LSP) implementation for GAMESS (US) quantum chemistry input files.

## Features

### Core LSP Features
- **Syntax Validation**: Real-time parsing and error detection
- **Auto-completion**: 
  - $GROUP names when typing `$`
  - Parameter names within groups
  - Parameter values with valid options
  - Code snippets for common calculations
- **Hover Documentation**: 
  - Group descriptions and parameters
  - Parameter type, default values, and valid options
- **Document Symbols**: Outline view for navigating $GROUP sections
- **Folding Ranges**: Collapse $GROUP sections
- **Diagnostics**: 
  - Unknown group warnings
  - Missing $END detection
  - Parameter type validation
  - Required group checking

### Supported $GROUPs

#### Core Groups (Required)
- `$CONTRL` - Control options (SCFTYP, RUNTYP, MAXIT, MULT, etc.)
- `$DATA` - Molecular geometry and basis set data

#### Basis Set Groups
- `$BASIS` - Basis set specification (GBASIS, NGAUSS, NDFUNC, etc.)

#### SCF/Method Groups
- `$SCF` - SCF convergence options (CONV, DIIS, SOSCF, etc.)
- `$DFT` - Density Functional Theory options
- `$MP2` - MP2 perturbation theory options
- `$CC` - Coupled Cluster options
- `$CIS` - Configuration Interaction Singles
- `$EOM` - Equation of Motion coupled cluster

#### System/Resource Groups
- `$SYSTEM` - System resources and memory
- `$GUESS` - Initial guess options

#### Geometry/Optimization Groups
- `$STATPT` - Geometry optimization options
- `$FORCE` - Force constant calculation
- `$HESS` - Hessian matrix options

#### Solvation Groups
- `$PCM` - Polarizable Continuum Model
- `$COSMO` - Conductor-like Screening Model

#### Analysis Groups
- `$POP` - Population analysis
- `$ELMOM` - Electric moments
- `$ELPOT` - Electrostatic potential
- `$PDC` - Potential-derived charges
- `$LOCAL` - Localized orbitals
- `$VEC` - Molecular orbital manipulation

### Code Snippets
- `scf` - Single point SCF calculation
- `opt` - Geometry optimization
- `freq` - Frequency calculation
- `optfreq` - Optimization + Frequency
- `dft` - DFT calculation
- `mp2` - MP2 calculation
- `tddft` - Time-Dependent DFT
- `cis` - CIS/TDHF calculation
- `data` - $DATA group template
- `contrl` - $CONTRL group template

## Installation

```bash
pip install gamess-lsp
```

## Usage

### VS Code

Install the GAMESS extension (coming soon).

### Neovim

Using `lspconfig`:

```lua
require('lspconfig').gamess_lsp.setup{}
```

Or with custom configuration:

```lua
require('lspconfig').gamess_lsp.setup{
    cmd = {'gamess-lsp', '--stdio'},
    filetypes = {'gamess', 'inp'},
    root_dir = require('lspconfig').util.find_git_ancestor,
    settings = {},
}
```

### Command Line

```bash
gamess-lsp --stdio
```

## Example Input

```fortran
$CONTRL SCFTYP=RHF RUNTYP=ENERGY MAXIT=50 MULT=1 $END
$SYSTEM MEMORY=4000000 $END
$BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
$SCF CONV=1.0E-06 DIIS=.TRUE. $END
$DATA
Water molecule - RHF/6-31G(d)
Cnv 2

O  8.0   0.000000   0.000000   0.117790
H  1.0   0.000000   0.755453  -0.471161
H  1.0   0.000000  -0.755453  -0.471161
$END
$GUESS GUESS=HUCKEL $END
```

## Development

```bash
git clone https://github.com/newtontech/gamess-lsp.git
cd gamess-lsp
pip install -e ".[dev]"
pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gamess_lsp

# Run specific test file
pytest tests/test_parser.py
```

### Project Structure

```
gamess-lsp/
├── gamess_lsp/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point
│   ├── cli.py                # CLI interface
│   ├── parser.py             # GAMESS input file parser
│   ├── groups.py             # $GROUP documentation data
│   ├── data_parser.py        # $DATA group coordinate parser
│   ├── diagnostics.py        # LSP diagnostics provider
│   ├── server.py             # LSP server implementation
│   ├── document_symbols.py   # Document symbol provider
│   ├── folding.py            # Folding range provider
│   └── snippets.py           # Code snippets
├── tests/
│   ├── test_parser.py        # Parser tests
│   ├── test_groups.py        # Groups data tests
│   ├── test_data_parser.py   # Data parser tests
│   ├── test_diagnostics.py   # Diagnostics tests
│   ├── test_document_symbols.py  # Document symbol tests
│   ├── test_folding.py       # Folding tests
│   ├── test_snippets.py      # Snippets tests
│   └── test_server.py        # Server tests
├── setup.py                  # Package setup
├── README.md                 # This file
└── PLAN.md                   # Development plan
```

## Dependencies

- Python 3.8+
- `pygls>=1.1.0` - Python LSP framework
- `lsprotocol>=2023.0.0` - Language Server Protocol types

## License

MIT

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## Resources

- [GAMESS Documentation](https://www.msg.chem.iastate.edu/gamess/documentation.html)
- [GAMESS Input Manual](https://www.msg.chem.iastate.edu/gamess/GAMESS_Manual/input.doc.html)
- [Language Server Protocol Specification](https://microsoft.github.io/language-server-protocol/)
