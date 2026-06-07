"""Shared tokenizer for GAMESS keyword/value parsing."""

from typing import List


def tokenize_line(line: str) -> List[str]:
    """Tokenize a line into keyword=value pairs, respecting quoted values.

    Splits on whitespace outside of quotes. Handles both single and
    double quotes, matching the same quote character to close.

    Args:
        line: A string containing keyword=value pairs separated by spaces.

    Returns:
        List of token strings (e.g., ['KEY=VAL', 'NAME="quoted value"']).
    """
    tokens = []
    current = ""
    in_quotes = False
    quote_char = None

    for char in line:
        if char in "\"'":
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
            current += char
        elif char == " " and not in_quotes:
            if current:
                tokens.append(current)
                current = ""
        else:
            current += char

    if current:
        tokens.append(current)

    return tokens
