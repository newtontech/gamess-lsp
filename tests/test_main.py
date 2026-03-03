"""Test __main__ module."""


def test_main_module_imports():
    """Test that __main__ can be imported without running."""
    # Just check the module structure without triggering main
    import gamess_lsp.__main__ as main_module
    assert hasattr(main_module, 'main')

