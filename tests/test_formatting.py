"""Tests for GAMESS LSP formatting feature."""

from unittest.mock import MagicMock, patch

from lsprotocol.types import (
    DocumentFormattingParams,
    DocumentRangeFormattingParams,
    FormattingOptions,
    Position,
    Range,
    TextDocumentIdentifier,
)

from gamess_lsp.features.formatting import GamessFormattingProvider
from gamess_lsp.server import _format_keywords, formatting, range_formatting


# ---------------------------------------------------------------------------
# Helper to build params
# ---------------------------------------------------------------------------

def _fmt_params(
    uri: str = "file:///test.inp",
    tab_size: int = 2,
    insert_spaces: bool = True,
) -> DocumentFormattingParams:
    return DocumentFormattingParams(
        text_document=TextDocumentIdentifier(uri=uri),
        options=FormattingOptions(tab_size=tab_size, insert_spaces=insert_spaces),
    )


def _range_params(
    start_line: int,
    end_line: int,
    uri: str = "file:///test.inp",
    tab_size: int = 2,
    insert_spaces: bool = True,
) -> DocumentRangeFormattingParams:
    return DocumentRangeFormattingParams(
        text_document=TextDocumentIdentifier(uri=uri),
        range=Range(
            start=Position(line=start_line, character=0),
            end=Position(line=end_line, character=0),
        ),
        options=FormattingOptions(tab_size=tab_size, insert_spaces=insert_spaces),
    )


def _mock_doc(source: str) -> MagicMock:
    doc = MagicMock()
    doc.source = source
    doc.lines = source.split("\n")
    return doc


# ===========================================================================
# Document formatting via server handler
# ===========================================================================


class TestFormatting:
    """Test document formatting via the server handler."""

    @patch("gamess_lsp.server.server")
    def test_format_simple_document(self, mock_server):
        """Test formatting a simple document."""
        mock_doc = _mock_doc("$CONTRL SCFTYP=RHF $END")
        mock_server.workspace.get_text_document.return_value = mock_doc

        result = formatting(_fmt_params())
        assert len(result) == 1
        assert isinstance(result[0].new_text, str)

    @patch("gamess_lsp.server.server")
    def test_format_multiline_document(self, mock_server):
        """Test formatting a multiline document."""
        content = "$CONTRL\nSCFTYP=RHF\nRUNTYP=ENERGY\n$END"
        mock_doc = _mock_doc(content)
        mock_server.workspace.get_text_document.return_value = mock_doc

        result = formatting(_fmt_params())
        assert len(result) == 1
        formatted = result[0].new_text
        assert "$CONTRL" in formatted
        assert "$END" in formatted

    @patch("gamess_lsp.server.server")
    def test_format_with_comments(self, mock_server):
        """Test formatting preserves comments."""
        content = "! This is a comment\n$CONTRL SCFTYP=RHF $END\n! Another comment"
        mock_doc = _mock_doc(content)
        mock_server.workspace.get_text_document.return_value = mock_doc

        result = formatting(_fmt_params())
        assert len(result) == 1
        formatted = result[0].new_text
        assert "! This is a comment" in formatted

    @patch("gamess_lsp.server.server")
    def test_format_empty_document(self, mock_server):
        """Formatting an empty document returns no edits (nothing to change)."""
        mock_doc = _mock_doc("")
        mock_server.workspace.get_text_document.return_value = mock_doc

        result = formatting(_fmt_params())
        # Empty input produces empty output -> no edit needed
        assert result == []


# ===========================================================================
# FormattingProvider unit tests
# ===========================================================================


