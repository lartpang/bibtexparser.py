"""Tests for the BibTeX parser."""

import sys

sys.path.insert(0, "..")  # 将上级目录添加到 sys.path 以导入 bibtexparser

import pytest

from bibtexparser import parse
from bibtexparser.ir import Entry, Library
from bibtexparser.parser import Parser


class TestParserBasics:
    """Test basic parser functionality."""

    def test_empty_input(self):
        """Test parsing empty input."""
        library = parse("")
        assert len(library.entries) == 0
        assert len(library.failed_blocks) == 0

    def test_single_entry(self):
        """Test parsing a single entry."""
        bib = """
        @article{key2023,
            author = {John Doe},
            title = {A Great Paper},
            year = 2023,
        }
        """
        library = parse(bib)

        assert len(library.entries) == 1
        entry = library.entries[0]
        assert entry.entry_type == "article"
        assert entry.key == "key2023"
        assert "author" in entry
        assert "title" in entry
        assert "year" in entry

    def test_entry_field_values(self):
        """Test that field values are parsed correctly."""
        bib = """
        @book{mybook,
            author = {Jane Smith},
            title = {The Book Title},
            year = {2022},
            publisher = {Publisher Name},
        }
        """
        library = parse(bib)
        entry = library.entries[0]

        assert entry.get("author") == "Jane Smith"
        assert entry.get("title") == "The Book Title"
        assert entry.get("year") == "2022"
        assert entry.get("publisher") == "Publisher Name"


class TestParserEntryTypes:
    """Test parsing different entry types."""

    @pytest.mark.parametrize(
        "entry_type",
        [
            "article",
            "book",
            "inproceedings",
            "incollection",
            "misc",
            "phdthesis",
            "mastersthesis",
            "techreport",
            "manual",
            "unpublished",
        ],
    )
    def test_standard_entry_types(self, entry_type):
        """Test parsing standard entry types."""
        bib = f"@{entry_type}{{key, author = {{Test}}}}"
        library = parse(bib)

        assert len(library.entries) == 1
        assert library.entries[0].entry_type == entry_type


class TestParserSpecialEntries:
    """Test parsing special entry types (@string, @preamble, @comment)."""

    def test_string_definition(self):
        """Test parsing @string definitions."""
        bib = """
        @string{myjournal = {Journal of Testing}}
        @article{key, journal = myjournal}
        """
        library = parse(bib)

        assert "myjournal" in library.strings
        assert library.strings["myjournal"].value == "Journal of Testing"

    def test_preamble(self):
        """Test parsing @preamble entries."""
        bib = '@preamble{"This is a preamble"}'
        library = parse(bib)

        assert len(library.preambles) == 1

    def test_comment(self):
        """Test parsing @comment entries."""
        bib = "@comment{This is a comment}"
        library = parse(bib)

        assert len(library.comments) >= 1


class TestParserDelimiters:
    """Test different delimiter styles."""

    def test_braces_delimiter(self):
        """Test entries with brace delimiters."""
        bib = "@article{key, author = {Test}}"
        library = parse(bib)
        assert len(library.entries) == 1

    def test_parentheses_delimiter(self):
        """Test entries with parenthesis delimiters."""
        bib = "@article(key, author = {Test})"
        library = parse(bib)
        assert len(library.entries) == 1


class TestParserStringConcatenation:
    """Test string concatenation with #."""

    def test_simple_concatenation(self):
        """Test simple string concatenation."""
        bib = """
        @article{key,
            title = {First} # { Second},
        }
        """
        library = parse(bib)
        entry = library.entries[0]
        # The parser should concatenate the strings
        assert "First" in entry.get("title", "")
        assert "Second" in entry.get("title", "")


class TestParserErrorHandling:
    """Test parser error handling and recovery."""

    def test_malformed_entry_recovery(self):
        """Test that parser recovers from malformed entries."""
        bib = """
        @article{good1, author = {Test1}}
        @article{bad entry with spaces
        @article{good2, author = {Test2}}
        """
        library = parse(bib)

        # Should have parsed at least the good entries
        # and recorded the bad one as a failed block
        assert len(library.entries) >= 1

    def test_missing_comma_tolerance(self):
        """Test tolerance for missing commas."""
        bib = """
        @article{key,
            author = {Test}
            title = {Missing comma above}
        }
        """
        # Should not raise an exception
        library = parse(bib)

    def test_trailing_comma(self):
        """Test that trailing commas are allowed."""
        bib = """
        @article{key,
            author = {Test},
            title = {Title},
        }
        """
        library = parse(bib)
        assert len(library.entries) == 1


class TestParserMultipleEntries:
    """Test parsing multiple entries."""

    def test_multiple_entries(self):
        """Test parsing multiple entries."""
        bib = """
        @article{key1, author = {Author1}}
        @book{key2, author = {Author2}}
        @inproceedings{key3, author = {Author3}}
        """
        library = parse(bib)

        assert len(library.entries) == 3
        assert library.entries[0].key == "key1"
        assert library.entries[1].key == "key2"
        assert library.entries[2].key == "key3"

    def test_entry_access_by_key(self):
        """Test accessing entries by key."""
        bib = """
        @article{mykey, author = {Test}}
        """
        library = parse(bib)

        assert "mykey" in library
        entry = library.get_entry("mykey")
        assert entry is not None
        assert entry.key == "mykey"


class TestParserLibraryMethods:
    """Test Library helper methods."""

    def test_library_len(self):
        """Test Library.__len__."""
        bib = "@article{a,} @book{b,}"
        library = parse(bib)
        assert len(library) == 2

    def test_library_iter(self):
        """Test Library.__iter__."""
        bib = "@article{a,} @book{b,}"
        library = parse(bib)
        keys = [entry.key for entry in library]
        assert keys == ["a", "b"]

    def test_library_contains(self):
        """Test Library.__contains__."""
        bib = "@article{mykey,}"
        library = parse(bib)
        assert "mykey" in library
        assert "otherkey" not in library

    def test_library_keys(self):
        """Test Library.keys()."""
        bib = "@article{a,} @book{b,} @misc{c,}"
        library = parse(bib)
        assert library.keys() == ["a", "b", "c"]

    def test_library_has_errors(self):
        """Test Library.has_errors property."""
        bib = "@article{good,}"
        library = parse(bib)
        assert not library.has_errors


class TestEntryMethods:
    """Test Entry helper methods."""

    def test_entry_get(self):
        """Test Entry.get() method."""
        bib = "@article{key, author = {Test}}"
        library = parse(bib)
        entry = library.entries[0]

        assert entry.get("author") == "Test"
        assert entry.get("missing") is None
        assert entry.get("missing", "default") == "default"

    def test_entry_getitem(self):
        """Test Entry.__getitem__ method."""
        bib = "@article{key, author = {Test}}"
        library = parse(bib)
        entry = library.entries[0]

        assert entry["author"] == "Test"

        with pytest.raises(KeyError):
            _ = entry["missing"]

    def test_entry_contains(self):
        """Test Entry.__contains__ method."""
        bib = "@article{key, author = {Test}}"
        library = parse(bib)
        entry = library.entries[0]

        assert "author" in entry
        assert "AUTHOR" in entry  # Case insensitive
        assert "missing" not in entry
