"""Tests for the BibTeX lexer."""

import sys

sys.path.insert(0, "..")  # 将上级目录添加到 sys.path 以导入 bibtexparser


from bibtexparser.lexer import Lexer, Token, TokenType


class TestLexerBasics:
    """Test basic lexer functionality."""

    def test_empty_input(self):
        """Test lexing empty input."""
        lexer = Lexer("")
        tokens = lexer.get_all_tokens()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_single_at(self):
        """Test lexing a single @ symbol."""
        lexer = Lexer("@")
        tokens = lexer.get_all_tokens()
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.AT
        assert tokens[1].type == TokenType.EOF

    def test_basic_tokens(self):
        """Test lexing basic token types."""
        lexer = Lexer("@article{key,}")
        tokens = lexer.get_all_tokens()

        expected = [
            TokenType.AT,
            TokenType.NAME,  # article
            TokenType.LBRACE,
            TokenType.NAME,  # key
            TokenType.COMMA,
            TokenType.RBRACE,
            TokenType.EOF,
        ]
        assert [t.type for t in tokens] == expected

    def test_name_values(self):
        """Test that NAME tokens have correct values."""
        lexer = Lexer("@article{my_key123,}")
        tokens = lexer.get_all_tokens()

        names = [t for t in tokens if t.type == TokenType.NAME]
        assert len(names) == 2
        assert names[0].value == "article"
        assert names[1].value == "my_key123"


class TestLexerStrings:
    """Test string handling in the lexer."""

    def test_quoted_string(self):
        """Test lexing quoted strings."""
        lexer = Lexer('author = "John Doe"')
        tokens = lexer.get_all_tokens()

        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "John Doe"

    def test_braced_string(self):
        """Test lexing braced strings."""
        lexer = Lexer("title = {Hello World}")
        tokens = lexer.get_all_tokens()

        # The braced string is read when encountering { in value context
        # The lexer sees LBRACE first, then we need to check parser behavior
        assert TokenType.LBRACE in [t.type for t in tokens]

    def test_nested_braces(self):
        """Test lexing strings with nested braces."""
        lexer = Lexer('title = "{Nested {Braces} Here}"')
        tokens = lexer.get_all_tokens()

        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        assert len(string_tokens) == 1
        assert "{Nested {Braces} Here}" in string_tokens[0].value

    def test_string_with_escape(self):
        """Test lexing strings with escape sequences."""
        lexer = Lexer(r'author = "John \"Jack\" Doe"')
        tokens = lexer.get_all_tokens()

        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        assert len(string_tokens) == 1


class TestLexerNumbers:
    """Test number handling in the lexer."""

    def test_number(self):
        """Test lexing numbers."""
        lexer = Lexer("year = 2023")
        tokens = lexer.get_all_tokens()

        number_tokens = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(number_tokens) == 1
        assert number_tokens[0].value == "2023"


class TestLexerPositions:
    """Test line and column tracking."""

    def test_line_tracking(self):
        """Test that line numbers are tracked correctly."""
        lexer = Lexer("@article\n{key}")
        tokens = lexer.get_all_tokens()

        assert tokens[0].line == 1  # @
        assert tokens[1].line == 1  # article
        assert tokens[2].line == 2  # {
        assert tokens[3].line == 2  # key

    def test_column_tracking(self):
        """Test that column numbers are tracked correctly."""
        lexer = Lexer("@article{key}")
        tokens = lexer.get_all_tokens()

        assert tokens[0].column == 1  # @
        assert tokens[1].column == 2  # article
        assert tokens[2].column == 9  # {


class TestLexerConcatenation:
    """Test string concatenation operator."""

    def test_hash_operator(self):
        """Test lexing the # operator."""
        lexer = Lexer('month = jan # " 15"')
        tokens = lexer.get_all_tokens()

        assert TokenType.HASH in [t.type for t in tokens]
        hash_token = [t for t in tokens if t.type == TokenType.HASH][0]
        assert hash_token.value == "#"


class TestLexerErrorHandling:
    """Test error handling in the lexer."""

    def test_unexpected_character_warning(self):
        """Test that unexpected characters generate warnings."""
        lexer = Lexer("@article§{key}")
        tokens = lexer.get_all_tokens()

        # Should still produce valid tokens
        assert TokenType.AT in [t.type for t in tokens]
        # And generate a warning
        assert len(lexer.warnings) > 0
