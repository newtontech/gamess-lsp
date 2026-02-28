# GAMESS Language Server

Language Server Protocol (LSP) implementation for GAMESS (US) quantum chemistry input files.

## Features

- **Syntax Highlighting**: Full support for GAMESS input file syntax
- **Auto-completion**: Group names ($CONTRL, $BASIS, etc.) and parameter suggestions
- **Validation**: Real-time error detection for invalid parameters
- **Documentation**: Hover information for groups and parameters
- **Snippets**: Common input templates

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

### Command Line

```bash
gamess-lsp --stdio
```

## Supported $Groups

- $CONTRL - Control options
- $BASIS - Basis set specification
- $DATA - Molecular geometry and basis set data
- $SYSTEM - System resources
- $SCF - SCF convergence options
- And more...

## Development

```bash
git clone https://github.com/newtontech/gamess-lsp.git
cd gamess-lsp
pip install -e ".[dev]"
pytest
```

## License

MIT
