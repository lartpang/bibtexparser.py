"""
Intermediate Representation (IR) data structures for BibTeX.

This module defines the core data structures that represent a parsed BibTeX library.
These dataclasses form the intermediate representation that sits between the raw
BibTeX text and the formatted output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Field:
    """
    Represents a single field within a BibTeX entry.

    Attributes:
        key: The field name (e.g., 'author', 'title', 'year').
        value: The field value after string expansion.
        raw_value: The original value before string expansion.
        line: Source line number where this field starts.
        column: Source column number where this field starts.
    """

    key: str
    value: str
    raw_value: Optional[str] = None
    line: int = 0
    column: int = 0

    def __post_init__(self):
        if self.raw_value is None:
            self.raw_value = self.value


@dataclass
class Entry:
    """
    Represents a BibTeX entry (e.g., @article, @book).

    Attributes:
        entry_type: The type of entry (e.g., 'article', 'book', 'inproceedings').
        key: The citation key used to reference this entry.
        fields: Dictionary of field name to Field objects.
        line: Source line number where this entry starts.
        raw_text: The original text of this entry (for lossless reconstruction).
    """

    entry_type: str
    key: str
    fields: dict[str, Field] = field(default_factory=dict)
    line: int = 0
    raw_text: str = ""

    def get(self, field_name: str, default: Optional[str] = None) -> Optional[str]:
        """Get the value of a field by name."""
        f = self.fields.get(field_name.lower())
        return f.value if f else default

    def __getitem__(self, field_name: str) -> str:
        """Get the value of a field by name, raising KeyError if not found."""
        f = self.fields.get(field_name.lower())
        if f is None:
            raise KeyError(f"Field '{field_name}' not found in entry '{self.key}'")
        return f.value

    def __contains__(self, field_name: str) -> bool:
        """Check if a field exists in this entry."""
        return field_name.lower() in self.fields


@dataclass
class StringDefinition:
    """
    Represents a @string definition.

    Attributes:
        key: The string abbreviation name.
        value: The expanded value of this string.
        raw_value: The original value before expansion.
        line: Source line number.
    """

    key: str
    value: str
    raw_value: Optional[str] = None
    line: int = 0

    def __post_init__(self):
        if self.raw_value is None:
            self.raw_value = self.value


@dataclass
class Preamble:
    """
    Represents a @preamble entry.

    Attributes:
        value: The preamble content.
        line: Source line number.
    """

    value: str
    line: int = 0


@dataclass
class Comment:
    """
    Represents a @comment entry or implicit comment.

    Attributes:
        value: The comment content.
        line: Source line number.
    """

    value: str
    line: int = 0


@dataclass
class ParsingFailedBlock:
    """
    Represents a block that failed to parse.

    When the parser encounters a section it cannot parse, it captures
    that section as a ParsingFailedBlock and continues parsing.

    Attributes:
        raw_text: The original text that failed to parse.
        error_message: Description of what went wrong.
        line: Source line number where the block starts.
    """

    raw_text: str
    error_message: str
    line: int = 0


@dataclass
class Library:
    """
    Represents an entire BibTeX library/database.

    This is the top-level container that holds all parsed content
    from a BibTeX file.

    Attributes:
        entries: List of successfully parsed entries.
        strings: Dictionary of @string definitions (key -> StringDefinition).
        preambles: List of @preamble entries.
        comments: List of @comment entries.
        failed_blocks: List of blocks that failed to parse.
    """

    entries: list[Entry] = field(default_factory=list)
    strings: dict[str, StringDefinition] = field(default_factory=dict)
    preambles: list[Preamble] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    failed_blocks: list[ParsingFailedBlock] = field(default_factory=list)

    def get_entry(self, key: str) -> Optional[Entry]:
        """Get an entry by its citation key."""
        for entry in self.entries:
            if entry.key == key:
                return entry
        return None

    def __len__(self) -> int:
        """Return the number of entries."""
        return len(self.entries)

    def __iter__(self):
        """Iterate over entries."""
        return iter(self.entries)

    def __contains__(self, key: str) -> bool:
        """Check if an entry with the given key exists."""
        return any(entry.key == key for entry in self.entries)

    def keys(self) -> list[str]:
        """Return all entry citation keys."""
        return [entry.key for entry in self.entries]

    @property
    def has_errors(self) -> bool:
        """Check if there were any parsing failures."""
        return len(self.failed_blocks) > 0
