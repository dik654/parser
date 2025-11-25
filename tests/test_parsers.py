"""
Comprehensive tests for Parser modules.
"""

import tempfile
from pathlib import Path

import pytest

from src.document import Document, DocumentType
from src.parsers.base import BaseParser
from src.parsers.registry import ParserRegistry, register_parser


class TestBaseParser:
    """Tests for BaseParser interface."""

    def test_base_parser_is_abstract(self):
        """Test that BaseParser cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseParser()

    def test_get_extension(self):
        """Test extension extraction helper."""

        class ConcreteParser(BaseParser):
            @property
            def supported_extensions(self):
                return [".txt"]

            def supports(self, source):
                return True

            def parse(self, source, **kwargs):
                return None

        parser = ConcreteParser()
        assert parser._get_extension("test.txt") == ".txt"
        assert parser._get_extension(Path("test.PDF")) == ".pdf"


class TestParserRegistry:
    """Tests for ParserRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        ParserRegistry.clear()

    def test_register_parser(self):
        """Test parser registration."""

        class TestParser(BaseParser):
            @property
            def supported_extensions(self):
                return [".test"]

            def supports(self, source):
                return True

            def parse(self, source, **kwargs):
                return Document(
                    id="test",
                    content="test",
                    doc_type=DocumentType.TEXT,
                )

        ParserRegistry.register("test", TestParser, extensions=["test"])
        assert "test" in ParserRegistry.list_parsers()
        assert "test" in ParserRegistry.list_supported_extensions()

    def test_get_parser(self):
        """Test getting parser by name."""

        class TestParser(BaseParser):
            @property
            def supported_extensions(self):
                return [".test"]

            def supports(self, source):
                return True

            def parse(self, source, **kwargs):
                return Document(
                    id="test",
                    content="test",
                    doc_type=DocumentType.TEXT,
                )

        ParserRegistry.register("test", TestParser, extensions=["test"])
        parser = ParserRegistry.get_parser("test")
        assert isinstance(parser, TestParser)

    def test_get_parser_not_found(self):
        """Test getting non-existent parser."""
        with pytest.raises(KeyError):
            ParserRegistry.get_parser("nonexistent")

    def test_get_parser_for_file(self):
        """Test getting parser by file path."""

        class TxtParser(BaseParser):
            @property
            def supported_extensions(self):
                return [".txt"]

            def supports(self, source):
                return True

            def parse(self, source, **kwargs):
                return Document(
                    id="test",
                    content="test",
                    doc_type=DocumentType.TEXT,
                )

        ParserRegistry.register("txt", TxtParser, extensions=["txt"])
        parser = ParserRegistry.get_parser_for_file("test.txt")
        assert isinstance(parser, TxtParser)

    def test_get_parser_for_file_not_found(self):
        """Test getting parser for unsupported file."""
        result = ParserRegistry.get_parser_for_file("test.xyz")
        assert result is None

    def test_unregister_parser(self):
        """Test parser unregistration."""

        class TestParser(BaseParser):
            @property
            def supported_extensions(self):
                return [".test"]

            def supports(self, source):
                return True

            def parse(self, source, **kwargs):
                return Document(
                    id="test",
                    content="test",
                    doc_type=DocumentType.TEXT,
                )

        ParserRegistry.register("test", TestParser, extensions=["test"])
        assert "test" in ParserRegistry.list_parsers()

        ParserRegistry.unregister("test")
        assert "test" not in ParserRegistry.list_parsers()

    def test_is_supported(self):
        """Test checking if file is supported."""

        class TxtParser(BaseParser):
            @property
            def supported_extensions(self):
                return [".txt"]

            def supports(self, source):
                return True

            def parse(self, source, **kwargs):
                return Document(
                    id="test",
                    content="test",
                    doc_type=DocumentType.TEXT,
                )

        ParserRegistry.register("txt", TxtParser, extensions=["txt"])
        assert ParserRegistry.is_supported("test.txt")
        assert not ParserRegistry.is_supported("test.xyz")

    def test_register_decorator(self):
        """Test register_parser decorator."""

        @register_parser("decorated", extensions=["dec"])
        class DecoratedParser(BaseParser):
            @property
            def supported_extensions(self):
                return [".dec"]

            def supports(self, source):
                return True

            def parse(self, source, **kwargs):
                return Document(
                    id="test",
                    content="test",
                    doc_type=DocumentType.TEXT,
                )

        assert "decorated" in ParserRegistry.list_parsers()
        assert "dec" in ParserRegistry.list_supported_extensions()


