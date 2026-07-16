"""
Basic tests for gamess-lsp
"""

from gamess_lsp import __version__


def test_import():
    """Test that the package can be imported."""
    assert __version__ == "0.1.1"


def test_version():
    """Test version is correct."""
    assert __version__ == "0.1.1"
