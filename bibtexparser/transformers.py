"""
Transformers (middleware) for BibTeX Libraries.

This module provides transformation functions that modify a Library IR
after parsing, allowing for normalization, validation, and other processing.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Optional

from .ir import Entry, Field, Library, StringDefinition


class Transformer(ABC):
    """Base class for all transformers."""

    @abstractmethod
    def transform(self, library: Library) -> Library:
        """
        Transform a library and return the modified version.

        Args:
            library: The Library to transform.

        Returns:
            The transformed Library (may be the same instance, modified in-place).
        """
        pass


class StringExpander(Transformer):
    """
    Expands @string references in field values.

    This transformer replaces string abbreviations with their full values.
    """

    def transform(self, library: Library) -> Library:
        strings = library.strings

        for entry in library.entries:
            for field in entry.fields.values():
                field.value = self._expand_value(field.value, strings)

        return library

    def _expand_value(self, value: str, strings: dict[str, StringDefinition]) -> str:
        """Expand string references in a value."""
        # Simple expansion - replaces exact matches
        for key, string_def in strings.items():
            # Use word boundary matching to avoid partial replacements
            pattern = rf"\b{re.escape(key)}\b"
            value = re.sub(pattern, string_def.value, value, flags=re.IGNORECASE)
        return value


class FieldNormalizer(Transformer):
    """
    Normalizes field names to a consistent case.
    """

    def __init__(self, case: str = "lower"):
        """
        Initialize the normalizer.

        Args:
            case: Target case ('lower', 'upper', 'title').
        """
        self.case = case

    def transform(self, library: Library) -> Library:
        for entry in library.entries:
            new_fields = {}
            for field in entry.fields.values():
                new_key = self._apply_case(field.key)
                field.key = new_key
                new_fields[new_key] = field
            entry.fields = new_fields

        return library

    def _apply_case(self, text: str) -> str:
        if self.case == "lower":
            return text.lower()
        elif self.case == "upper":
            return text.upper()
        elif self.case == "title":
            return text.capitalize()
        return text


class PageNormalizer(Transformer):
    """
    Normalizes page ranges to use consistent separators.

    BibTeX standard uses -- (en-dash) for page ranges.
    """

    def __init__(self, separator: str = "--"):
        """
        Initialize the normalizer.

        Args:
            separator: Page range separator (default: '--' for en-dash).
        """
        self.separator = separator

    def transform(self, library: Library) -> Library:
        for entry in library.entries:
            if "pages" in entry.fields:
                field = entry.fields["pages"]
                field.value = self._normalize_pages(field.value)

        return library

    def _normalize_pages(self, value: str) -> str:
        """Normalize page range separators."""
        # Replace various separators with the standard one
        # Handles: 1-10, 1–10, 1—10, 1 - 10, etc.
        value = re.sub(r"\s*[-–—]+\s*", self.separator, value)
        return value


class DuplicateKeyHandler(Transformer):
    """
    Handles duplicate citation keys in a library.
    """

    def __init__(self, strategy: str = "keep_first"):
        """
        Initialize the handler.

        Args:
            strategy: How to handle duplicates:
                - 'keep_first': Keep the first occurrence
                - 'keep_last': Keep the last occurrence
                - 'rename': Rename duplicates with suffix (_1, _2, etc.)
        """
        self.strategy = strategy

    def transform(self, library: Library) -> Library:
        seen: dict[str, int] = {}
        result_entries: list[Entry] = []

        for entry in library.entries:
            key = entry.key
            key_lower = key.lower()

            if key_lower in seen:
                if self.strategy == "keep_first":
                    continue  # Skip this duplicate
                elif self.strategy == "keep_last":
                    # Remove the previous one
                    result_entries = [e for e in result_entries if e.key.lower() != key_lower]
                    result_entries.append(entry)
                    seen[key_lower] = 1
                elif self.strategy == "rename":
                    # Rename with suffix
                    seen[key_lower] += 1
                    entry.key = f"{key}_{seen[key_lower]}"
                    result_entries.append(entry)
            else:
                seen[key_lower] = 1
                result_entries.append(entry)

        library.entries = result_entries
        return library


class FieldFilter(Transformer):
    """
    Filters fields in entries, keeping only specified fields.
    """

    def __init__(
        self,
        include: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
    ):
        """
        Initialize the filter.

        Args:
            include: List of field names to keep (if specified, only these are kept).
            exclude: List of field names to remove.
        """
        self.include = [f.lower() for f in include] if include else None
        self.exclude = [f.lower() for f in exclude] if exclude else []

    def transform(self, library: Library) -> Library:
        for entry in library.entries:
            new_fields = {}
            for key, field in entry.fields.items():
                key_lower = key.lower()

                if self.include is not None:
                    if key_lower not in self.include:
                        continue
                if key_lower in self.exclude:
                    continue

                new_fields[key] = field

            entry.fields = new_fields

        return library


class EntryTypeNormalizer(Transformer):
    """
    Normalizes entry types to a consistent case and handles aliases.
    """

    # Common entry type aliases
    ALIASES = {
        "conference": "inproceedings",
        "electronic": "misc",
        "www": "misc",
        "online": "misc",
    }

    def __init__(self, case: str = "lower", resolve_aliases: bool = True):
        """
        Initialize the normalizer.

        Args:
            case: Target case ('lower', 'upper', 'title').
            resolve_aliases: Whether to resolve entry type aliases.
        """
        self.case = case
        self.resolve_aliases = resolve_aliases

    def transform(self, library: Library) -> Library:
        for entry in library.entries:
            entry_type = entry.entry_type.lower()

            if self.resolve_aliases and entry_type in self.ALIASES:
                entry_type = self.ALIASES[entry_type]

            if self.case == "lower":
                entry.entry_type = entry_type.lower()
            elif self.case == "upper":
                entry.entry_type = entry_type.upper()
            elif self.case == "title":
                entry.entry_type = entry_type.capitalize()

        return library


class LatexEncoder(Transformer):
    """
    Encodes special characters to LaTeX format.
    """

    # Common special characters and their LaTeX equivalents
    ENCODINGS = {
        "ä": '\\"{a}',
        "ö": '\\"{o}',
        "ü": '\\"{u}',
        "Ä": '\\"{A}',
        "Ö": '\\"{O}',
        "Ü": '\\"{U}',
        "ß": "{\\ss}",
        "é": "\\'{e}",
        "è": "\\`{e}",
        "ê": "\\^{e}",
        "á": "\\'{a}",
        "à": "\\`{a}",
        "â": "\\^{a}",
        "ó": "\\'{o}",
        "ò": "\\`{o}",
        "ô": "\\^{o}",
        "ú": "\\'{u}",
        "ù": "\\`{u}",
        "û": "\\^{u}",
        "ñ": "\\~{n}",
        "ç": "\\c{c}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
    }

    def __init__(self, fields: Optional[list[str]] = None):
        """
        Initialize the encoder.

        Args:
            fields: List of field names to encode. If None, encodes all fields.
        """
        self.fields = [f.lower() for f in fields] if fields else None

    def transform(self, library: Library) -> Library:
        for entry in library.entries:
            for key, field in entry.fields.items():
                if self.fields is None or key.lower() in self.fields:
                    field.value = self._encode(field.value)

        return library

    def _encode(self, value: str) -> str:
        """Encode special characters in a value."""
        for char, latex in self.ENCODINGS.items():
            value = value.replace(char, latex)
        return value


def apply_transformers(library: Library, *transformers: Transformer) -> Library:
    """
    Apply multiple transformers to a library in sequence.

    Args:
        library: The Library to transform.
        *transformers: Transformers to apply in order.

    Returns:
        The transformed Library.

    Example:
        >>> library = apply_transformers(
        ...     library,
        ...     FieldNormalizer(),
        ...     PageNormalizer(),
        ...     DuplicateKeyHandler(),
        ... )
    """
    for transformer in transformers:
        library = transformer.transform(library)
    return library
