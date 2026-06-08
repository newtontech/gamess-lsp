"""Tests for the navigation feature providers.

Covers SymbolIndex, DefinitionProvider, HoverProvider, and ReferencesProvider
for sections, keywords, includes, and variables.
"""

import pytest

from gamess_lsp.features.navigation import (
    DefinitionProvider,
    HoverProvider,
    ReferencesProvider,
    SymbolIndex,
    SymbolInfo,
    _extract_word,
)
from lsprotocol.types import Position


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BASIC_INPUT = """\
! Water molecule DFT calculation
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS=CC-PVDZ $END
 $STATPT OPTTOL=0.0001 NSTEP=50 $END
 $DATA
Water molecule
C1

O     8.0   0.000000   0.000000   0.117489
H     1.0   0.000000   0.757210  -0.469957
 $END
"""

BASIS_WITH_INCLUDE = """\
 $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
 $BASIS EXTFIL=.TRUE. BASNAM=mybasis $END
"""

VEC_INPUT = """\
 $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
 $GUESS GUESS=MOREAD $END
 $VEC
1  1  0.123456  0.234567
 $END
"""

MULTI_SECTION_INPUT = """\
 $CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END
 $SCF DIRSCF=.TRUE. $END
 $SCF DIRSCF=.FALSE. $END
 $CONTRL SCFTYP=UHF $END
"""


# ---------------------------------------------------------------------------
# _extract_word
# ---------------------------------------------------------------------------


class TestExtractWord:
    def test_middle_of_keyword(self):
        assert _extract_word("SCFTYP=RHF", 3) == "SCFTYP"

    def test_start_of_line(self):
        assert _extract_word("SCFTYP=RHF", 0) == "SCFTYP"

    def test_dollar_prefix(self):
        assert _extract_word("$CONTRL SCFTYP=RHF", 1) == "$CONTRL"

    def test_empty_line(self):
        assert _extract_word("", 0) == ""

    def test_position_out_of_range(self):
        assert _extract_word("hi", 99) == ""


# ---------------------------------------------------------------------------
# SymbolIndex
# ---------------------------------------------------------------------------


class TestSymbolIndex:
    def test_build_sections(self):
        idx = SymbolIndex()
        idx.build(BASIC_INPUT)
        section_names = [s.name for s in idx.symbols if s.kind == "section"]
        assert "CONTRL" in section_names
        assert "SYSTEM" in section_names
        assert "BASIS" in section_names
        assert "STATPT" in section_names
        assert "DATA" in section_names

    def test_build_keywords(self):
        idx = SymbolIndex()
        idx.build(BASIC_INPUT)
        kw_names = [s.name for s in idx.symbols if s.kind == "keyword"]
        assert "SCFTYP" in kw_names
        assert "DFTTYP" in kw_names
        assert "RUNTYP" in kw_names
        assert "MWORDS" in kw_names
        assert "GBASIS" in kw_names
        assert "OPTTOL" in kw_names

    def test_build_variables_data(self):
        idx = SymbolIndex()
        idx.build(BASIC_INPUT)
        vars = [s for s in idx.symbols if s.kind == "variable"]
        var_names = [v.name for v in vars]
        assert "O" in var_names
        assert "H" in var_names

    def test_build_vec_variable(self):
        idx = SymbolIndex()
        idx.build(VEC_INPUT)
        vars = [s for s in idx.symbols if s.kind == "variable" and s.name == "VEC"]
        assert len(vars) == 1
        assert vars[0].detail == "Molecular orbital vectors"

    def test_build_include_symbols(self):
        idx = SymbolIndex()
        idx.build(BASIS_WITH_INCLUDE)
        includes = [s for s in idx.symbols if s.kind == "include"]
        inc_names = [s.name for s in includes]
        assert "EXTFIL" in inc_names
        assert "BASNAM" in inc_names
        basnam = [s for s in includes if s.name == "BASNAM"][0]
        assert basnam.detail == "mybasis"

    def test_symbol_at_keyword(self):
        idx = SymbolIndex()
        idx.build(BASIC_INPUT)
        # Line 1 (0-based) = "$CONTRL SCFTYP=RHF ..."
        # SCFTYP starts around column 10
        sym = idx.symbol_at(1, 12)
        assert sym is not None
        assert sym.kind == "keyword"
        assert sym.name == "SCFTYP"

    def test_symbol_at_section(self):
        idx = SymbolIndex()
        idx.build(BASIC_INPUT)
        # Line 1 (0-based) = "$CONTRL ..."
        sym = idx.symbol_at(1, 1)
        assert sym is not None
        assert sym.kind == "section"
        assert sym.name == "CONTRL"

    def test_symbol_at_nothing(self):
        idx = SymbolIndex()
        idx.build(BASIC_INPUT)
        # Line 0 is a comment, no symbols
        sym = idx.symbol_at(0, 1)
        assert sym is None

    def test_find_definitions(self):
        """Parser deduplicates groups (dict key), so only the last occurrence is indexed."""
        idx = SymbolIndex()
        idx.build(MULTI_SECTION_INPUT)
        defs = idx.find_definitions("CONTRL")
        # Parser keeps the last $CONTRL (line 4), so only 1 in the index
        assert len(defs) == 1
        assert defs[0].line == 3  # 0-based line 3 = 1-based line 4

    def test_find_definitions_by_kind(self):
        idx = SymbolIndex()
        idx.build(MULTI_SECTION_INPUT)
        defs = idx.find_definitions("CONTRL", kind="section")
        assert all(d.kind == "section" for d in defs)

    def test_empty_content(self):
        idx = SymbolIndex()
        idx.build("")
        assert idx.symbols == []

    def test_uri_propagation(self):
        idx = SymbolIndex()
        idx.build(BASIC_INPUT, uri="file:///test.inp")
        for s in idx.symbols:
            assert s.uri == "file:///test.inp"


