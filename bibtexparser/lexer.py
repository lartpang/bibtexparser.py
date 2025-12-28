"""
Lexer (Tokenizer) for BibTeX files.

This module provides lexical analysis for BibTeX content, converting
raw text into a stream of tokens for the parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator, Optional

from .exceptions import LexerError, ParsingWarning


class TokenType(Enum):
    """Types of tokens in BibTeX syntax."""

    AT = auto()  # @
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    LPAREN = auto()  # (
    RPAREN = auto()  # )
    EQUALS = auto()  # =
    COMMA = auto()  # ,
    HASH = auto()  # # (string concatenation)
    STRING = auto()  # Quoted or braced string value
    NAME = auto()  # Identifier (entry type, field name, citation key)
    NUMBER = auto()  # Numeric value
    EOF = auto()  # End of file


@dataclass
class Token:
    """
    A single token from the lexer.

    Attributes:
        type: The type of this token.
        value: The string value of this token.
        line: The line number (1-indexed) where this token starts.
        column: The column number (1-indexed) where this token starts.
    """

    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"


class Lexer:
    """
    Lexical analyzer for BibTeX content.

    The lexer converts raw BibTeX text into a stream of tokens.
    It is fault-tolerant and will skip over invalid characters
    while recording warnings.
    """

    def __init__(self, text: str):
        """
        Initialize the lexer with BibTeX text.

        Args:
            text: The BibTeX content to tokenize.
        """
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.warnings: list[ParsingWarning] = []

    @property
    def current_char(self) -> Optional[str]:
        """Get the current character, or None if at end."""
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def peek(self, offset: int = 1) -> Optional[str]:
        """Peek at a character ahead without advancing."""
        pos = self.pos + offset
        if pos >= len(self.text):
            return None
        return self.text[pos]

    def advance(self) -> Optional[str]:
        """Advance to the next character and return it."""
        char = self.current_char
        if char is not None:
            self.pos += 1
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char

    def skip_whitespace(self) -> None:
        """Skip over whitespace characters."""
        while self.current_char is not None and self.current_char in " \t\n\r":
            self.advance()

    def skip_to_next_at(self) -> str:
        """Skip characters until we find the next @ or EOF. Returns skipped text."""
        start_pos = self.pos
        while self.current_char is not None and self.current_char != "@":
            self.advance()
        return self.text[start_pos : self.pos]

    def read_name(self) -> str:
        """Read an identifier (entry type, field name, or citation key)."""
        result = []
        # BibTeX names can contain letters, digits, and some special chars
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char in "_-:./+'"):
            result.append(self.current_char)
            self.advance()
        return "".join(result)

    def read_number(self) -> str:
        """Read a numeric value."""
        result = []
        while self.current_char is not None and self.current_char.isdigit():
            result.append(self.current_char)
            self.advance()
        return "".join(result)

    def read_braced_string(self) -> str:
        """
        Read a brace-delimited string, handling nested braces.

        Returns the string content WITHOUT the outer braces.
        """
        if self.current_char != "{":
            raise LexerError("Expected '{'", self.line, self.column)

        self.advance()  # consume opening {
        result = []
        brace_depth = 1

        while self.current_char is not None and brace_depth > 0:
            if self.current_char == "{":
                brace_depth += 1
                result.append(self.current_char)
                self.advance()
            elif self.current_char == "}":
                brace_depth -= 1
                if brace_depth > 0:
                    result.append(self.current_char)
                self.advance()
            elif self.current_char == "\\":
                # Handle escape sequences
                result.append(self.current_char)
                self.advance()
                if self.current_char is not None:
                    result.append(self.current_char)
                    self.advance()
            else:
                result.append(self.current_char)
                self.advance()

        return "".join(result)

    def read_quoted_string(self) -> str:
        """
        Read a quote-delimited string.

        Returns the string content WITHOUT the quotes.
        Handles nested braces within the string.
        """
        if self.current_char != '"':
            raise LexerError("Expected '\"'", self.line, self.column)

        self.advance()  # consume opening "
        result = []
        brace_depth = 0

        while self.current_char is not None:
            if self.current_char == "{":
                brace_depth += 1
                result.append(self.current_char)
                self.advance()
            elif self.current_char == "}":
                brace_depth -= 1
                result.append(self.current_char)
                self.advance()
            elif self.current_char == '"' and brace_depth == 0:
                self.advance()  # consume closing "
                break
            elif self.current_char == "\\":
                # Handle escape sequences
                result.append(self.current_char)
                self.advance()
                if self.current_char is not None:
                    result.append(self.current_char)
                    self.advance()
            else:
                result.append(self.current_char)
                self.advance()

        return "".join(result)

    def next_token(self) -> Token:
        """
        Get the next token from the input.

        Returns:
            The next Token, or a Token with type EOF at end of input.
        """
        self.skip_whitespace()

        if self.current_char is None:
            return Token(TokenType.EOF, "", self.line, self.column)

        line = self.line
        column = self.column
        char = self.current_char

        # Single-character tokens
        if char == "@":
            self.advance()
            return Token(TokenType.AT, "@", line, column)
        elif char == "{":
            self.advance()
            return Token(TokenType.LBRACE, "{", line, column)
        elif char == "}":
            self.advance()
            return Token(TokenType.RBRACE, "}", line, column)
        elif char == "(":
            self.advance()
            return Token(TokenType.LPAREN, "(", line, column)
        elif char == ")":
            self.advance()
            return Token(TokenType.RPAREN, ")", line, column)
        elif char == "=":
            self.advance()
            return Token(TokenType.EQUALS, "=", line, column)
        elif char == ",":
            self.advance()
            return Token(TokenType.COMMA, ",", line, column)
        elif char == "#":
            self.advance()
            return Token(TokenType.HASH, "#", line, column)

        # String values
        elif char == '"':
            value = self.read_quoted_string()
            return Token(TokenType.STRING, value, line, column)
        elif char == "{":
            value = self.read_braced_string()
            return Token(TokenType.STRING, value, line, column)

        # Numbers
        elif char.isdigit():
            value = self.read_number()
            return Token(TokenType.NUMBER, value, line, column)

        # Names (identifiers)
        elif char.isalpha() or char == "_":
            value = self.read_name()
            return Token(TokenType.NAME, value, line, column)

        # Unknown character - skip and warn
        else:
            self.warnings.append(ParsingWarning(f"Unexpected character: {char!r}", self.line, self.column))
            self.advance()
            return self.next_token()

    def tokenize(self) -> Iterator[Token]:
        """
        Generate all tokens from the input.

        Yields:
            Token objects until EOF is reached.
        """
        while True:
            token = self.next_token()
            yield token
            if token.type == TokenType.EOF:
                break

    def get_all_tokens(self) -> list[Token]:
        """
        Get all tokens as a list.

        Returns:
            List of all tokens including the final EOF token.
        """
        return list(self.tokenize())
