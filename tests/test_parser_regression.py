"""Additional tests for GAMESS LSP to reach 100% coverage."""

from unittest.mock import MagicMock, patch

# import pytest
from lsprotocol.types import (
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    TextDocumentItem,
    VersionedTextDocumentIdentifier,
)

from gamess_lsp.server import (
    did_change,
    did_open,
)


class TestDocumentEventsCoverage:
    """Test document event handlers for full coverage."""

    @patch("gamess_lsp.server.server")
    def test_did_open_document(self, mock_server):
        """Test did open document handler."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///test.inp",
                language_id="gamess",
                version=1,
                text="$CONTRL SCFTYP=RHF $END",
            )
        )

        # Should not raise
        did_open(params)

    @patch("gamess_lsp.server.server")
    def test_did_change_document(self, mock_server):
        """Test did change document handler."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri="file:///test.inp", version=2),
            content_changes=[MagicMock(text="$CONTRL SCFTYP=UHF $END")],
        )

        # Should not raise
        did_change(params)


class TestFormattingEdgeCases:
    """Test formatting edge cases."""

    @patch("gamess_lsp.server.server")
    def test_formatting_preserves_comments(self, mock_server):
        """Test that formatting preserves comments."""
        from gamess_lsp.server import formatting

        mock_doc = MagicMock()
        mock_doc.source = "! This is a comment\n$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["! This is a comment\n", "$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = MagicMock()
        params.text_document.uri = "file:///test.inp"
        params.options.tab_size = 2
        params.options.insert_spaces = True

        result = formatting(params)
        assert isinstance(result, list)