class TestFormattingProvider:
    """Test the FormattingProvider class directly."""

    def setup_method(self):
        self.provider = GamessFormattingProvider(server=MagicMock())

    # -- document formatting --------------------------------------------------

    def test_format_simple_group(self):
        """Format a single-group document."""
        text = "$CONTRL\nSCFTYP=RHF\nRUNTYP=ENERGY\n$END"
        result = self.provider.format_document(text, _fmt_params())
        assert len(result) == 1
        formatted = result[0].new_text
        assert formatted.startswith("$CONTRL\n")
        assert formatted.endswith("$END")
        assert "  SCFTYP=RHF" in formatted
        assert "  RUNTYP=ENERGY" in formatted

    def test_format_uppercases_keywords(self):
        """Keywords are uppercased during formatting."""
        text = "$contrl\nscftyp=rhf\n$end"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert "$CONTRL" in formatted
        assert "SCFTYP=RHF" in formatted
        assert "$END" in formatted

    def test_format_uppercases_group_names(self):
        """Group names are uppercased."""
        text = "$basis\ngbasIS=CC-PVDZ\n$end"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert "$BASIS" in formatted
        assert "GBASIS=CC-PVDZ" in formatted

    def test_format_preserves_comments(self):
        """Comments are preserved unchanged."""
        text = "! My calc\n$CONTRL\nSCFTYP=RHF\n$END\n! trailing"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert "! My calc" in formatted
        assert "! trailing" in formatted

    def test_format_preserves_blank_lines(self):
        """Blank lines are preserved."""
        text = "$CONTRL\nSCFTYP=RHF\n\n$END"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert "\n\n" in formatted

    def test_format_multiple_groups(self):
        """Multiple groups are formatted with proper indentation."""
        text = "$CONTRL\nSCFTYP=RHF RUNTYP=ENERGY\n$END\n$BASIS\nGBASIS=STO NGAUSS=3\n$END"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        lines = formatted.split("\n")
        assert lines[0] == "$CONTRL"
        assert lines[1] == "  SCFTYP=RHF RUNTYP=ENERGY"
        assert lines[2] == "$END"
        assert lines[3] == "$BASIS"
        assert lines[4] == "  GBASIS=STO NGAUSS=3"
        assert lines[5] == "$END"

    def test_format_data_group_preserves_geometry(self):
        """$DATA group content is preserved with indentation."""
        text = "$DATA\nWater molecule\nCnv 2\n\nO     8.0   0.0  0.0  0.117\nH     1.0   0.0  0.757 -0.470\n$END"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert "  Water molecule" in formatted
        assert "  Cnv 2" in formatted
        assert "  O     8.0   0.0  0.0  0.117" in formatted

    def test_format_inline_keywords_after_group(self):
        """Inline keywords after group name are placed on next line."""
        text = "$CONTRL SCFTYP=RHF\n$END"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        lines = formatted.split("\n")
        assert lines[0] == "$CONTRL"
        assert lines[1] == "  SCFTYP=RHF"

    def test_format_preserves_trailing_newline(self):
        """Trailing newline is preserved."""
        text = "$CONTRL\nSCFTYP=RHF\n$END\n"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert formatted.endswith("\n")

    def test_format_no_trailing_newline(self):
        """No trailing newline when original lacks one."""
        text = "$CONTRL\nSCFTYP=RHF\n$END"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert not formatted.endswith("\n")

    def test_format_already_formatted_returns_empty(self):
        """Already-formatted document returns no edits."""
        text = "$CONTRL\n  SCFTYP=RHF\n$END"
        result = self.provider.format_document(text, _fmt_params())
        assert result == []

    def test_format_tab_indent_option(self):
        """Tab indent option is respected."""
        text = "$CONTRL\nSCFTYP=RHF\n$END"
        params = _fmt_params(tab_size=4, insert_spaces=False)
        result = self.provider.format_document(text, params)
        formatted = result[0].new_text
        assert "\tSCFTYP=RHF" in formatted

    def test_format_custom_tab_size(self):
        """Custom tab_size produces correct number of spaces."""
        text = "$CONTRL\nSCFTYP=RHF\n$END"
        params = _fmt_params(tab_size=4)
        result = self.provider.format_document(text, params)
        formatted = result[0].new_text
        assert "    SCFTYP=RHF" in formatted

    def test_format_normalizes_spaces_around_equals(self):
        """Spaces around equals signs are normalized."""
        text = "$CONTRL\nSCFTYP = RHF  RUNTYP = ENERGY\n$END"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert "SCFTYP=RHF" in formatted
        assert "RUNTYP=ENERGY" in formatted

    # -- $END edge cases ------------------------------------------------------

    def test_format_dollar_end_case_insensitive(self):
        """$end, $End, etc. are all treated as $END."""
        text = "$CONTRL\nSCFTYP=RHF\n$end"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert "$END" in formatted

    def test_format_inline_dollar_end(self):
        """Inline $END after group name produces group + $END."""
        text = "$CONTRL $END"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        lines = formatted.split("\n")
        assert "$CONTRL" in lines[0]
        assert "$END" in lines[1]

    # -- malformed input ------------------------------------------------------

    def test_format_unclosed_group(self):
        """Unclosed group is still formatted (indent preserved)."""
        text = "$CONTRL\nSCFTYP=RHF"
        result = self.provider.format_document(text, _fmt_params())
        formatted = result[0].new_text
        assert "$CONTRL" in formatted
        assert "SCFTYP=RHF" in formatted

    def test_format_lone_dollar_end(self):
        """$END without matching group is handled gracefully."""
        text = "$END"
        result = self.provider.format_document(text, _fmt_params())
        # $END with no open group: formatted == original, so no edits
        assert result == []

    # -- idempotency ----------------------------------------------------------

    def test_format_idempotent(self):
        """Formatting twice produces the same output."""
        text = "$CONTRL\n  scftyp=rhf   runtyp=ENERGY\n$end\n$BASIS\n  GBASIS=CC-PVDZ\n$END"
        result1 = self.provider.format_document(text, _fmt_params())
        first_pass = result1[0].new_text

        result2 = self.provider.format_document(first_pass, _fmt_params())
        # Second pass should produce no edits (already formatted)
        assert result2 == []

    def test_format_idempotent_complex(self):
        """Idempotency with comments, blank lines, multiple groups, $DATA."""
        text = """! Complex input
$CONTRL
SCFTYP=RHF RUNTYP=OPTIMIZE
$END

$BASIS
GBASIS=CC-PVDZ
$END

$DATA
Water
C1

O     8.0   0.0  0.0  0.117
H     1.0   0.0  0.757 -0.470
$END"""
        first = self.provider.format_document(text, _fmt_params())[0].new_text
        second_result = self.provider.format_document(first, _fmt_params())
        assert second_result == [], f"Not idempotent: got {second_result}"


