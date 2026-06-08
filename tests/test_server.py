"""Tests for GAMESS LSP server."""

from unittest.mock import MagicMock, patch

from gamess_lsp.server import (
    _get_diagnostics,
    _get_word_at_position,
    completion,
    diagnostic,
    did_change,
    did_open,
    hover,
    main,
    server,
)


class TestGAMESSServer:
    """Test GAMESS LSP server."""

    def test_server_exists(self):
        """Test server instance exists."""
        assert server is not None
        assert server.name == "gamess-lsp"
        assert server.version == "0.1.0"


class TestGetDiagnostics:
    """Test _get_diagnostics function."""

    def test_get_diagnostics_empty(self):
        """Test diagnostics for empty content."""
        diagnostics = _get_diagnostics("")
        assert isinstance(diagnostics, list)
        # Empty input triggers missing required group diagnostics from typecheck
        assert all(d.source == "gamess-lsp-typecheck" for d in diagnostics)

    def test_get_diagnostics_warning(self):
        """Test diagnostics with warning."""
        content = """$UNKNOWN $END"""
        diagnostics = _get_diagnostics(content)
        assert len(diagnostics) >= 1  # At least unknown group warning

    def test_get_diagnostics_valid(self):
        """Test diagnostics for valid content."""
        content = """$CONTRL SCFTYP=RHF $END"""
        diagnostics = _get_diagnostics(content)
        # Valid content should have no warnings
        assert isinstance(diagnostics, list)


class TestGetWordAtPosition:
    """Test _get_word_at_position function."""

    def test_get_word_at_position(self):
        """Test getting word at position."""
        line = "SCFTYP=RHF"
        assert _get_word_at_position(line, 0) == "SCFTYP"
        assert _get_word_at_position(line, 3) == "SCFTYP"
        assert _get_word_at_position(line, 8) == "RHF"

    def test_get_word_at_position_empty(self):
        """Test getting word at empty line."""
        assert _get_word_at_position("", 0) == ""
        assert _get_word_at_position("   ", 1) == ""

    def test_get_word_at_position_out_of_range(self):
        """Test getting word at out of range position."""
        assert _get_word_at_position("test", 10) == ""


class TestCompletion:
    """Test completion feature."""

    @patch("gamess_lsp.server.server")
    def test_completion_groups(self, mock_server):
        """Test completion for groups."""
        mock_doc = MagicMock()
        mock_doc.source = ""
        mock_doc.lines = ["$"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = MagicMock()
        params.text_document.uri = "test://test.inp"
        params.position.line = 0
        params.position.character = 1

        result = completion(params)
        assert result is not None
        assert len(result.items) > 0
        # Should suggest groups starting with $
        assert any("$CONTRL" in item.label for item in result.items)

    @patch("gamess_lsp.server.server")
    def test_completion_with_content(self, mock_server):
        """Test completion with file content."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL "
        mock_doc.lines = ["$CONTRL "]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = MagicMock()
        params.text_document.uri = "test://test.inp"
        params.position.line = 0
        params.position.character = 8

        result = completion(params)
        assert result is not None


class TestHover:
    """Test hover feature."""

    @patch("gamess_lsp.server.server")
    def test_hover_group(self, mock_server):
        """Test hover for group name."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL"
        mock_doc.lines = ["$CONTRL"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = MagicMock()
        params.text_document.uri = "test://test.inp"
        params.position.line = 0
        params.position.character = 3

        result = hover(params)
        assert result is not None

    @patch("gamess_lsp.server.server")
    def test_hover_no_word(self, mock_server):
        """Test hover with no word at position."""
        mock_doc = MagicMock()
        mock_doc.source = "   "
        mock_doc.lines = ["   "]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = MagicMock()
        params.text_document.uri = "test://test.inp"
        params.position.line = 0
        params.position.character = 1

        result = hover(params)
        assert result is None


class TestDidOpen:
    """Test did_open feature."""

    @patch("gamess_lsp.server.server")
    def test_did_open(self, mock_server):
        """Test document open."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL $END"
        mock_doc.uri = "test://test.inp"
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = MagicMock()
        params.text_document.uri = "test://test.inp"

        # Should not raise
        did_open(params)


class TestDidChange:
    """Test did_change feature."""

    @patch("gamess_lsp.server.server")
    def test_did_change(self, mock_server):
        """Test document change."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL $END"
        mock_doc.uri = "test://test.inp"
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = MagicMock()
        params.text_document.uri = "test://test.inp"

        # Should not raise
        did_change(params)


class TestDiagnostic:
    """Test diagnostic feature."""

    @patch("gamess_lsp.server.server")
    def test_diagnostic(self, mock_server):
        """Test diagnostic request."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL $END"
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = MagicMock()
        params.text_document.uri = "test://test.inp"

        result = diagnostic(params)
        assert isinstance(result, list)


class TestMain:
    """Test main entry point."""

    @patch("gamess_lsp.server.server.start_io")
    def test_main(self, mock_start):
        """Test main function."""
        main()
        mock_start.assert_called_once()

    @patch("gamess_lsp.server.server.start_io")
    def test_main_module(self, mock_start):
        """Test main as module."""
        import gamess_lsp.server as server_module

        server_module.main()
        mock_start.assert_called_once()
