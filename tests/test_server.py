"""Tests for GAMESS LSP server."""

import pytest
from unittest.mock import MagicMock, patch

from gamess_lsp.server import GamessLanguageServer, completions, hover


class TestServer:
    """Test cases for LSP server."""
    
    def test_server_creation(self):
        server = GamessLanguageServer("test", "v1.0")
        assert server.name == "test"
        assert server.version == "v1.0"
        assert server.parser is not None
        assert server.diagnostics is not None
    
    def test_server_documents_dict(self):
        server = GamessLanguageServer("test", "v1.0")
        assert isinstance(server.documents, dict)
        assert len(server.documents) == 0


class TestServerFeatures:
    """Test LSP feature integration."""
    
    @pytest.fixture
    def mock_server(self):
        server = MagicMock(spec=GamessLanguageServer)
        server.documents = {}
        return server
    
    def test_completions_empty_document(self, mock_server):
        params = MagicMock()
        params.text_document.uri = "file:///test.inp"
        params.position.line = 0
        params.position.character = 0
        
        result = completions(mock_server, params)
        assert result is None  # No document content
    
    def test_hover_empty_document(self, mock_server):
        params = MagicMock()
        params.text_document.uri = "file:///test.inp"
        params.position.line = 0
        params.position.character = 0
        
        result = hover(mock_server, params)
        assert result is None  # No document content