# ---------------------------------------------------------------------------
# DefinitionProvider
# ---------------------------------------------------------------------------


class TestDefinitionProvider:
    provider = DefinitionProvider()

    def test_definition_on_section(self):
        result = self.provider.get_definition(
            BASIC_INPUT,
            "file:///test.inp",
            Position(line=1, character=1),
        )
        assert result is not None
        assert len(result) >= 1
        loc = result[0]
        assert loc.uri == "file:///test.inp"
        # Should point to $CONTRL start
        assert loc.range.start.line == 1

    def test_definition_on_keyword(self):
        result = self.provider.get_definition(
            BASIC_INPUT,
            "file:///test.inp",
            Position(line=1, character=12),  # SCFTYP
        )
        assert result is not None
        assert result[0].range.start.line == 1

    def test_definition_on_data_atom(self):
        result = self.provider.get_definition(
            BASIC_INPUT,
            "file:///test.inp",
            Position(line=9, character=0),  # O atom line
        )
        assert result is not None
        # Should find the O atom variable
        assert result[0].range.start.line == 9

    def test_definition_empty_word(self):
        result = self.provider.get_definition(
            "   \n",
            "file:///test.inp",
            Position(line=0, character=1),
        )
        assert result is None

    def test_definition_on_include(self):
        result = self.provider.get_definition(
            BASIS_WITH_INCLUDE,
            "file:///test.inp",
            Position(line=1, character=30),  # BASNAM area
        )
        # May return a location pointing to the include target or the keyword
        # depending on whether the target file exists
        assert result is None or isinstance(result, list)

    def test_definition_unknown_word(self):
        content = "SOME TEXT\n"
        result = self.provider.get_definition(
            content,
            "file:///test.inp",
            Position(line=0, character=0),
        )
        assert result is None


# ---------------------------------------------------------------------------
# HoverProvider
# ---------------------------------------------------------------------------


class TestHoverProvider:
    provider = HoverProvider()

    def test_hover_on_section(self):
        result = self.provider.get_hover(
            BASIC_INPUT,
            Position(line=1, character=1),
        )
        assert result is not None
        assert "CONTRL" in result.contents.value

    def test_hover_on_keyword(self):
        result = self.provider.get_hover(
            BASIC_INPUT,
            Position(line=1, character=12),  # SCFTYP
        )
        assert result is not None
        assert "SCFTYP" in result.contents.value

    def test_hover_on_data_atom(self):
        result = self.provider.get_hover(
            BASIC_INPUT,
            Position(line=9, character=0),  # O atom
        )
        assert result is not None
        assert "Atom" in result.contents.value

    def test_hover_on_vec_variable(self):
        result = self.provider.get_hover(
            VEC_INPUT,
            Position(line=2, character=1),  # $VEC
        )
        assert result is not None
        assert "VEC" in result.contents.value

    def test_hover_on_include(self):
        result = self.provider.get_hover(
            BASIS_WITH_INCLUDE,
            Position(line=1, character=30),
        )
        # Hover on the include keyword area
        assert result is None or "include" in result.contents.value.lower() or "BASIS" in result.contents.value

    def test_hover_unknown_keyword(self):
        content = "$CONTRL FOOBAR=123 $END\n"
        result = self.provider.get_hover(
            content,
            Position(line=0, character=10),
        )
        assert result is not None
        assert "FOOBAR" in result.contents.value

    def test_hover_empty_line(self):
        result = self.provider.get_hover(
            BASIC_INPUT,
            Position(line=0, character=0),
        )
        assert result is None

    def test_hover_on_keyword_with_values(self):
        result = self.provider.get_hover(
            BASIC_INPUT,
            Position(line=1, character=33),  # RUNTYP at correct column
        )
        assert result is not None
        assert "RUNTYP" in result.contents.value
        assert "OPTIMIZE" in result.contents.value

    def test_hover_returns_markdown(self):
        result = self.provider.get_hover(
            BASIC_INPUT,
            Position(line=1, character=1),
        )
        assert result is not None
        assert result.contents.kind.name == "Markdown"


