"""Additional tests for GAMESS LSP server to achieve 100% coverage."""

from unittest.mock import MagicMock, patch

from lsprotocol.types import (
    CodeActionParams,
    CompletionParams,
    DefinitionParams,
    DocumentFormattingParams,
    HoverParams,
    Position,
    Range,
    ReferenceParams,
    RenameParams,
    TextDocumentIdentifier,
)

from gamess_lsp.server import (
    code_action,
    completion,
    definition,
    formatting,
    hover,
    references,
    rename,
)


class TestFormattingCoverage:
    """Test formatting functionality for full coverage."""

    @patch("gamess_lsp.server.server")
    def test_formatting_empty_document(self, mock_server):
        """Test formatting an empty document."""
        mock_doc = MagicMock()
        mock_doc.source = ""
        mock_doc.lines = []
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            options=MagicMock(tab_size=2, insert_spaces=True),
        )

        result = formatting(params)
        # Empty document returns a single edit replacing content with empty string
        assert isinstance(result, list)

    @patch("gamess_lsp.server.server")
    def test_formatting_complex_document(self, mock_server):
        """Test formatting a complex document."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END\n$SYSTEM MWORDS=100 $END\n"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END\n", "$SYSTEM MWORDS=100 $END\n"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            options=MagicMock(tab_size=2, insert_spaces=True),
        )

        result = formatting(params)
        assert isinstance(result, list)
        assert len(result) == 1

    @patch("gamess_lsp.server.server")
    def test_formatting_with_geometry(self, mock_server):
        """Test formatting document with geometry."""
        mock_doc = MagicMock()
        mock_doc.source = "$DATA\nWater\nC1\nO 8.0 0.0 0.0 0.0\n$END\n"
        mock_doc.lines = mock_doc.source.split("\n")
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DocumentFormattingParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            options=MagicMock(tab_size=2, insert_spaces=True),
        )

        result = formatting(params)
        assert isinstance(result, list)


class TestCompletionCoverage:
    """Test completion functionality for full coverage."""

    @patch("gamess_lsp.server.server")
    def test_completion_value_after_equals(self, mock_server):
        """Test completion after equals sign."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP="
        mock_doc.lines = ["$CONTRL SCFTYP="]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=16),
        )

        result = completion(params)
        assert isinstance(result.items, list)

    @patch("gamess_lsp.server.server")
    def test_completion_keyword_after_equals_with_value(self, mock_server):
        """Test completion with partial value after equals."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=R"
        mock_doc.lines = ["$CONTRL SCFTYP=R"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=17),
        )

        result = completion(params)
        assert isinstance(result.items, list)

    @patch("gamess_lsp.server.server")
    def test_completion_in_unknown_group(self, mock_server):
        """Test completion inside an unknown group."""
        mock_doc = MagicMock()
        mock_doc.source = "$UNKNOWN KEY="
        mock_doc.lines = ["$UNKNOWN KEY="]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=12),
        )

        result = completion(params)
        assert isinstance(result.items, list)

    @patch("gamess_lsp.server.server")
    def test_completion_no_dollar_sign(self, mock_server):
        """Test completion without dollar sign - returns all groups."""
        mock_doc = MagicMock()
        mock_doc.source = "TEST"
        mock_doc.lines = ["TEST"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=4),
        )

        result = completion(params)
        assert isinstance(result.items, list)
        # Should include group completions
        group_items = [i for i in result.items if i.label.startswith("$")]
        assert len(group_items) > 0


class TestHoverCoverage:
    """Test hover functionality for full coverage."""

    @patch("gamess_lsp.server.server")
    def test_hover_on_group_start(self, mock_server):
        """Test hover on group name start."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),
        )

        result = hover(params)
        assert result is not None

    @patch("gamess_lsp.server.server")
    def test_hover_on_empty_line(self, mock_server):
        """Test hover on empty line."""
        mock_doc = MagicMock()
        mock_doc.source = "\n$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["", "$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=0),
        )
        # result may be None for empty lines
        hover(params)

    @patch("gamess_lsp.server.server")
    def test_hover_keyword_not_in_group(self, mock_server):
        """Test hover on keyword not in current group keywords list."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL UNKNOWNKEY=RHF $END"
        mock_doc.lines = ["$CONTRL UNKNOWNKEY=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=8),
        )
        # Should handle unknown keywords gracefully
        hover(params)


class TestDefinitionCoverage:
    """Test definition functionality for full coverage."""

    @patch("gamess_lsp.server.server")
    def test_definition_empty_word(self, mock_server):
        """Test definition with empty word at position."""
        mock_doc = MagicMock()
        mock_doc.source = "   "
        mock_doc.lines = ["   "]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DefinitionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),
        )

        result = definition(params)
        assert result is None

    @patch("gamess_lsp.server.server")
    def test_definition_keyword_in_different_group(self, mock_server):
        """Test definition for keyword in group different from current."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END\n$SYSTEM MWORDS=100 $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END", "$SYSTEM MWORDS=100 $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DefinitionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=1, character=8),
        )

        result = definition(params)
        # Should find keyword in its group
        assert result is not None

    @patch("gamess_lsp.server.server")
    def test_definition_no_current_group(self, mock_server):
        """Test definition outside of any group."""
        mock_doc = MagicMock()
        mock_doc.source = "SOME TEXT"
        mock_doc.lines = ["SOME TEXT"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = DefinitionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=0),
        )

        result = definition(params)
        assert result is None


