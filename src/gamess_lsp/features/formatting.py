"""LSP formatting provider for GAMESS input files.

This module provides document and range formatting for GAMESS input files,
including group indentation, keyword normalization (uppercase), comment
preservation, and $DATA section handling.
"""

from __future__ import annotations

import re
from typing import List

from lsprotocol.types import (
    DocumentFormattingParams,
    DocumentRangeFormattingParams,
    FormattingOptions,
    Position,
    Range,
    TextEdit,
)
from pygls.server import LanguageServer

from ..tokenizer import tokenize_line


class GamessFormattingProvider:
    """Provides formatting for GAMESS input files.

    Handles:
    - Consistent indentation of group bodies
    - Keyword normalization (uppercase group names and keywords)
    - Preservation of comments and blank lines
    - $DATA section content preserved without keyword formatting
    - Range formatting for partial document edits
    """

    def __init__(self, server: LanguageServer) -> None:
        """Initialize the formatting provider.

        Args:
            server: The language server instance.
        """
        self.server = server

    def format_document(self, text: str, params: DocumentFormattingParams) -> List[TextEdit]:
        """Format the entire document.

        Args:
            text: Document text.
            params: Formatting parameters.

        Returns:
            List of text edits to apply.
        """
        options = params.options or FormattingOptions(tab_size=2, insert_spaces=True)
        formatted = self._format_text(text, options)

        if formatted == text:
            return []

        lines = text.splitlines()
        return [
            TextEdit(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=len(lines), character=0),
                ),
                new_text=formatted,
            )
        ]

    def format_range(self, text: str, params: DocumentRangeFormattingParams) -> List[TextEdit]:
        """Format a specific range of the document.

        For range formatting, the provider formats only the selected line range.
        It determines the correct indentation context by scanning from the
        document start so that group nesting is respected.

        Args:
            text: Document text.
            params: Range formatting parameters.

        Returns:
            List of text edits to apply.
        """
        options = params.options or FormattingOptions(tab_size=2, insert_spaces=True)
        all_lines = text.splitlines()

        start_line = params.range.start.line
        end_line = params.range.end.line

        # Clamp to valid range
        start_line = max(0, start_line)
        end_line = min(len(all_lines) - 1, end_line)

        if start_line > end_line:
            return []

        indent_str = " " * options.tab_size if options.insert_spaces else "\t"

        # Compute indent context from the beginning of the document
        # so we know the correct nesting level at the range start.
        indent_level, in_data = self._compute_context_at_line(all_lines, start_line)

        edits: List[TextEdit] = []

        for i in range(start_line, end_line + 1):
            if i >= len(all_lines):
                break

            original = all_lines[i]
            formatted = self._format_line(original, indent_level, in_data, indent_str)

            if formatted != original:
                line_length = len(original)
                edits.append(
                    TextEdit(
                        range=Range(
                            start=Position(line=i, character=0),
                            end=Position(line=i, character=line_length),
                        ),
                        new_text=formatted,
                    )
                )

            # Update context for next line based on this line
            indent_level, in_data = self._update_context(formatted.strip(), indent_level, in_data)

        return edits

    def _format_text(self, text: str, options: FormattingOptions) -> str:
        """Format the full text and return the formatted version.

        Args:
            text: Full document text.
            options: Formatting options.

        Returns:
            Formatted text.
        """
        lines = text.splitlines()
        indent_str = " " * options.tab_size if options.insert_spaces else "\t"
        indent_level = 0
        in_data = False
        data_line_count = 0
        formatted_lines: List[str] = []

        for line in lines:
            stripped = line.strip()

            # Empty lines: preserve as blank
            if not stripped:
                formatted_lines.append("")
                continue

            # Comments: preserve content, strip leading whitespace
            if stripped.startswith("!"):
                formatted_lines.append(stripped)
                continue

            # $END: decrease indent, exit group
            if re.match(r"^\$END\b", stripped, re.IGNORECASE):
                indent_level = max(0, indent_level - 1)
                in_data = False
                data_line_count = 0
                formatted_lines.append(indent_str * indent_level + "$END")
                continue

            # Group start: $GROUPNAME
            group_match = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)\s*(.*)", stripped)
            if group_match:
                group_name = group_match.group(1).upper()
                rest = group_match.group(2).strip()

                formatted_lines.append(indent_str * indent_level + f"${group_name}")
                indent_level += 1

                if group_name == "DATA":
                    in_data = True
                    data_line_count = 0

                if rest:
                    # Handle inline content after group name
                    if rest.upper().startswith("$END"):
                        indent_level = max(0, indent_level - 1)
                        in_data = False
                        formatted_lines.append(indent_str * indent_level + "$END")
                    elif in_data:
                        # Inside $DATA: title/symmetry line
                        data_line_count += 1
                        formatted_lines.append(indent_str * indent_level + rest)
                    else:
                        # Inline keywords after group name
                        formatted_keywords = self._format_keywords(rest)
                        formatted_lines.append(indent_str * indent_level + formatted_keywords)

                continue

            # Inside $DATA group: preserve geometry lines
            if in_data:
                data_line_count += 1
                formatted_lines.append(indent_str * indent_level + stripped)
                continue

            # Regular keyword line inside a group
            if indent_level > 0 and "=" in stripped:
                formatted_keywords = self._format_keywords(stripped)
                formatted_lines.append(indent_str * indent_level + formatted_keywords)
                continue

            # Fallback: preserve stripped content at current indent
            formatted_lines.append(indent_str * indent_level + stripped)

        result = "\n".join(formatted_lines)
        if text.endswith("\n"):
            result += "\n"

        return result

    def _format_line(
        self,
        original_line: str,
        indent_level: int,
        in_data: bool,
        indent_str: str,
    ) -> str:
        """Format a single line with the given context.

        Args:
            original_line: The raw line content.
            indent_level: Current indentation level.
            in_data: Whether we are inside a $DATA group.
            indent_str: Indentation string (spaces or tab).

        Returns:
            Formatted line.
        """
        stripped = original_line.strip()

        if not stripped:
            return ""

        if stripped.startswith("!"):
            return stripped

        # $END
        if re.match(r"^\$END\b", stripped, re.IGNORECASE):
            level = max(0, indent_level - 1)
            return indent_str * level + "$END"

        # Group start
        group_match = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)\s*(.*)", stripped)
        if group_match:
            group_name = group_match.group(1).upper()
            rest = group_match.group(2).strip()
            result = indent_str * indent_level + f"${group_name}"
            if rest:
                if "=" in rest:
                    result += "\n" + indent_str * (indent_level + 1) + self._format_keywords(rest)
                else:
                    result += " " + rest
            return result

        # Inside $DATA: preserve as-is with indent
        if in_data:
            return indent_str * indent_level + stripped

        # Regular keyword line inside a group
        if indent_level > 0 and "=" in stripped:
            return indent_str * indent_level + self._format_keywords(stripped)

        return indent_str * indent_level + stripped

    @staticmethod
    def _compute_context_at_line(lines: List[str], target_line: int) -> tuple[int, bool]:
        """Compute the indentation level and $DATA context at a target line.

        Args:
            lines: All lines in the document.
            target_line: The line index to compute context for.

        Returns:
            Tuple of (indent_level, in_data) at the start of target_line.
        """
        indent_level = 0
        in_data = False

        for i in range(target_line):
            if i >= len(lines):
                break

            stripped = lines[i].strip()
            if not stripped or stripped.startswith("!"):
                continue

            if re.match(r"^\$END\b", stripped, re.IGNORECASE):
                indent_level = max(0, indent_level - 1)
                in_data = False
            else:
                group_match = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)", stripped)
                if group_match:
                    group_name = group_match.group(1).upper()
                    if group_name != "END":
                        indent_level += 1
                        in_data = group_name == "DATA"

        return indent_level, in_data

    @staticmethod
    def _update_context(
        stripped_line: str,
        current_level: int,
        in_data: bool,
    ) -> tuple[int, bool]:
        """Update context after processing a line.

        Args:
            stripped_line: Stripped line content.
            current_level: Current indent level.
            in_data: Whether currently inside $DATA.

        Returns:
            Tuple of (updated_level, updated_in_data).
        """
        if not stripped_line or stripped_line.startswith("!"):
            return current_level, in_data

        if re.match(r"^\$END\b", stripped_line, re.IGNORECASE):
            return max(0, current_level - 1), False

        group_match = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)", stripped_line)
        if group_match:
            group_name = group_match.group(1).upper()
            if group_name != "END":
                return current_level + 1, group_name == "DATA"

        return current_level, in_data

    @staticmethod
    def _format_keywords(line: str) -> str:
        """Format a line of keyword=value pairs.

        Tokenizes the line, normalizes spacing around equals signs,
        and uppercases keyword names.  Handles cases where ``=`` is a
        standalone token (``KEY = VALUE``) by merging with adjacent tokens.

        Args:
            line: Line containing keyword=value pairs.

        Returns:
            Formatted keyword line.
        """
        tokens = tokenize_line(line)

        # Merge standalone '=' tokens with neighbours: KEY = VALUE -> KEY=VALUE
        merged: List[str] = []
        i = 0
        while i < len(tokens):
            if tokens[i] == "=" and merged and i + 1 < len(tokens):
                merged[-1] = merged[-1] + "=" + tokens[i + 1]
                i += 2
            else:
                merged.append(tokens[i])
                i += 1

        formatted_tokens: List[str] = []
        for token in merged:
            if "=" in token:
                key, value = token.split("=", 1)
                key_clean = key.strip().upper()
                val_clean = value.strip()
                # Uppercase value unless it is quoted
                if not (val_clean.startswith('"') or val_clean.startswith("'")):
                    val_clean = val_clean.upper()
                formatted_tokens.append(f"{key_clean}={val_clean}")
            else:
                formatted_tokens.append(token.strip().upper())

        return " ".join(formatted_tokens)


# Alias for convenience
FormattingProvider = GamessFormattingProvider


def get_formatting_provider(server: LanguageServer) -> GamessFormattingProvider:
    """Create a formatting provider instance.

    Args:
        server: The language server instance.

    Returns:
        Formatting provider instance.
    """
    return GamessFormattingProvider(server)
