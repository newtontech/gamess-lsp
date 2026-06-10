"""Tests for the shared tokenizer utility."""

from gamess_lsp.tokenizer import tokenize_line


class TestTokenizeLine:
    """Tests for tokenize_line function."""

    def test_simple_tokens(self):
        """Whitespace-separated tokens without quotes."""
        assert tokenize_line("A=1 B=2 C=3") == ["A=1", "B=2", "C=3"]

    def test_empty_string(self):
        """Empty input returns empty list."""
        assert tokenize_line("") == []

    def test_whitespace_only(self):
        """Whitespace-only input returns empty list."""
        assert tokenize_line("   ") == []

    def test_single_token(self):
        """Single token without spaces."""
        assert tokenize_line("KEY=VALUE") == ["KEY=VALUE"]

    def test_double_quoted_value(self):
        """Double-quoted value preserved as single token."""
        assert tokenize_line('KEY="hello world"') == ['KEY="hello world"']

    def test_single_quoted_value(self):
        """Single-quoted value preserved as single token."""
        assert tokenize_line("KEY='hello world'") == ["KEY='hello world'"]

    def test_mixed_quoted_and_unquoted(self):
        """Mix of quoted and unquoted tokens."""
        result = tokenize_line('A=1 NAME="john doe" C=3')
        assert result == ["A=1", 'NAME="john doe"', "C=3"]

    def test_quoted_with_inner_spaces(self):
        """Quoted values with multiple inner spaces."""
        result = tokenize_line('TITLE="a  b   c"')
        assert result == ['TITLE="a  b   c"']

    def test_adjacent_quoted_values(self):
        """Two quoted values adjacent with single space separator."""
        result = tokenize_line('A="x" B="y"')
        assert result == ['A="x"', 'B="y"']

    def test_unclosed_quote_treated_as_quoted(self):
        """Unclosed quote swallows remaining input into one token."""
        result = tokenize_line('KEY="unclosed value')
        assert result == ['KEY="unclosed value']

    def test_alternating_quotes(self):
        """Double quotes inside single-quoted value."""
        result = tokenize_line("""MSG='say "hello"'""")
        assert result == ["""MSG='say "hello"'"""]

    def test_leading_and_trailing_whitespace(self):
        """Leading and trailing whitespace is ignored."""
        assert tokenize_line("  A=1 B=2  ") == ["A=1", "B=2"]

    def test_multiple_spaces_between_tokens(self):
        """Multiple spaces between tokens collapsed."""
        assert tokenize_line("A=1   B=2") == ["A=1", "B=2"]

    def test_empty_quotes_preserved(self):
        """Empty quoted string preserved as token content."""
        assert tokenize_line('KEY=""') == ['KEY=""']
