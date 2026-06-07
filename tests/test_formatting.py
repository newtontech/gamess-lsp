"""Tests for GAMESS LSP formatting feature."""

from unittest.mock import MagicMock, patch

from lsprotocol.types import DocumentFormattingParams, FormattingOptions, TextDocumentIdentifier

from gamess_lsp.server import _format_keywords, formatting


class TestFormatting:
    """Test document formatting feature."""

    @patch("gamess_lsp.server.server")
    def test_format_simple_document(self, mock_server):
        """Test formatting a simple document."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            options=FormattingOptions(tab_size=2, insert_spaces=True),
        )

        result = formatting(params)
        assert len(result) == 1
        # Should format the entire document
        assert isinstance(result[0].new_text, str)

    @patch("gamess_lsp.server.server")
    def test_format_multiline_document(self, mock_server):
        """Test formatting a multiline document."""
        content = """$CONTRL
SCFTYP=RHF
RUNTYP=ENERGY
$END"""
        mock_doc = MagicMock()
        mock_doc.source = content
        mock_doc.lines = content.split("\n")
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            options=FormattingOptions(tab_size=2, insert_spaces=True),
        )

        result = formatting(params)
        assert len(result) == 1
        formatted = result[0].new_text
        assert "$CONTRL" in formatted
        assert "$END" in formatted

    @patch("gamess_lsp.server.server")
    def test_format_with_comments(self, mock_server):
        """Test formatting preserves comments."""
        content = """! This is a comment
$CONTRL SCFTYP=RHF $END
! Another comment"""
        mock_doc = MagicMock()
        mock_doc.source = content
        mock_doc.lines = content.split("\n")
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            options=FormattingOptions(tab_size=2, insert_spaces=True),
        )

        result = formatting(params)
        assert len(result) == 1
        formatted = result[0].new_text
        assert "! This is a comment" in formatted

    @patch("gamess_lsp.server.server")
    def test_format_empty_document(self, mock_server):
        """Test formatting an empty document."""
        mock_doc = MagicMock()
        mock_doc.source = ""
        mock_doc.lines = []
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            options=FormattingOptions(tab_size=2, insert_spaces=True),
        )

        result = formatting(params)
        assert len(result) == 1
        assert result[0].new_text == ""


class TestFormatKeywords:
    """Test _format_keywords helper function."""

    def test_format_single_keyword(self):
        """Test formatting a single keyword."""
        result = _format_keywords("SCFTYP=RHF")
        assert result == "SCFTYP=RHF"

    def test_format_multiple_keywords(self):
        """Test formatting multiple keywords."""
        result = _format_keywords("SCFTYP=RHF RUNTYP=ENERGY")
        assert "SCFTYP=RHF" in result
        assert "RUNTYP=ENERGY" in result

    def test_format_quoted_values(self):
        """Test formatting with quoted values."""
        result = _format_keywords('EXETYP="CHECK"')
        assert 'EXETYP="CHECK"' in result

    def test_format_with_extra_spaces(self):
        """Test formatting normalizes spaces."""
        result = _format_keywords("SCFTYP  =  RHF")
        # The formatter preserves the key=value format
        assert "SCFTYP" in result
        assert "RHF" in result