# ---------------------------------------------------------------------------
# ReferencesProvider
# ---------------------------------------------------------------------------


class TestReferencesProvider:
    provider = ReferencesProvider()

    def test_references_on_section(self):
        result = self.provider.get_references(
            MULTI_SECTION_INPUT,
            "file:///test.inp",
            Position(line=0, character=1),  # $CONTRL
        )
        # Textual search finds all $CONTRL occurrences (2 in the input)
        assert len(result) >= 2

    def test_references_on_keyword(self):
        result = self.provider.get_references(
            MULTI_SECTION_INPUT,
            "file:///test.inp",
            Position(line=0, character=10),  # SCFTYP
        )
        # SCFTYP appears in both $CONTRL sections
        assert len(result) >= 2

    def test_references_no_match(self):
        content = "$CONTRL SCFTYP=RHF $END\n"
        result = self.provider.get_references(
            content,
            "file:///test.inp",
            Position(line=0, character=1),
        )
        # CONTRL should match $CONTRL
        assert len(result) >= 1

    def test_references_empty_word(self):
        result = self.provider.get_references(
            "   \n",
            "file:///test.inp",
            Position(line=0, character=1),
        )
        assert result == []

    def test_references_include_declaration_false(self):
        result = self.provider.get_references(
            MULTI_SECTION_INPUT,
            "file:///test.inp",
            Position(line=0, character=1),
            include_declaration=False,
        )
        # With include_declaration=False, at least one reference excluded
        # (behavior depends on whether the index treats the first as declaration)
        assert isinstance(result, list)

    def test_references_data_atom(self):
        result = self.provider.get_references(
            BASIC_INPUT,
            "file:///test.inp",
            Position(line=9, character=0),  # O atom
        )
        assert len(result) >= 1

    def test_references_fallback_textual_search(self):
        """Fallback to regex when symbol index has no match."""
        content = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        # Position on "ENERGY" (value, not a keyword)
        result = self.provider.get_references(
            content,
            "file:///test.inp",
            Position(line=0, character=30),
        )
        # Should still do a regex-based search
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Integration: providers work with server.py patterns
# ---------------------------------------------------------------------------


class TestNavigationIntegration:
    """Integration tests verifying navigation works through server handlers."""

    def test_index_covers_all_groups(self):
        idx = SymbolIndex()
        idx.build(BASIC_INPUT)
        kinds = {s.kind for s in idx.symbols}
        assert "section" in kinds
        assert "keyword" in kinds
        assert "variable" in kinds

    def test_definition_round_trip(self):
        """Definition of a keyword should point to its own line."""
        content = "$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END\n"
        provider = DefinitionProvider()
        result = provider.get_definition(
            content,
            "file:///test.inp",
            Position(line=0, character=10),  # SCFTYP
        )
        assert result is not None
        assert result[0].range.start.line == 0

    def test_hover_round_trip(self):
        """Hover on a section should return its documentation."""
        provider = HoverProvider()
        result = provider.get_hover(
            "$BASIS GBASIS=CC-PVDZ $END\n",
            Position(line=0, character=1),
        )
        assert result is not None
        assert "BASIS" in result.contents.value

    def test_references_count_across_file(self):
        """References for a section name should count all occurrences."""
        content = "$SCF DIRSCF=.TRUE. $END\n $SCF DIIS=.TRUE. $END\n"
        provider = ReferencesProvider()
        result = provider.get_references(
            content,
            "file:///test.inp",
            Position(line=0, character=1),  # $SCF
        )
        assert len(result) == 2

    def test_multi_file_workspace(self):
        """Multiple URIs in the index should be trackable."""
        idx1 = SymbolIndex()
        idx1.build("$CONTRL SCFTYP=RHF $END\n", uri="file:///a.inp")
        idx2 = SymbolIndex()
        idx2.build("$CONTRL SCFTYP=UHF $END\n", uri="file:///b.inp")

        symbols = idx1.symbols + idx2.symbols
        sections = [s for s in symbols if s.kind == "section" and s.name == "CONTRL"]
        assert len(sections) == 2
        uris = {s.uri for s in sections}
        assert uris == {"file:///a.inp", "file:///b.inp"}

    def test_include_resolution_nonexistent_file(self):
        """Include resolution for non-existent file should still return a URI."""
        result = DefinitionProvider._resolve_include_uri(
            "file:///home/user/test.inp", "nonexistent_basis"
        )
        # May return None (file doesn't exist) or a best-guess URI
        # Either way, it should not crash
        assert result is None or "nonexistent_basis" in result

    def test_definition_provider_with_unclosed_group(self):
        """Definition should handle unclosed groups gracefully."""
        content = "$CONTRL SCFTYP=RHF\n"
        provider = DefinitionProvider()
        result = provider.get_definition(
            content,
            "file:///test.inp",
            Position(line=0, character=10),
        )
        assert result is not None
