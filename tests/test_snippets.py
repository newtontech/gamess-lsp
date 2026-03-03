"""Tests for GAMESS snippets."""

import pytest
from gamess_lsp.snippets import (
    GAMESS_SNIPPETS,
    get_snippet,
    get_all_snippets,
)


class TestSnippets:
    """Test cases for code snippets."""
    
    def test_get_snippet_exists(self):
        snippet = get_snippet("scf_calculation")
        assert snippet is not None
        assert snippet.prefix == "scf"
    
    def test_get_snippet_not_exists(self):
        snippet = get_snippet("nonexistent")
        assert snippet is None
    
    def test_get_all_snippets(self):
        snippets = get_all_snippets()
        assert len(snippets) > 0
        assert len(snippets) == len(GAMESS_SNIPPETS)
    
    def test_scf_snippet(self):
        snippet = get_snippet("scf_calculation")
        assert snippet is not None
        assert "scf" == snippet.prefix
        assert "SCFTYP" in '\n'.join(snippet.body)
        assert "RHF" in '\n'.join(snippet.body)
    
    def test_opt_snippet(self):
        snippet = get_snippet("geometry_optimization")
        assert snippet is not None
        assert "opt" == snippet.prefix
        assert "OPTIMIZE" in '\n'.join(snippet.body)
    
    def test_freq_snippet(self):
        snippet = get_snippet("frequency_calculation")
        assert snippet is not None
        assert "freq" == snippet.prefix
        assert "HESSIAN" in '\n'.join(snippet.body)
    
    def test_dft_snippet(self):
        snippet = get_snippet("dft_calculation")
        assert snippet is not None
        assert "dft" == snippet.prefix
        assert "DFTTYP" in '\n'.join(snippet.body)
    
    def test_mp2_snippet(self):
        snippet = get_snippet("mp2_calculation")
        assert snippet is not None
        assert "mp2" == snippet.prefix
        assert "MPLEVL=2" in '\n'.join(snippet.body)
    
    def test_tddft_snippet(self):
        snippet = get_snippet("td_dft")
        assert snippet is not None
        assert "tddft" == snippet.prefix
        assert "TDDFT" in '\n'.join(snippet.body)
    
    def test_cis_snippet(self):
        snippet = get_snippet("cis_calculation")
        assert snippet is not None
        assert "cis" == snippet.prefix
        assert "CITYP=CIS" in '\n'.join(snippet.body)
    
    def test_data_group_snippet(self):
        snippet = get_snippet("data_group")
        assert snippet is not None
        assert "data" == snippet.prefix
        assert "$DATA" in snippet.body[0]
    
    def test_contrl_group_snippet(self):
        snippet = get_snippet("control_group")
        assert snippet is not None
        assert "contrl" == snippet.prefix
        assert "$CONTRL" in snippet.body[0]
    
    def test_snippets_have_description(self):
        for snippet in get_all_snippets():
            assert snippet.description
            assert len(snippet.description) > 0
    
    def test_snippets_have_body(self):
        for snippet in get_all_snippets():
            assert len(snippet.body) > 0
            for line in snippet.body:
                assert isinstance(line, str)