# ===========================================================================
# Range formatting
# ===========================================================================


class TestRangeFormatting:
    """Test range formatting via the server handler."""

    def setup_method(self):
        self.provider = GamessFormattingProvider(server=MagicMock())

    @patch("gamess_lsp.server.server")
    def test_range_format_handler(self, mock_server):
        """Range formatting handler delegates to provider."""
        content = "$CONTRL\n  scftyp=rhf\n  RUNTYP=ENERGY\n$END"
        mock_doc = _mock_doc(content)
        mock_server.workspace.get_text_document.return_value = mock_doc

        result = range_formatting(_range_params(1, 2))
        assert isinstance(result, list)
        for edit in result:
            assert hasattr(edit, "new_text")
            assert hasattr(edit, "range")

    def test_range_format_only_selected_lines(self):
        """Range formatting only changes lines within the range."""
        text = "$CONTRL\nscftyp=rhf\nRUNTYP=ENERGY\n$END"
        result = self.provider.format_range(text, _range_params(1, 1))
        # Only line 1 should change
        for edit in result:
            assert edit.range.start.line >= 1
            assert edit.range.end.line <= 1
            assert "SCFTYP=RHF" in edit.new_text

    def test_range_format_respects_group_indent(self):
        """Range formatting computes correct indent from document context."""
        text = "$CONTRL\nscftyp=rhf\nRUNTYP=ENERGY\n$END"
        result = self.provider.format_range(text, _range_params(1, 2))
        for edit in result:
            assert edit.new_text.startswith("  ")

    def test_range_format_outside_group(self):
        """Range formatting on lines outside a group uses zero indent."""
        text = "! top comment\n$CONTRL\nSCFTYP=RHF\n$END"
        result = self.provider.format_range(text, _range_params(0, 0))
        # Comment line should be preserved as-is
        if result:
            assert "! top comment" in result[0].new_text

    def test_range_format_empty_range(self):
        """Range formatting with invalid range returns no edits."""
        text = "$CONTRL\nSCFTYP=RHF\n$END"
        result = self.provider.format_range(
            text, _range_params(5, 3)  # start > end
        )
        assert result == []

    def test_range_format_clamps_to_document(self):
        """Range formatting clamps to document boundaries."""
        text = "$CONTRL\nSCFTYP=RHF\n$END"
        result = self.provider.format_range(
            text, _range_params(0, 100)  # end beyond document
        )
        assert isinstance(result, list)

    def test_range_format_unchanged_returns_empty(self):
        """Range formatting returns empty list if lines are already formatted."""
        text = "$CONTRL\n  SCFTYP=RHF\n$END"
        result = self.provider.format_range(text, _range_params(1, 1))
        assert result == []


