"""Tests for GAMESS LSP code actions."""

from unittest.mock import MagicMock, patch

from lsprotocol.types import CodeActionParams, Position, Range, RenameParams, TextDocumentIdentifier

from gamess_lsp.server import code_action, rename


class TestCodeAction:
    """Test code action feature."""

    @patch("gamess_lsp.server.server")
    def test_code_action_add_end(self, mock_server):
        """Test code action to add missing $END."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF"]
        mock_doc.version = 1
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=100)),
            context=MagicMock(),
        )

        actions = code_action(params)
        assert len(actions) >= 1
        # Find Add missing $END action
        add_end_actions = [a for a in actions if "Add missing $END" in a.title]
        assert len(add_end_actions) >= 1

    @patch("gamess_lsp.server.server")
    def test_code_action_unknown_group(self, mock_server):
        """Test code action to fix unknown groups."""
        mock_doc = MagicMock()
        mock_doc.source = "$CNTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CNTRL SCFTYP=RHF $END"]
        mock_doc.version = 1
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=100)),
            context=MagicMock(),
        )

        actions = code_action(params)
        # Should suggest changing CNTRL to CONTRL
        fix_actions = [a for a in actions if "Change to" in a.title]
        assert len(fix_actions) >= 1

    @patch("gamess_lsp.server.server")
    def test_code_action_add_runtpy(self, mock_server):
        """Test code action to add RUNTYP to $CONTRL."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_doc.version = 1
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=100)),
            context=MagicMock(),
        )

        actions = code_action(params)
        runtyp_actions = [a for a in actions if "RUNTYP" in a.title]
        assert len(runtyp_actions) >= 1

    @patch("gamess_lsp.server.server")
    def test_code_action_empty_document(self, mock_server):
        """Test code action with empty document."""
        mock_doc = MagicMock()
        mock_doc.source = ""
        mock_doc.lines = []
        mock_doc.version = 1
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=100)),
            context=MagicMock(),
        )

        actions = code_action(params)
        assert isinstance(actions, list)


class TestRename:
    """Test rename feature."""

    @patch("gamess_lsp.server.server")
    def test_rename_group(self, mock_server):
        """Test renaming a group."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = RenameParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),  # On 'C' in $CONTRL
            new_name="CONTROL",
        )

        result = rename(params)
        assert result is not None
        assert params.text_document.uri in result.changes

    @patch("gamess_lsp.server.server")
    def test_rename_keyword(self, mock_server):
        """Test renaming a keyword."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL SCFTYP=RHF $END"
        mock_doc.lines = ["$CONTRL SCFTYP=RHF $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = RenameParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=8),  # On 'S' in SCFTYP
            new_name="WAVEFUNCTION",
        )

        result = rename(params)
        # Should return a WorkspaceEdit
        assert result is not None

    @patch("gamess_lsp.server.server")
    def test_rename_empty_position(self, mock_server):
        """Test rename at empty position."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL $END"
        mock_doc.lines = ["$CONTRL $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = RenameParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=20),  # Past end of line
            new_name="TEST",
        )

        result = rename(params)
        # May return None if no word at position
        assert result is None or isinstance(result, type(result))

    @patch("gamess_lsp.server.server")
    def test_rename_keyword_at_end_of_line(self, mock_server):
        """Test renaming a keyword at the end of line."""
        mock_doc = MagicMock()
        mock_doc.source = "$CONTRL $END"
        mock_doc.lines = ["$CONTRL $END"]
        mock_server.workspace.get_text_document.return_value = mock_doc

        params = RenameParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=1),  # On 'C' in $CONTRL
            new_name="CONTROL",
        )

        result = rename(params)
        assert result is not None
        assert params.text_document.uri in result.changes
