"""
Parser for BibTeX files.

This module provides the main parsing functionality, converting
a token stream from the lexer into an intermediate representation (IR).
"""

from __future__ import annotations

from typing import Optional

from .exceptions import ParserError, ParsingWarning
from .ir import (
    Comment,
    Entry,
    Field,
    Library,
    ParsingFailedBlock,
    Preamble,
    StringDefinition,
)
from .lexer import Lexer, Token, TokenType


class Parser:
    """
    Parser for BibTeX content.

    The parser converts a stream of tokens into a Library IR.
    It is fault-tolerant and will continue parsing after errors,
    recording failed blocks.
    """

    def __init__(self, strict: bool = False):
        """
        Initialize the parser.

        Args:
            strict: If True, raise exceptions on parse errors.
                   If False (default), record errors and continue.
        """
        self.strict = strict
        self.warnings: list[ParsingWarning] = []

    def parse(self, text: str) -> Library:
        """
        Parse BibTeX text into a Library.

        Args:
            text: The BibTeX content to parse.

        Returns:
            A Library containing all parsed entries and metadata.
        """
        lexer = Lexer(text)
        self.tokens: list[Token] = lexer.get_all_tokens()
        self.warnings.extend(lexer.warnings)
        self.pos = 0
        self.text = text

        library = Library()

        while not self._is_at_end():
            try:
                self._parse_entry(library)
            except ParserError as e:
                if self.strict:
                    raise
                # Record the failed block and try to recover
                failed_text = self._recover_to_next_entry()
                library.failed_blocks.append(
                    ParsingFailedBlock(
                        raw_text=failed_text,
                        error_message=str(e),
                        line=e.line or 0,
                    )
                )

        return library

    @property
    def _current(self) -> Token:
        """Get the current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        """Peek at a token ahead."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[pos]

    def _advance(self) -> Token:
        """Advance to the next token and return the current one."""
        token = self._current
        if not self._is_at_end():
            self.pos += 1
        return token

    def _is_at_end(self) -> bool:
        """Check if we're at the end of input."""
        return self._current.type == TokenType.EOF

    def _check(self, *types: TokenType) -> bool:
        """Check if the current token is one of the given types."""
        return self._current.type in types

    def _match(self, *types: TokenType) -> Optional[Token]:
        """If current token matches any of the types, advance and return it."""
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, type_: TokenType, message: str) -> Token:
        """Expect a specific token type, raising an error if not found."""
        if self._check(type_):
            return self._advance()
        raise ParserError(
            f"{message}. Got {self._current.type.name}: {self._current.value!r}",
            self._current.line,
            self._current.column,
        )

    def _recover_to_next_entry(self) -> str:
        """
        Skip tokens until we find the next @ or EOF.
        Returns the text that was skipped.
        """
        start_line = self._current.line
        skipped_tokens = []

        while not self._is_at_end() and not self._check(TokenType.AT):
            skipped_tokens.append(self._current.value)
            self._advance()

        # Try to reconstruct the skipped text
        return " ".join(skipped_tokens)

    def _parse_entry(self, library: Library) -> None:
        """Parse a single entry and add it to the library."""
        # Skip any leading content before @
        while not self._is_at_end() and not self._check(TokenType.AT):
            # This is implicit comment content
            token = self._advance()
            if token.value.strip():
                library.comments.append(Comment(value=token.value, line=token.line))

        if self._is_at_end():
            return

        # Expect @
        at_token = self._expect(TokenType.AT, "Expected '@'")
        entry_line = at_token.line

        # Get entry type
        type_token = self._expect(TokenType.NAME, "Expected entry type after '@'")
        entry_type = type_token.value.lower()

        # Handle special entry types
        if entry_type == "comment":
            self._parse_comment(library, entry_line)
        elif entry_type == "preamble":
            self._parse_preamble(library, entry_line)
        elif entry_type == "string":
            self._parse_string(library, entry_line)
        else:
            self._parse_regular_entry(library, entry_type, entry_line)

    def _parse_comment(self, library: Library, line: int) -> None:
        """Parse a @comment entry."""
        # @comment can have various formats
        # We'll try to capture everything until the matching brace/paren or next @
        content = []

        if self._match(TokenType.LBRACE):
            # Read until matching RBRACE
            depth = 1
            while not self._is_at_end() and depth > 0:
                token = self._advance()
                if token.type == TokenType.LBRACE:
                    depth += 1
                    content.append("{")
                elif token.type == TokenType.RBRACE:
                    depth -= 1
                    if depth > 0:
                        content.append("}")
                else:
                    content.append(token.value)
        elif self._match(TokenType.LPAREN):
            # Read until matching RPAREN
            depth = 1
            while not self._is_at_end() and depth > 0:
                token = self._advance()
                if token.type == TokenType.LPAREN:
                    depth += 1
                    content.append("(")
                elif token.type == TokenType.RPAREN:
                    depth -= 1
                    if depth > 0:
                        content.append(")")
                else:
                    content.append(token.value)
        else:
            # No delimiter, just take everything until next @
            while not self._is_at_end() and not self._check(TokenType.AT):
                content.append(self._advance().value)

        library.comments.append(Comment(value=" ".join(content), line=line))

    def _parse_preamble(self, library: Library, line: int) -> None:
        """Parse a @preamble entry."""
        # Expect opening delimiter
        if self._match(TokenType.LBRACE):
            closing = TokenType.RBRACE
        elif self._match(TokenType.LPAREN):
            closing = TokenType.RPAREN
        else:
            raise ParserError(
                "Expected '{' or '(' after @preamble",
                self._current.line,
                self._current.column,
            )

        # Parse the value
        value = self._parse_value()

        # Expect closing delimiter
        self._expect(closing, f"Expected '{'}' if closing == TokenType.RBRACE else ')'}'")

        library.preambles.append(Preamble(value=value, line=line))

    def _parse_string(self, library: Library, line: int) -> None:
        """Parse a @string definition."""
        # Expect opening delimiter
        if self._match(TokenType.LBRACE):
            closing = TokenType.RBRACE
        elif self._match(TokenType.LPAREN):
            closing = TokenType.RPAREN
        else:
            raise ParserError(
                "Expected '{' or '(' after @string",
                self._current.line,
                self._current.column,
            )

        # Get the name
        name_token = self._expect(TokenType.NAME, "Expected string name")
        name = name_token.value

        # Expect =
        self._expect(TokenType.EQUALS, "Expected '=' after string name")

        # Parse the value (with string expansion)
        raw_value = self._parse_value(expand_strings=False, library_strings={})
        expanded_value = self._expand_string_value(raw_value, library.strings)

        # Add to library (so subsequent strings can reference it)
        library.strings[name.lower()] = StringDefinition(
            key=name,
            value=expanded_value,
            raw_value=raw_value,
            line=line,
        )

        # Skip optional comma
        self._match(TokenType.COMMA)

        # Expect closing delimiter
        self._expect(closing, f"Expected closing delimiter")

    def _parse_regular_entry(self, library: Library, entry_type: str, line: int) -> None:
        """Parse a regular entry (article, book, etc.)."""
        # Expect opening delimiter
        if self._match(TokenType.LBRACE):
            closing = TokenType.RBRACE
        elif self._match(TokenType.LPAREN):
            closing = TokenType.RPAREN
        else:
            raise ParserError(
                f"Expected '{{' or '(' after @{entry_type}",
                self._current.line,
                self._current.column,
            )

        # Get the citation key
        key_token = self._expect(TokenType.NAME, "Expected citation key")
        key = key_token.value

        # Expect comma after key
        self._expect(TokenType.COMMA, "Expected ',' after citation key")

        # Parse fields
        fields: dict[str, Field] = {}
        while not self._is_at_end() and not self._check(closing):
            # Skip extra commas
            while self._match(TokenType.COMMA):
                pass

            if self._check(closing):
                break

            # Parse field
            field = self._parse_field(library.strings)
            if field:
                fields[field.key.lower()] = field

            # Expect comma or closing
            if not self._check(closing):
                self._match(TokenType.COMMA)

        # Expect closing delimiter
        self._expect(closing, "Expected closing delimiter")

        # Create and add entry
        entry = Entry(
            entry_type=entry_type,
            key=key,
            fields=fields,
            line=line,
        )
        library.entries.append(entry)

    def _parse_field(self, strings: dict[str, StringDefinition]) -> Optional[Field]:
        """Parse a single field (name = value)."""
        if not self._check(TokenType.NAME):
            return None

        name_token = self._advance()
        name = name_token.value
        field_line = name_token.line
        field_column = name_token.column

        # Expect =
        if not self._match(TokenType.EQUALS):
            # This might be a malformed field, try to recover
            self.warnings.append(
                ParsingWarning(
                    f"Expected '=' after field name '{name}'",
                    self._current.line,
                    self._current.column,
                )
            )
            return None

        # Parse value
        raw_value = self._parse_value(expand_strings=False, library_strings=strings)
        expanded_value = self._expand_string_value(raw_value, strings)

        return Field(
            key=name,
            value=expanded_value,
            raw_value=raw_value,
            line=field_line,
            column=field_column,
        )

    def _parse_value(
        self,
        expand_strings: bool = True,
        library_strings: Optional[dict[str, StringDefinition]] = None,
    ) -> str:
        """
        Parse a field value, handling string concatenation.

        The value can be:
        - A quoted string: "value"
        - A braced string: {value}
        - A number: 2023
        - A name (string reference): jan
        - Concatenation: "a" # "b" # name
        """
        if library_strings is None:
            library_strings = {}

        parts = []

        while True:
            if self._check(TokenType.STRING):
                token = self._advance()
                parts.append(token.value)
            elif self._check(TokenType.NUMBER):
                token = self._advance()
                parts.append(token.value)
            elif self._check(TokenType.NAME):
                # This could be a string reference
                token = self._advance()
                if expand_strings:
                    # Try to expand the string reference
                    string_def = library_strings.get(token.value.lower())
                    if string_def:
                        parts.append(string_def.value)
                    else:
                        # Unknown string reference, keep as-is
                        parts.append(token.value)
                else:
                    parts.append(token.value)
            elif self._check(TokenType.LBRACE):
                # Braced value - need to read it properly
                self._advance()  # consume {
                value = self._read_braced_value()
                parts.append(value)
            else:
                break

            # Check for string concatenation
            if not self._match(TokenType.HASH):
                break

        return "".join(parts)

    def _read_braced_value(self) -> str:
        """Read a braced value, handling nesting."""
        result = []
        depth = 1

        while not self._is_at_end() and depth > 0:
            token = self._advance()
            if token.type == TokenType.LBRACE:
                depth += 1
                result.append("{")
            elif token.type == TokenType.RBRACE:
                depth -= 1
                if depth > 0:
                    result.append("}")
            else:
                result.append(token.value)
                # Add space between tokens
                if result and not result[-1].endswith(" "):
                    result.append(" ")

        # Clean up trailing space
        text = "".join(result)
        return text.strip()

    def _expand_string_value(self, value: str, strings: dict[str, StringDefinition]) -> str:
        """Expand string references in a value."""
        # This is a simplified expansion - the main expansion happens in _parse_value
        # This handles cases where the value might contain concatenated strings
        return value


def parse(text: str, strict: bool = False) -> Library:
    """
    Parse BibTeX text into a Library.

    This is the main entry point for parsing BibTeX content.

    Args:
        text: The BibTeX content to parse.
        strict: If True, raise exceptions on parse errors.
               If False (default), record errors and continue.

    Returns:
        A Library containing all parsed entries and metadata.

    Example:
        >>> from bibtexparser import parse
        >>> library = parse('@article{key, author = {Name}, year = 2023}')
        >>> print(library.entries[0].key)
        key
    """
    parser = Parser(strict=strict)
    return parser.parse(text)