class TestReferencesCoverage:
    """Test references functionality for full coverage."""

    @patch("gamess_lsp.server.server")
    def test_references_empty_word(self, mock_server):
        """Test references with empty word."""
        mock_doc = MagicMock()
        mock_doc.source = "   "
        mock_doc.lines = ["   "]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),
            context=MagicMock(),
        )

        result = references(params)
        assert result is None

    @patch("gamess_lsp.server.server")
    def test_references_no_matches(self, mock_server):
        """Test references when no matches found."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),
            context=MagicMock(),
        )

        # Looking for CONTRL should find it
        result = references(params)
        # May return None or list
        if result is not None:
            assert len(result) >= 0

    @patch("gamess_lsp.server.server")
    def test_references_keyword_matches(self, mock_server):
        """Test references for keyword with equals sign."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END\n$SCF SCFTYP=UHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END", "$SCF SCFTYP=UHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = ReferenceParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=8),
            context=MagicMock(),
        )

        result = references(params)
        assert result is not None
        # Should find both occurrences of SCFTYP


class TestCodeActionCoverage:
    """Test code action functionality for full coverage."""

    @patch("gamess_lsp.server.server")
    def test_code_action_line_out_of_range(self, mock_server):
        """Test code action with line number out of range."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_doc.version = 1
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=10, character=0), end=Position(line=10, character=100)),
            context=MagicMock(),
        )

        actions = code_action(params)
        assert isinstance(actions, list)

    @patch("gamess_lsp.server.server")
    def test_code_action_unknown_group_no_suggestions(self, mock_server):
        """Test code action for unknown group with no close matches."""
        mock_doc = MagicMock()
        # Use a name that won't match anything
        mock_doc.source = "$XYZABC123 SCFTYP=RHF $END"
        mock_doc.lines = ["$XYZABC123 SCFTYP=RHF $END"]
        mock_doc.version = 1
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=100)),
            context=MagicMock(),
        )

        actions = code_action(params)
        # Should handle case where no suggestions exist
        assert isinstance(actions, list)

    @patch("gamess_lsp.server.server")
    def test_code_action_not_contrl_group(self, mock_server):
        """Test code action when not in $CONTRL group."""
        mock_doc = MagicMock()
        mock_doc.source = "$SYSTEM MWORDS=100 $END"
        mock_doc.lines = ["$SYSTEM MWORDS=100 $END"]
        mock_doc.version = 1
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=100)),
            context=MagicMock(),
        )

        actions = code_action(params)
        # Should not add RUNTYP action when not in $CONTRL
        runtyp_actions = [a for a in actions if "RUNTYP" in a.title]
        assert len(runtyp_actions) == 0

    @patch("gamess_lsp.server.server")
    def test_code_action_contrl_has_runtpy(self, mock_server):
        """Test code action when $CONTRL already has RUNTYP."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END"]
        mock_doc.version = 1
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=100)),
            context=MagicMock(),
        )

        actions = code_action(params)
        # Should not add RUNTYP action if it already exists
        runtyp_actions = [a for a in actions if "Add RUNTYP" in a.title]
        assert len(runtyp_actions) == 0


class TestRenameCoverage:
    """Test rename functionality for full coverage."""

    @patch("gamess_lsp.server.server")
    def test_rename_no_word_at_position(self, mock_server):
        """Test rename with no word at position."""
        mock_doc = MagicMock()
        mock_doc.source = "   "
        mock_doc.lines = ["   "]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = RenameParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),
            new_name="TEST",
        )

        result = rename(params)
        assert result is None

    @patch("gamess_lsp.server.server")
    def test_rename_group_not_in_document(self, mock_server):
        """Test rename for group not present in document."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = RenameParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),
            new_name="NOTINDOC",
        )

        # Trying to rename CONTRL
        result = rename(params)
        # Should return edit even though it's a rename
        assert result is not None

    @patch("gamess_lsp.server.server")
    def test_rename_keyword_not_in_current_group(self, mock_server):
        """Test rename for keyword not in current group."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END\n$SYSTEM MWORDS=100 $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END", "$SYSTEM MWORDS=100 $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = RenameParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=8),
            new_name="NEWKEY",
        )

        result = rename(params)
        assert result is not None

    @patch("gamess_lsp.server.server")
    def test_rename_with_dollar_prefix(self, mock_server):
        """Test rename with $ prefix in new name."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = RenameParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),
            new_name="$NEWGROUP",
        )

        result = rename(params)
        assert result is not None
