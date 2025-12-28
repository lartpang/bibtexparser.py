"""Tests for the BibTeX formatters."""

import sys

sys.path.insert(0, "..")  # 将上级目录添加到 sys.path 以导入 bibtexparser

from bibtexparser import parse
from bibtexparser.formatters import (
    AlignedFormatter,
    BibtexFormatter,
    Case,
    CompactFormatter,
    EntryDelimiter,
    FormattingOptions,
    ValueWrapper,
)


class TestFormattingOptions:
    """Test FormattingOptions configuration."""

    def test_default_options(self):
        """Test default formatting options."""
        options = FormattingOptions()

        assert options.indent == 2
        assert options.entry_type_case == Case.LOWER
        assert options.field_name_case == Case.LOWER
        assert options.value_wrapper == ValueWrapper.BRACES
        assert options.trailing_comma is True

    def test_custom_options(self):
        """Test custom formatting options."""
        options = FormattingOptions(
            indent=4,
            entry_type_case=Case.UPPER,
            field_name_case=Case.TITLE,
            value_wrapper=ValueWrapper.QUOTES,
            trailing_comma=False,
        )

        assert options.indent == 4
        assert options.entry_type_case == Case.UPPER
        assert options.field_name_case == Case.TITLE
        assert options.value_wrapper == ValueWrapper.QUOTES
        assert options.trailing_comma is False

    def test_indent_string_spaces(self):
        """Test get_indent_string with spaces."""
        options = FormattingOptions(indent=4)
        assert options.get_indent_string() == "    "

    def test_indent_string_tab(self):
        """Test get_indent_string with tab."""
        options = FormattingOptions(indent=-1)
        assert options.get_indent_string() == "\t"


class TestBibtexFormatter:
    """Test BibtexFormatter functionality."""

    def test_format_simple_entry(self):
        """Test formatting a simple entry."""
        bib = "@article{key, author = {Test Author}, title = {Test Title}}"
        library = parse(bib)
        formatter = BibtexFormatter()
        output = formatter.format(library)

        assert "@article{key," in output
        assert "author = {Test Author}" in output
        assert "title = {Test Title}" in output

    def test_format_entry_type_case_lower(self):
        """Test entry type case formatting (lower)."""
        bib = "@ARTICLE{key, author = {Test}}"
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(entry_type_case=Case.LOWER))
        output = formatter.format(library)

        assert "@article{key," in output

    def test_format_entry_type_case_upper(self):
        """Test entry type case formatting (upper)."""
        bib = "@article{key, author = {Test}}"
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(entry_type_case=Case.UPPER))
        output = formatter.format(library)

        assert "@ARTICLE{key," in output

    def test_format_field_name_case(self):
        """Test field name case formatting."""
        bib = "@article{key, AUTHOR = {Test}}"
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(field_name_case=Case.LOWER))
        output = formatter.format(library)

        assert "author = " in output

    def test_format_value_wrapper_braces(self):
        """Test value wrapper with braces."""
        bib = '@article{key, author = "Test"}'
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(value_wrapper=ValueWrapper.BRACES))
        output = formatter.format(library)

        assert "author = {Test}" in output

    def test_format_value_wrapper_quotes(self):
        """Test value wrapper with quotes."""
        bib = "@article{key, author = {Test}}"
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(value_wrapper=ValueWrapper.QUOTES))
        output = formatter.format(library)

        assert 'author = "Test"' in output

    def test_format_trailing_comma(self):
        """Test trailing comma option."""
        bib = "@article{key, author = {Test}}"
        library = parse(bib)

        # With trailing comma
        formatter = BibtexFormatter(FormattingOptions(trailing_comma=True))
        output = formatter.format(library)
        lines = output.strip().split("\n")
        # Find the author line (last field line before closing brace)
        author_line = [l for l in lines if "author" in l][0]
        assert author_line.strip().endswith(",")

        # Without trailing comma
        formatter = BibtexFormatter(FormattingOptions(trailing_comma=False))
        output = formatter.format(library)
        lines = output.strip().split("\n")
        author_line = [l for l in lines if "author" in l][0]
        assert not author_line.strip().endswith(",")

    def test_format_delimiter_braces(self):
        """Test entry delimiter with braces."""
        bib = "@article(key, author = {Test})"
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(entry_delimiter=EntryDelimiter.BRACES))
        output = formatter.format(library)

        assert "@article{key," in output
        assert output.strip().endswith("}")

    def test_format_delimiter_parens(self):
        """Test entry delimiter with parentheses."""
        bib = "@article{key, author = {Test}}"
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(entry_delimiter=EntryDelimiter.PARENS))
        output = formatter.format(library)

        assert "@article(key," in output
        assert output.strip().endswith(")")


class TestFieldOrdering:
    """Test field ordering in formatter."""

    def test_sort_fields(self):
        """Test alphabetical field sorting."""
        bib = "@article{key, zebra = {Z}, alpha = {A}, beta = {B}}"
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(sort_fields=True))
        output = formatter.format(library)

        # Find field positions
        alpha_pos = output.find("alpha")
        beta_pos = output.find("beta")
        zebra_pos = output.find("zebra")

        assert alpha_pos < beta_pos < zebra_pos

    def test_custom_field_order(self):
        """Test custom field ordering."""
        bib = "@article{key, year = {2023}, author = {Test}, title = {Title}}"
        library = parse(bib)
        formatter = BibtexFormatter(FormattingOptions(field_order=["author", "title", "year"]))
        output = formatter.format(library)

        author_pos = output.find("author")
        title_pos = output.find("title")
        year_pos = output.find("year")

        assert author_pos < title_pos < year_pos


class TestAlignedFormatter:
    """Test AlignedFormatter functionality."""

    def test_value_alignment(self):
        """Test that values are aligned."""
        bib = "@article{key, author = {Test}, title = {Long Title}, y = {2023}}"
        library = parse(bib)
        formatter = AlignedFormatter(indent=2)
        output = formatter.format(library)

        # All = signs should be at the same column
        lines = [l for l in output.split("\n") if "=" in l]
        equals_positions = [l.find("=") for l in lines]

        # All should be at the same position
        assert len(set(equals_positions)) == 1


class TestCompactFormatter:
    """Test CompactFormatter functionality."""

    def test_compact_format(self):
        """Test compact formatting."""
        bib = """
        @article{key,
            author = {Test Author},
            title = {Test Title},
            year = {2023},
        }
        """
        library = parse(bib)
        formatter = CompactFormatter()
        output = formatter.format(library)

        # Should be on a single line
        assert "\n" not in output.strip()
        # Should contain all fields
        assert "author=" in output
        assert "title=" in output
        assert "year=" in output


class TestRoundTrip:
    """Test parsing and re-formatting (round-trip)."""

    def test_simple_roundtrip(self):
        """Test that parse -> format -> parse produces same data."""
        original_bib = "@article{key, author = {Test Author}, year = {2023}}"

        # Parse -> Format -> Parse
        library1 = parse(original_bib)
        formatter = BibtexFormatter()
        formatted = formatter.format(library1)
        library2 = parse(formatted)

        # Should have same entries
        assert len(library1.entries) == len(library2.entries)
        assert library1.entries[0].key == library2.entries[0].key
        assert library1.entries[0].get("author") == library2.entries[0].get("author")
        assert library1.entries[0].get("year") == library2.entries[0].get("year")
