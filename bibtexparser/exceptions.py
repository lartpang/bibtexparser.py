"""
Custom exceptions for the BibTeX parser.
"""

from dataclasses import dataclass
from typing import Optional


class BibtexError(Exception):
    """Base exception for all bibtex errors."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
    ):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.line is not None and self.column is not None:
            return f"Line {self.line}, Column {self.column}: {self.message}"
        elif self.line is not None:
            return f"Line {self.line}: {self.message}"
        return self.message


class LexerError(BibtexError):
    """Error during lexical analysis."""

    pass


class ParserError(BibtexError):
    """Error during parsing."""

    pass


class ValidationError(BibtexError):
    """Error during validation."""

    pass


@dataclass
class ParsingWarning:
    """A warning generated during parsing (non-fatal)."""

    message: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"Warning at Line {self.line}, Column {self.column}: {self.message}"
