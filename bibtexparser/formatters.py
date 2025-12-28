"""
Output formatters for BibTeX content.

This module provides various formatting options for outputting
BibTeX libraries back to text format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from .ir import Entry, Field, Library


class Case(Enum):
    """Case options for output formatting."""

    LOWER = "lower"  # article, author
    UPPER = "upper"  # ARTICLE, AUTHOR
    TITLE = "title"  # Article, Author
    PRESERVE = "preserve"  # Keep original case


class ValueWrapper(Enum):
    """How to wrap field values."""

    BRACES = "braces"  # {value}
    QUOTES = "quotes"  # "value"


class EntryDelimiter(Enum):
    """Delimiter style for entries."""

    BRACES = "braces"  # @article{key, ...}
    PARENS = "parens"  # @article(key, ...)


@dataclass
class FormattingOptions:
    """
    Configuration options for BibTeX output formatting.

    Attributes:
        indent: Number of spaces for field indentation (or use tab if negative).
        entry_type_case: Case for entry types (article, ARTICLE, Article).
        field_name_case: Case for field names (author, AUTHOR, Author).
        value_wrapper: How to wrap field values ({} or "").
        entry_delimiter: Delimiter for entries ({} or ()).
        trailing_comma: Whether to add a trailing comma after the last field.
        align_values: Whether to align all = signs vertically.
        align_column: Column position for = when aligning (0 = auto).
        sort_fields: Whether to sort fields alphabetically.
        field_order: Custom field order (fields not in list come after).
        entry_separator: Number of blank lines between entries.
        wrap_width: Maximum line width (0 = no wrapping).
        month_style: How to format months ('numeric', 'short', 'long', 'macro').
    """

    indent: int = 2
    entry_type_case: Case = Case.LOWER
    field_name_case: Case = Case.LOWER
    value_wrapper: ValueWrapper = ValueWrapper.BRACES
    entry_delimiter: EntryDelimiter = EntryDelimiter.BRACES
    trailing_comma: bool = True
    align_values: bool = False
    align_column: int = 0
    sort_fields: bool = False
    field_order: list[str] = field(default_factory=list)
    entry_separator: int = 1
    wrap_width: int = 0
    month_style: str = "preserve"

    def get_indent_string(self) -> str:
        """Get the indentation string."""
        if self.indent < 0:
            return "\t"
        return " " * self.indent


class BibtexFormatter:
    """
    Formatter for outputting BibTeX content.

    This class formats a Library IR into BibTeX text with
    configurable formatting options.
    """

    # Standard abbreviated month macros
    MONTH_MACROS = {
        "1": "jan",
        "2": "feb",
        "3": "mar",
        "4": "apr",
        "5": "may",
        "6": "jun",
        "7": "jul",
        "8": "aug",
        "9": "sep",
        "10": "oct",
        "11": "nov",
        "12": "dec",
        "01": "jan",
        "02": "feb",
        "03": "mar",
        "04": "apr",
        "05": "may",
        "06": "jun",
        "07": "jul",
        "08": "aug",
        "09": "sep",
    }

    MONTH_NAMES = {
        "jan": "January",
        "feb": "February",
        "mar": "March",
        "apr": "April",
        "may": "May",
        "jun": "June",
        "jul": "July",
        "aug": "August",
        "sep": "September",
        "oct": "October",
        "nov": "November",
        "dec": "December",
    }

    def __init__(self, options: Optional[FormattingOptions] = None):
        """
        Initialize the formatter.

        Args:
            options: Formatting options. Uses defaults if not provided.
        """
        self.options = options or FormattingOptions()

    def format(self, library: Library) -> str:
        """
        Format a Library into BibTeX text.

        Args:
            library: The Library to format.

        Returns:
            Formatted BibTeX string.
        """
        parts = []

        # Format @string definitions first
        for string_def in library.strings.values():
            parts.append(self._format_string(string_def.key, string_def.value))

        # Add separator if we had strings
        if parts and library.entries:
            parts.append("")

        # Format preambles
        for preamble in library.preambles:
            parts.append(self._format_preamble(preamble.value))

        # Add separator if we had preambles
        if library.preambles and library.entries:
            parts.append("")

        # Format entries
        entry_separator = "\n" * self.options.entry_separator
        formatted_entries = []
        for entry in library.entries:
            formatted_entries.append(self._format_entry(entry))

        parts.append(entry_separator.join(formatted_entries))

        # Format comments
        for comment in library.comments:
            if comment.value.strip():
                parts.append(self._format_comment(comment.value))

        return "\n".join(parts)

    def format_entry(self, entry: Entry) -> str:
        """
        Format a single entry.

        Args:
            entry: The Entry to format.

        Returns:
            Formatted BibTeX entry string.
        """
        return self._format_entry(entry)

    def _format_entry(self, entry: Entry) -> str:
        """Internal method to format an entry."""
        lines = []

        # Entry type
        entry_type = self._apply_case(entry.entry_type, self.options.entry_type_case)

        # Delimiters
        if self.options.entry_delimiter == EntryDelimiter.BRACES:
            open_delim, close_delim = "{", "}"
        else:
            open_delim, close_delim = "(", ")"

        # Opening line
        lines.append(f"@{entry_type}{open_delim}{entry.key},")

        # Get sorted/ordered fields
        fields = self._order_fields(entry.fields)

        # Calculate alignment if needed
        if self.options.align_values:
            max_name_len = max(len(f.key) for f in fields) if fields else 0
            if self.options.align_column > 0:
                align_col = self.options.align_column
            else:
                align_col = max_name_len
        else:
            align_col = 0

        # Format fields
        indent = self.options.get_indent_string()
        for i, f in enumerate(fields):
            is_last = i == len(fields) - 1
            field_line = self._format_field(f, indent, align_col, is_last)
            lines.append(field_line)

        # Closing line
        lines.append(close_delim)

        return "\n".join(lines)

    def _format_field(self, f: Field, indent: str, align_col: int, is_last: bool) -> str:
        """Format a single field."""
        name = self._apply_case(f.key, self.options.field_name_case)
        value = self._format_value(f.value, f.key)

        # Wrap the value
        if self.options.value_wrapper == ValueWrapper.BRACES:
            wrapped_value = f"{{{value}}}"
        else:
            wrapped_value = f'"{value}"'

        # Handle alignment
        if align_col > 0:
            name_padded = name.ljust(align_col)
            field_str = f"{indent}{name_padded} = {wrapped_value}"
        else:
            field_str = f"{indent}{name} = {wrapped_value}"

        # Add comma
        if is_last and not self.options.trailing_comma:
            return field_str
        return f"{field_str},"

    def _format_value(self, value: str, field_name: str) -> str:
        """Format a field value, applying any transformations."""
        # Handle month formatting
        if field_name.lower() == "month" and self.options.month_style != "preserve":
            value = self._format_month(value)

        return value

    def _format_month(self, value: str) -> str:
        """Format a month value according to options."""
        value_lower = value.lower().strip()

        # Try to find month macro
        month_macro = None
        if value_lower in self.MONTH_MACROS:
            month_macro = self.MONTH_MACROS[value_lower]
        elif value_lower in self.MONTH_NAMES:
            month_macro = value_lower
        else:
            # Try to match full month names
            for macro, name in self.MONTH_NAMES.items():
                if value_lower == name.lower():
                    month_macro = macro
                    break

        if month_macro is None:
            return value  # Can't recognize, preserve as-is

        if self.options.month_style == "macro":
            return month_macro
        elif self.options.month_style == "short":
            return month_macro.capitalize()
        elif self.options.month_style == "long":
            return self.MONTH_NAMES.get(month_macro, value)
        elif self.options.month_style == "numeric":
            for num, mac in self.MONTH_MACROS.items():
                if mac == month_macro and len(num) <= 2:
                    return num.lstrip("0")
            return value
        else:
            return value

    def _order_fields(self, fields: dict[str, Field]) -> list[Field]:
        """Order fields according to options."""
        field_list = list(fields.values())

        if self.options.field_order:
            # Custom order
            ordered = []
            remaining = {f.key.lower(): f for f in field_list}

            for name in self.options.field_order:
                name_lower = name.lower()
                if name_lower in remaining:
                    ordered.append(remaining.pop(name_lower))

            # Add remaining fields
            if self.options.sort_fields:
                remaining_sorted = sorted(remaining.values(), key=lambda f: f.key.lower())
                ordered.extend(remaining_sorted)
            else:
                ordered.extend(remaining.values())

            return ordered

        elif self.options.sort_fields:
            return sorted(field_list, key=lambda f: f.key.lower())

        return field_list

    def _format_string(self, name: str, value: str) -> str:
        """Format a @string definition."""
        entry_type = self._apply_case("string", self.options.entry_type_case)

        if self.options.entry_delimiter == EntryDelimiter.BRACES:
            open_delim, close_delim = "{", "}"
        else:
            open_delim, close_delim = "(", ")"

        if self.options.value_wrapper == ValueWrapper.BRACES:
            wrapped_value = f"{{{value}}}"
        else:
            wrapped_value = f'"{value}"'

        return f"@{entry_type}{open_delim}{name} = {wrapped_value}{close_delim}"

    def _format_preamble(self, value: str) -> str:
        """Format a @preamble entry."""
        entry_type = self._apply_case("preamble", self.options.entry_type_case)

        if self.options.entry_delimiter == EntryDelimiter.BRACES:
            open_delim, close_delim = "{", "}"
        else:
            open_delim, close_delim = "(", ")"

        if self.options.value_wrapper == ValueWrapper.BRACES:
            wrapped_value = f"{{{value}}}"
        else:
            wrapped_value = f'"{value}"'

        return f"@{entry_type}{open_delim}{wrapped_value}{close_delim}"

    def _format_comment(self, value: str) -> str:
        """Format a @comment entry."""
        entry_type = self._apply_case("comment", self.options.entry_type_case)
        return f"@{entry_type}{{{value}}}"

    def _apply_case(self, text: str, case: Case) -> str:
        """Apply case transformation to text."""
        if case == Case.LOWER:
            return text.lower()
        elif case == Case.UPPER:
            return text.upper()
        elif case == Case.TITLE:
            return text.capitalize()
        else:  # PRESERVE
            return text


class CompactFormatter(BibtexFormatter):
    """
    Formatter that produces compact output with minimal whitespace.

    This is useful for reducing file size.
    """

    def __init__(self):
        options = FormattingOptions(
            indent=0,
            trailing_comma=False,
            entry_separator=0,
            align_values=False,
        )
        super().__init__(options)

    def _format_entry(self, entry: Entry) -> str:
        """Format an entry in compact form."""
        entry_type = self._apply_case(entry.entry_type, self.options.entry_type_case)
        fields_str = ", ".join(
            f"{self._apply_case(f.key, self.options.field_name_case)}={{{f.value}}}" for f in entry.fields.values()
        )
        return f"@{entry_type}{{{entry.key}, {fields_str}}}"


class AlignedFormatter(BibtexFormatter):
    """
    Formatter that aligns all equals signs vertically.

    This produces more readable output for human editing.
    """

    def __init__(self, indent: int = 2, field_order: Optional[list[str]] = None):
        options = FormattingOptions(
            indent=indent,
            align_values=True,
            trailing_comma=True,
            field_order=field_order or [],
        )
        super().__init__(options)