class TestMarkdownParser:
    """Tests for MarkdownParser (doesn't require external libs)."""

    def test_markdown_parser_import(self):
        """Test markdown parser can be imported."""
        from src.parsers.markdown import MarkdownParser

        parser = MarkdownParser()
        assert parser.name == "MarkdownParser"

    def test_markdown_parse_string(self):
        """Test parsing markdown string."""
        from src.parsers.markdown import MarkdownParser

        parser = MarkdownParser()
        md_content = "# Title\n\nThis is a paragraph.\n\n## Section\n\nMore content."

        doc = parser.parse(md_content)
        assert doc.content is not None
        assert "Title" in doc.content
        assert "paragraph" in doc.content

    def test_markdown_frontmatter(self):
        """Test parsing YAML frontmatter."""
        from src.parsers.markdown import MarkdownParser

        parser = MarkdownParser()
        md_content = """---
title: Test Title
author: Test Author
---

# Content

Body text here.
"""
        doc = parser.parse(md_content)
        assert doc.metadata.title == "Test Title" or "Test Title" in str(doc.metadata.custom)

    def test_markdown_preserve_structure(self):
        """Test preserving markdown structure."""
        from src.parsers.markdown import MarkdownParser

        parser = MarkdownParser(preserve_structure=True)
        md_content = "# Header\n\nParagraph"
        doc = parser.parse(md_content)
        assert "#" in doc.content or "Header" in doc.content

    def test_markdown_extract_links(self):
        """Test extracting links from markdown."""
        from src.parsers.markdown import MarkdownParser

        parser = MarkdownParser(extract_links=True)
        md_content = "Check [this link](https://example.com) for more."
        doc = parser.parse(md_content)
        assert doc.metadata.custom.get("links") is not None


class TestHTMLParser:
    """Tests for HTMLParser."""

    def test_html_parser_import(self):
        """Test HTML parser can be imported."""
        from src.parsers.html import HTMLParser

        parser = HTMLParser()
        assert parser.name == "HTMLParser"

    def test_html_parse_basic(self):
        """Test basic HTML parsing."""
        pytest.importorskip("bs4")
        from src.parsers.html import HTMLParser

        parser = HTMLParser()
        html = "<html><body><p>Hello World</p></body></html>"
        doc = parser.parse(html)
        assert "Hello World" in doc.content

    def test_html_remove_scripts(self):
        """Test script tag removal."""
        pytest.importorskip("bs4")
        from src.parsers.html import HTMLParser

        parser = HTMLParser(remove_scripts=True)
        html = "<p>Text</p><script>alert('x')</script>"
        doc = parser.parse(html)
        assert "alert" not in doc.content
        assert "Text" in doc.content

    def test_html_remove_styles(self):
        """Test style tag removal."""
        pytest.importorskip("bs4")
        from src.parsers.html import HTMLParser

        parser = HTMLParser(remove_styles=True)
        html = "<p>Text</p><style>.class { color: red; }</style>"
        doc = parser.parse(html)
        assert "color" not in doc.content
        assert "Text" in doc.content

    def test_html_extract_title(self):
        """Test title extraction."""
        pytest.importorskip("bs4")
        from src.parsers.html import HTMLParser

        parser = HTMLParser()
        html = "<html><head><title>Page Title</title></head><body>Content</body></html>"
        doc = parser.parse(html)
        assert doc.metadata.title == "Page Title"

    def test_html_preserve_structure(self):
        """Test structure preservation."""
        pytest.importorskip("bs4")
        from src.parsers.html import HTMLParser

        parser = HTMLParser(preserve_structure=True)
        html = "<h1>Header</h1><p>Paragraph</p><ul><li>Item</li></ul>"
        doc = parser.parse(html)
        assert "Header" in doc.content
        assert "Paragraph" in doc.content


class TestParserSyntax:
    """Tests to verify parser files have correct syntax."""

    def test_pdf_parser_syntax(self):
        """Test PDF parser syntax."""
        from src.parsers.pdf import PDFParser

        parser = PDFParser()
        assert parser.name == "PDFParser"
        assert ".pdf" in parser.supported_extensions

    def test_docx_parser_syntax(self):
        """Test DOCX parser syntax."""
        from src.parsers.docx import DOCXParser

        parser = DOCXParser()
        assert parser.name == "DOCXParser"
        assert ".docx" in parser.supported_extensions

    def test_pptx_parser_syntax(self):
        """Test PPTX parser syntax."""
        from src.parsers.pptx import PPTXParser

        parser = PPTXParser()
        assert parser.name == "PPTXParser"
        assert ".pptx" in parser.supported_extensions

    def test_xlsx_parser_syntax(self):
        """Test XLSX parser syntax."""
        from src.parsers.xlsx import XLSXParser

        parser = XLSXParser()
        assert parser.name == "XLSXParser"
        assert ".xlsx" in parser.supported_extensions

    def test_hwpx_parser_syntax(self):
        """Test HWPX parser syntax."""
        from src.parsers.hwpx import HWPXParser

        parser = HWPXParser()
        assert parser.name == "HWPXParser"
        assert ".hwpx" in parser.supported_extensions

    def test_hwp_parser_syntax(self):
        """Test HWP parser syntax."""
        from src.parsers.hwp import HWPParser

        parser = HWPParser()
        assert parser.name == "HWPParser"
        assert ".hwp" in parser.supported_extensions

    def test_image_parser_syntax(self):
        """Test Image parser syntax."""
        from src.parsers.image import ImageParser

        parser = ImageParser()
        assert parser.name == "ImageParser"
        assert ".png" in parser.supported_extensions
        assert ".jpg" in parser.supported_extensions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
