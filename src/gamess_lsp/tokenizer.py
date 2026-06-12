"""Shared tokenizer for GAMESS keyword/value parsing.

Provides both low-level line tokenization and higher-level keyword=value
pair extraction, eliminating duplication between parser and formatter
(issue #66).
"""

from __future__ import annotations

from typing import List, Tuple


def tokenize_line(line: str) -> List[str]:
    """Tokenize a line into keyword=value pairs, respecting quoted values.

    Splits on whitespace outside of quotes. Handles both single and
    double quotes, matching the same quote character to close.

    Args:
        line: A string containing keyword=value pairs separated by spaces.

    Returns:
        List of token strings (e.g., ['KEY=VAL', 'NAME="quoted value"']).
    """
    tokens: List[str] = []
    current = ""
    in_quotes = False
    quote_char: str | None = None

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


def parse_keyword_pairs(line: str) -> List[Tuple[str, str]]:
    """Extract keyword=value pairs from a GAMESS input line.

    Tokenizes the line, merges standalone ``=`` tokens with their
    neighbours (``KEY = VALUE`` -> ``KEY=VALUE``), and returns a list
    of ``(name, value)`` tuples.

    This consolidates the duplicated splitting logic previously found in
    both the parser and the formatter (issue #66).

    Args:
        line: A line containing keyword=value pairs.

    Returns:
        List of (keyword_name, keyword_value) tuples. Keywords without
        an ``=`` sign are returned with an empty value string.
    """
    tokens = tokenize_line(line)

    # Merge standalone '=' tokens with neighbours
    merged: List[str] = []
    i = 0
    while i < len(tokens):
        if tokens[i] == "=" and merged and i + 1 < len(tokens):
            merged[-1] = merged[-1] + "=" + tokens[i + 1]
            i += 2
        else:
            merged.append(tokens[i])
            i += 1

    pairs: List[Tuple[str, str]] = []
    for token in merged:
        if "=" in token:
            key, value = token.split("=", 1)
            pairs.append((key.strip(), value.strip().strip("\"'")))
        else:
            pairs.append((token.strip(), ""))

    return pairs
