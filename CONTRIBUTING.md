# Contributing to GAMESS-LSP

Thank you for your interest in contributing to GAMESS-LSP! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Adding New Keywords](#adding-new-keywords)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/gamess-lsp.git
   cd gamess-lsp
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/my-new-feature
   ```

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Installation

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Set up pre-commit hooks (optional but recommended):
   ```bash
   pre-commit install
   ```

## Making Changes

### Project Structure

```
gamess-lsp/
├── src/gamess_lsp/
│   ├── __init__.py      # Package initialization
│   ├── parser.py        # GAMESS input file parser
│   ├── server.py        # LSP server implementation
│   └── keywords.py      # GAMESS keywords database
├── tests/
│   ├── conftest.py      # Pytest configuration
│   ├── test_parser.py   # Parser tests
│   ├── test_server.py   # Server tests
│   └── test_keywords.py # Keywords tests
├── pyproject.toml       # Project configuration
├── README.md            # Project documentation
├── CHANGELOG.md         # Version history
└── CONTRIBUTING.md      # This file
```

### Key Files

- **parser.py**: Contains the GAMESS input file parser
  - `GAMESSParser`: Main parser class
  - `GAMESSGroup`: Represents a $ group
  - `GAMESSKeyword`: Represents a keyword-value pair
  - `GAMESSInputFile`: Represents a parsed input file

- **server.py**: LSP server implementation
  - Completion, hover, diagnostics, formatting, symbols
  - Uses pygls library for LSP protocol

- **keywords.py**: GAMESS keywords database
  - `GAMESS_GROUPS`: Dictionary of group descriptions
  - `GAMESS_KEYWORDS`: Dictionary of keywords with documentation

## Testing

### Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=gamess_lsp --cov-report=term-missing
```

Run a specific test file:
```bash
pytest tests/test_parser.py -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Name test classes with `Test` prefix
- Name test functions with `test_` prefix
- Use descriptive test names that explain what is being tested

Example:
```python
class TestGAMESSParser:
    def test_parse_simple_group(self):
        """Test parsing a simple $CONTRL group."""
        content = "$CONTRL SCFTYP=RHF $END"
        parser = GAMESSParser()
        result = parser.parse(content)
        assert "CONTRL" in result.groups
```

## Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

Run all checks:
```bash
black src tests
isort src tests
flake8 src tests
mypy src
```

### Style Guidelines

- Maximum line length: 100 characters
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Follow PEP 8 style guidelines

## Submitting Changes

### Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the CHANGELOG.md with your changes
3. Add tests for any new features
4. Ensure all tests pass
5. Ensure code passes all style checks
6. Submit a pull request to the `main` branch

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new features

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Adding New Keywords

To add support for a new GAMESS keyword:

1. **Add to keywords.py**:
   ```python
   GAMESS_KEYWORDS["GROUP_NAME"] = {
       "KEYWORD_NAME": {
           "doc": """Description of the keyword.
   Values: VALUE1, VALUE2, VALUE3.
   Default: VALUE1""",
           "values": ["VALUE1", "VALUE2", "VALUE3"]
       }
   }
   ```

2. **Add tests in test_keywords.py**:
   ```python
   def test_new_keyword(self):
       """Test that NEW_KEYWORD exists."""
       assert "NEW_KEYWORD" in GAMESS_KEYWORDS["GROUP_NAME"]
   ```

3. **Update documentation** if the keyword is significant

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. Python version
2. GAMESS-LSP version
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Sample GAMESS input file (if applicable)

### Feature Requests

For feature requests, please include:

1. Description of the feature
2. Use case / motivation
3. Proposed implementation (optional)

## Questions?

If you have questions, feel free to:

- Open an issue on GitHub
- Start a discussion in the repository

Thank you for contributing to GAMESS-LSP!


<!-- repo-governance-kit:contributing-v1 -->

## Agent-Ready Issue and PR Contract

Agent-ready work must have a GitHub issue with a goal, acceptance criteria, required tests, and out-of-scope notes. Branches should use `agent/issue-<number>-<slug>`, and PR bodies must include `Fixes #<issue-number>`.

Before requesting review, run `make format`, `make lint`, `make typecheck`, `make test`, and `make check`. Code changes should include tests or an explicit no-test justification in the PR body.
