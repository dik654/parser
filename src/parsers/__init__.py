"""
Document parsers for various file formats.
"""

from src.parsers.base import BaseParser
from src.parsers.registry import ParserRegistry, register_parser

# Import parsers to register them
from src.parsers.pdf import PDFParser
from src.parsers.docx import DOCXParser
from src.parsers.pptx import PPTXParser
from src.parsers.xlsx import XLSXParser
from src.parsers.html import HTMLParser
from src.parsers.markdown import MarkdownParser
from src.parsers.hwpx import HWPXParser
from src.parsers.hwp import HWPParser
from src.parsers.image import ImageParser

__all__ = [
    "BaseParser",
    "ParserRegistry",
    "register_parser",
    "PDFParser",
    "DOCXParser",
    "PPTXParser",
    "XLSXParser",
    "HTMLParser",
    "MarkdownParser",
    "HWPXParser",
    "HWPParser",
    "ImageParser",
]
