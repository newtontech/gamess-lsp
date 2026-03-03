"""Tests for LSP server module."""
import pytest
from unittest.mock import MagicMock, patch

from lsprotocol.types import (
    CompletionParams,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    HoverParams,
    Position,
    TextDocumentIdentifier,
    TextDocumentItem,
    VersionedTextDocumentIdentifier,
    TextDocumentContentChangeEvent,
)

from gamess_lsp.server import (
    server,
    did_open,
    did_change,
    completions,
    hover,
    document_symbol,
    folding_range,
    _get_word_at_position,
    _format_group_hover,
    _format_param_doc,
    _format_param_hover,
)


class TestDidOpen:
    """Tests for did_open handler."""
    
    def test_did_open_valid_document(self):
        """Test opening a valid document."""
        ls = MagicMock()
        ls.documents = {}
        
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///test.inp",
                language_id="gamess",
                version=1,
                text="$CONTRL SCFTYP=RHF $END\n$DATA\nTest\nC1\nH 1.0 0.0 0.0 0.0\n$END"
            )
        )
        
        did_open(ls, params)
        
        assert "file:///test.inp" in ls.documents
        assert ls.publish_diagnostics.called
    
    def test_did_open_empty_document(self):
        """Test opening an empty document."""
        ls = MagicMock()
        ls.documents = {}
        
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///empty.inp",
                language_id="gamess",
                version=1,
                text=""
            )
        )
        
        did_open(ls, params)
        
        assert "file:///empty.inp" in ls.documents


class TestDidChange:
    """Tests for did_change handler."""
    
    def test_did_change_document(self):
        """Test changing a document."""
        ls = MagicMock()
        ls.documents = {"file:///test.inp": "old content"}
        
        # Create a mock content change event
        change_event = MagicMock()
        change_event.text = "$CONTRL SCFTYP=RHF $END"
        
        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(
                uri="file:///test.inp",
                version=2
            ),
            content_changes=[change_event]
        )
        
        did_change(ls, params)
        
        assert ls.documents["file:///test.inp"] == "$CONTRL SCFTYP=RHF $END"
        assert ls.publish_diagnostics.called


class TestCompletions:
    """Tests for completions handler."""
    
    def test_completions_group_suggestion(self):
        """Test completion for group names."""
        ls = MagicMock()
        ls.documents = {"file:///test.inp": ""}
        
        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1)
        )
        
        result = completions(ls, params)
        
        assert result is not None
        assert len(result.items) > 0
        # Should include snippets
        assert any(item.label == "scf" for item in result.items)
    
    def test_completions_dollar_sign(self):
        """Test completion after typing $."""
        ls = MagicMock()
        ls.documents = {"file:///test.inp": "$CON"}
        
        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=4)
        )
        
        result = completions(ls, params)
        
        # Should include $CONTRL completion
        assert result is not None
    
    def test_completions_no_document(self):
        """Test completion when document not open."""
        ls = MagicMock()
        ls.documents = {}
        
        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///missing.inp"),
            position=Position(line=0, character=0)
        )
        
        result = completions(ls, params)
        
        assert result is None
    
    def test_completions_position_out_of_range(self):
        """Test completion at invalid position."""
        ls = MagicMock()
        ls.documents = {"file:///test.inp": "short line"}
        
        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=100, character=0)
        )
        
        result = completions(ls, params)
        
        assert result is None


class TestHover:
    """Tests for hover handler."""
    
    def test_hover_group(self):
        """Test hover over a group name."""
        ls = MagicMock()
        ls.documents = {"file:///test.inp": "$CONTRL SCFTYP=RHF $END"}
        
        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=2)  # Over CONTRL
        )
        
        result = hover(ls, params)
        
        assert result is not None
        assert "CONTRL" in str(result.contents)
    
    def test_hover_no_document(self):
        """Test hover when document not open."""
        ls = MagicMock()
        ls.documents = {}
        
        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///missing.inp"),
            position=Position(line=0, character=0)
        )
        
        result = hover(ls, params)
        
        assert result is None
    
    def test_hover_no_word(self):
        """Test hover at position with no word."""
        ls = MagicMock()
        ls.documents = {"file:///test.inp": "   "}
        
        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1)
        )
        
        result = hover(ls, params)
        
        assert result is None


class TestDocumentSymbol:
    """Tests for document symbol handler."""
    
    def test_document_symbol_valid(self):
        """Test document symbols for valid input."""
        ls = MagicMock()
        ls.documents = {
            "file:///test.inp": "$CONTRL SCFTYP=RHF $END\n$DATA\nTest\nC1\nH 1.0 0.0 0.0 0.0\n$END"
        }
        
        params = MagicMock()
        params.text_document.uri = "file:///test.inp"
        
        result = document_symbol(ls, params)
        
        assert result is not None
    
    def test_document_symbol_no_document(self):
        """Test document symbols when document not open."""
        ls = MagicMock()
        ls.documents = {}
        
        params = MagicMock()
        params.text_document.uri = "file:///missing.inp"
        
        result = document_symbol(ls, params)
        
        assert result == []


class TestFoldingRange:
    """Tests for folding range handler."""
    
    def test_folding_range_valid(self):
        """Test folding ranges for valid input."""
        ls = MagicMock()
        ls.documents = {
            "file:///test.inp": "$CONTRL\n  SCFTYP=RHF\n$END"
        }
        
        params = MagicMock()
        params.text_document.uri = "file:///test.inp"
        
        result = folding_range(ls, params)
        
        assert result is not None
    
    def test_folding_range_no_document(self):
        """Test folding ranges when document not open."""
        ls = MagicMock()
        ls.documents = {}
        
        params = MagicMock()
        params.text_document.uri = "file:///missing.inp"
        
        result = folding_range(ls, params)
        
        assert result == []


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_get_word_at_position(self):
        """Test word extraction at position."""
        assert _get_word_at_position("$CONTRL", 2) == "$CONTRL"
        assert _get_word_at_position("SCFTYP=RHF", 2) == "SCFTYP"
        assert _get_word_at_position("   ", 1) is None
    
    def test_format_group_hover(self):
        """Test group hover formatting."""
        group_doc = MagicMock()
        group_doc.name = "CONTRL"
        group_doc.description = "Control group"
        group_doc.required = True
        group_doc.parameters = {}
        
        result = _format_group_hover(group_doc)
        
        assert "$CONTRL" in result
        assert "Control group" in result
        assert "Required" in result
    
    def test_format_param_doc(self):
        """Test parameter documentation formatting."""
        param_doc = MagicMock()
        param_doc.description = "SCF type"
        param_doc.type = "string"
        param_doc.default = "RHF"
        param_doc.valid_values = ["RHF", "UHF"]
        
        result = _format_param_doc(param_doc)
        
        assert "SCF type" in result
        assert "RHF" in result
    
    def test_format_param_hover(self):
        """Test parameter hover formatting."""
        param_doc = MagicMock()
        param_doc.name = "SCFTYP"
        param_doc.description = "SCF type"
        param_doc.type = "string"
        param_doc.default = "RHF"
        param_doc.valid_values = ["RHF", "UHF"]
        
        result = _format_param_hover(param_doc)
        
        assert "SCFTYP" in result
        assert "SCF type" in result
        assert "RHF" in result