# ===========================================================================
# _format_keywords helper
# ===========================================================================


class TestFormatKeywords:
    """Test _format_keywords helper function."""

    def test_format_single_keyword(self):
        result = _format_keywords("SCFTYP=RHF")
        assert result == "SCFTYP=RHF"

    def test_format_multiple_keywords(self):
        result = _format_keywords("SCFTYP=RHF RUNTYP=ENERGY")
        assert "SCFTYP=RHF" in result
        assert "RUNTYP=ENERGY" in result

    def test_format_quoted_values(self):
        result = _format_keywords('EXETYP="CHECK"')
        assert 'EXETYP="CHECK"' in result

    def test_format_with_extra_spaces(self):
        result = _format_keywords("SCFTYP  =  RHF")
        assert "SCFTYP=RHF" in result

    def test_format_uppercases_keywords(self):
        result = _format_keywords("scftyp=rhf")
        assert "SCFTYP=RHF" == result

    def test_format_preserves_value_case(self):
        """Values that are not standard keywords are preserved."""
        result = _format_keywords("GBASIS=CC-PVDZ")
        assert "GBASIS=CC-PVDZ" == result


# ===========================================================================
# Internal helper unit tests
# ===========================================================================


class TestInternalHelpers:
    """Test internal helper methods of FormattingProvider."""

    def setup_method(self):
        self.provider = GamessFormattingProvider(server=MagicMock())

    def test_compute_context_at_line_basic(self):
        """Context computation tracks group nesting."""
        lines = ["$CONTRL", "SCFTYP=RHF", "$END", "$BASIS", "GBASIS=STO"]
        level, in_data = GamessFormattingProvider._compute_context_at_line(lines, 4)
        assert level == 1
        assert in_data is False

    def test_compute_context_at_line_data_group(self):
        """Context computation tracks $DATA group."""
        lines = ["$DATA", "Title", "C1", "O 8.0 0.0 0.0 0.0"]
        level, in_data = GamessFormattingProvider._compute_context_at_line(lines, 3)
        assert level == 1
        assert in_data is True

    def test_compute_context_at_line_after_end(self):
        """Context computation resets after $END."""
        lines = ["$CONTRL", "SCFTYP=RHF", "$END"]
        level, in_data = GamessFormattingProvider._compute_context_at_line(lines, 3)
        assert level == 0
        assert in_data is False

    def test_update_context_group_start(self):
        level, in_data = GamessFormattingProvider._update_context("$BASIS", 0, False)
        assert level == 1
        assert in_data is False

    def test_update_context_data_start(self):
        level, in_data = GamessFormattingProvider._update_context("$DATA", 0, False)
        assert level == 1
        assert in_data is True

    def test_update_context_end(self):
        level, in_data = GamessFormattingProvider._update_context("$END", 1, True)
        assert level == 0
        assert in_data is False

    def test_update_context_blank_line(self):
        level, in_data = GamessFormattingProvider._update_context("", 2, False)
        assert level == 2
        assert in_data is False

    def test_update_context_comment(self):
        level, in_data = GamessFormattingProvider._update_context("! comment", 1, True)
        assert level == 1
        assert in_data is True
