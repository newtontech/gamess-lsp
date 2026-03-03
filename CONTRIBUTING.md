# Contributing to GAMESS-LSP

Thank you for your interest in contributing to GAMESS-LSP! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository and clone it locally
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gamess_lsp

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v
```

## Code Style

We use several tools to maintain code quality:

```bash
# Format code with black
black gamess_lsp tests

# Lint with ruff
ruff check gamess_lsp tests

# Type check with mypy
mypy gamess_lsp
```

All code should:
- Follow PEP 8 style guidelines
- Include type hints where appropriate
- Have docstrings for public functions and classes
- Include tests for new features

## Adding New GAMESS Groups

To add documentation for a new GAMESS $GROUP:

1. Edit `gamess_lsp/groups.py`
2. Add a new `GroupDoc` entry to `GAMESS_GROUPS`
3. Include all relevant parameters with `ParameterDoc`
4. Add tests in `tests/test_groups.py`

Example:
```python
"NEWGROUP": GroupDoc(
    name="NEWGROUP",
    description="Description of the group",
    required=False,
    parameters={
        "PARAM1": ParameterDoc(
            name="PARAM1",
            description="Description of parameter",
            type="string",
            default="DEFAULT",
            valid_values=["VALUE1", "VALUE2"]
        ),
    }
)
```

## Adding Code Snippets

To add a new code snippet:

1. Edit `gamess_lsp/snippets.py`
2. Add a new entry to `GAMESS_SNIPPETS`

Example:
```python
"new_calculation": Snippet(
    prefix="newcalc",
    description="Description of calculation",
    body=[
        "$CONTRL SCFTYP=${1|RHF,UHF|} $END",
        "$DATA",
        "${2:Title}",
        "C1",
        "${3:C} 6.0 0.0 0.0 0.0",
        "$END"
    ]
)
```

## Pull Request Process

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make your changes and add tests

3. Ensure all tests pass:
   ```bash
   pytest
   ```

4. Check code style:
   ```bash
   black --check gamess_lsp tests
   ruff check gamess_lsp tests
   ```

5. Commit your changes with a clear message:
   ```bash
   git commit -m "feat: Add support for $NEWGROUP"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/my-feature
   ```

7. Create a Pull Request on GitHub

## Commit Message Guidelines

Use conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `style:` Code style changes (formatting)
- `chore:` Maintenance tasks

Examples:
```
feat: Add support for $PCM solvation group
fix: Correct parsing of inline $END
docs: Update README with new examples
test: Add edge case tests for parser
```

## Reporting Issues

When reporting issues, please include:

1. Python version
2. GAMESS-LSP version
3. A minimal example that reproduces the issue
4. Expected behavior
5. Actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
