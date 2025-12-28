"""
bibtexparser - A fault-tolerant BibTeX parser with flexible formatting options.
"""

from .formatters import BibtexFormatter, FormattingOptions
from .ir import (
    Comment,
    Entry,
    Field,
    Library,
    ParsingFailedBlock,
    Preamble,
    StringDefinition,
)
from .parser import Parser, parse

__version__ = "0.1.0"
__all__ = [
    # Main API
    "parse",
    "Parser",
    # IR types
    "Library",
    "Entry",
    "Field",
    "StringDefinition",
    "Preamble",
    "Comment",
    "ParsingFailedBlock",
    # Formatters
    "BibtexFormatter",
    "FormattingOptions",
]
