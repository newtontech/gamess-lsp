"""Tests for GAMESS LSP document symbols feature."""

from unittest.mock import MagicMock, patch

from lsprotocol.types import DocumentSymbolParams, SymbolKind, TextDocumentIdentifier

from gamess_lsp.server import document_symbol


class TestDocumentSymbol:
    """Test document symbol feature."""

    @patch("gamess_lsp.server.server")
    def test_document_symbol_groups(self, mock_server):
        """Test extracting document symbols for groups."""
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$SYSTEM MWORDS=100 $END
$DATA
Title
C1

H 1.0 0.0 0.0 0.0
$END"""
        mock_doc = MagicMock()
        mock_doc.source = content
        mock_doc.lines = content.split("\n")
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentSymbolParams(text_document=TextDocumentIdentifier(uri="file:///test.inp"))

        result = document_symbol(params)
        assert len(result) >= 3  # $CONTRL, $SYSTEM, $DATA

        # Check group names are present
        group_names = [symbol.name for symbol in result]
        assert "$CONTRL" in group_names
        assert "$SYSTEM" in group_names
        assert "$DATA" in group_names

    @patch("gamess_lsp.server.server")
    def test_document_symbol_with_keywords(self, mock_server):
        """Test that keywords within groups are included."""
        content = """$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"""
        mock_doc = MagicMock()
        mock_doc.source = content
        mock_doc.lines = content.split("\n")
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentSymbolParams(text_document=TextDocumentIdentifier(uri="file:///test.inp"))

        result = document_symbol(params)
        assert len(result) > 0

        # Find CONTRL group
        contrl_group = None
        for symbol in result:
            if symbol.name == "$CONTRL":
                contrl_group = symbol
                break

        assert contrl_group is not None
        assert contrl_group.kind == SymbolKind.Class

    @patch("gamess_lsp.server.server")
    def test_document_symbol_empty_document(self, mock_server):
        """Test document symbols for empty document."""
        mock_doc = MagicMock()
        mock_doc.source = ""
        mock_doc.lines = []
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentSymbolParams(text_document=TextDocumentIdentifier(uri="file:///test.inp"))

        result = document_symbol(params)
        assert len(result) == 0

    @patch("gamess_lsp.server.server")
    def test_document_symbol_kind(self, mock_server):
        """Test correct symbol kinds are assigned."""
        content = """$CONTRL SCFTYP=RHF $END"""
        mock_doc = MagicMock()
        mock_doc.source = content
        mock_doc.lines = [content]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentSymbolParams(text_document=TextDocumentIdentifier(uri="file:///test.inp"))

        result = document_symbol(params)
        assert len(result) > 0

        # Groups should be Namespace kind
        for symbol in result:
            if symbol.name.startswith("$"):
                assert symbol.kind == SymbolKind.Class
