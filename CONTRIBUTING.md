# Contributing to GAMESS LSP

Thank you for your interest in contributing to GAMESS LSP!

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce the bug
- Example input file if applicable
- Expected vs actual behavior

### Adding New Groups/Parameters

GAMESS has many $GROUPs and parameters. To add documentation for new groups:

1. Edit `gamess_lsp/groups.py`
2. Add the group documentation to `GAMESS_GROUPS` dictionary
3. Include all relevant parameters with descriptions, types, defaults, and valid values

### Improving the Parser

The parser is in `gamess_lsp/parser.py`. When improving it:
- Add tests to `tests/test_parser.py`
- Ensure all existing tests pass
- Consider edge cases (malformed input, comments, etc.)

### Adding LSP Features

The LSP server is in `gamess_lsp/server.py`. To add features:
- Code completion: Edit the `completions` function
- Hover information: Edit the `hover` function
- Diagnostics: Add validation in the parser and report via LSP

## Development Setup

```bash
git clone https://github.com/newtontech/gamess-lsp.git
cd gamess-lsp
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Style

We use Black for formatting and flake8 for linting:

```bash
black gamess_lsp tests
flake8 gamess_lsp tests
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run tests and ensure they pass
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

Thank you for your contributions!
