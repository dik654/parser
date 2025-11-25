"""
Comprehensive tests for Document module.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.document import Document, DocumentMetadata, DocumentType, TextChunk


class TestDocumentType:
    """Tests for DocumentType enum."""

    def test_basic_types(self):
        """Test basic document types exist."""
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.DOCX.value == "docx"
        assert DocumentType.PPTX.value == "pptx"
        assert DocumentType.XLSX.value == "xlsx"
        assert DocumentType.HTML.value == "html"
        assert DocumentType.MARKDOWN.value == "markdown"
        assert DocumentType.HWP.value == "hwp"
        assert DocumentType.HWPX.value == "hwpx"
        assert DocumentType.IMAGE.value == "image"
        assert DocumentType.TEXT.value == "text"

    def test_from_extension_common(self):
        """Test extension mapping for common formats."""
        assert DocumentType.from_extension("pdf") == DocumentType.PDF
        assert DocumentType.from_extension(".pdf") == DocumentType.PDF
        assert DocumentType.from_extension("PDF") == DocumentType.PDF
        assert DocumentType.from_extension("docx") == DocumentType.DOCX
        assert DocumentType.from_extension("doc") == DocumentType.DOCX
        assert DocumentType.from_extension("pptx") == DocumentType.PPTX
        assert DocumentType.from_extension("xlsx") == DocumentType.XLSX
        assert DocumentType.from_extension("xls") == DocumentType.XLSX

    def test_from_extension_korean(self):
        """Test extension mapping for Korean formats."""
        assert DocumentType.from_extension("hwp") == DocumentType.HWP
        assert DocumentType.from_extension("hwpx") == DocumentType.HWPX

    def test_from_extension_web(self):
        """Test extension mapping for web formats."""
        assert DocumentType.from_extension("html") == DocumentType.HTML
        assert DocumentType.from_extension("htm") == DocumentType.HTML
        assert DocumentType.from_extension("md") == DocumentType.MARKDOWN
        assert DocumentType.from_extension("markdown") == DocumentType.MARKDOWN

    def test_from_extension_images(self):
        """Test extension mapping for image formats."""
        assert DocumentType.from_extension("png") == DocumentType.IMAGE
        assert DocumentType.from_extension("jpg") == DocumentType.IMAGE
        assert DocumentType.from_extension("jpeg") == DocumentType.IMAGE
        assert DocumentType.from_extension("gif") == DocumentType.IMAGE
        assert DocumentType.from_extension("bmp") == DocumentType.IMAGE
        assert DocumentType.from_extension("tiff") == DocumentType.IMAGE
        assert DocumentType.from_extension("webp") == DocumentType.IMAGE

    def test_from_extension_unknown(self):
        """Test unknown extension returns UNKNOWN."""
        assert DocumentType.from_extension("xyz") == DocumentType.UNKNOWN
        assert DocumentType.from_extension("") == DocumentType.UNKNOWN


class TestDocumentMetadata:
    """Tests for DocumentMetadata dataclass."""

    def test_default_values(self):
        """Test default metadata values."""
        meta = DocumentMetadata()
        assert meta.title is None
        assert meta.author is None
        assert meta.created_at is None
        assert meta.page_count is None
        assert meta.custom == {}

    def test_with_values(self):
        """Test metadata with values."""
        now = datetime.now()
        meta = DocumentMetadata(
            title="Test Document",
            author="Test Author",
            created_at=now,
            page_count=10,
            word_count=1000,
            custom={"key": "value"},
        )
        assert meta.title == "Test Document"
        assert meta.author == "Test Author"
        assert meta.created_at == now
        assert meta.page_count == 10
        assert meta.word_count == 1000
        assert meta.custom["key"] == "value"

    def test_to_dict(self):
        """Test metadata serialization to dict."""
        now = datetime.now()
        meta = DocumentMetadata(
            title="Test",
            author="Author",
            created_at=now,
        )
        data = meta.to_dict()
        assert data["title"] == "Test"
        assert data["author"] == "Author"
        assert data["created_at"] == now.isoformat()

    def test_to_dict_none_values_excluded(self):
        """Test that None values are excluded from dict."""
        meta = DocumentMetadata(title="Test")
        data = meta.to_dict()
        assert "title" in data
        assert "author" not in data or data.get("author") is None


class TestTextChunk:
    """Tests for TextChunk dataclass."""

    def test_basic_chunk(self):
        """Test basic chunk creation."""
        chunk = TextChunk(
            content="Hello World",
            index=0,
            start_char=0,
            end_char=11,
        )
        assert chunk.content == "Hello World"
        assert chunk.index == 0
        assert chunk.start_char == 0
        assert chunk.end_char == 11
        assert chunk.length == 11

    def test_chunk_with_metadata(self):
        """Test chunk with metadata."""
        chunk = TextChunk(
            content="Test content",
            index=1,
            start_char=100,
            end_char=112,
            page_number=5,
            section="Introduction",
            metadata={"custom": "value"},
        )
        assert chunk.page_number == 5
        assert chunk.section == "Introduction"
        assert chunk.metadata["custom"] == "value"

    def test_chunk_to_dict(self):
        """Test chunk serialization."""
        chunk = TextChunk(
            content="Test",
            index=0,
            start_char=0,
            end_char=4,
            page_number=1,
        )
        data = chunk.to_dict()
        assert data["content"] == "Test"
        assert data["index"] == 0
        assert data["length"] == 4
        assert data["page_number"] == 1


class TestDocument:
    """Tests for Document dataclass."""

    def test_basic_document(self):
        """Test basic document creation."""
        doc = Document(
            id="test-123",
            content="This is test content.",
            doc_type=DocumentType.TEXT,
        )
        assert doc.id == "test-123"
        assert doc.content == "This is test content."
        assert doc.doc_type == DocumentType.TEXT
        assert doc.word_count == 4
        assert doc.char_count == 21
        assert doc.chunk_count == 0

    def test_document_with_chunks(self):
        """Test document with chunks."""
        chunks = [
            TextChunk(content="First", index=0, start_char=0, end_char=5),
            TextChunk(content="Second", index=1, start_char=6, end_char=12),
        ]
        doc = Document(
            id="test",
            content="First Second",
            doc_type=DocumentType.TEXT,
            chunks=chunks,
        )
        assert doc.chunk_count == 2

    def test_document_to_dict(self):
        """Test document serialization."""
        doc = Document(
            id="test",
            content="Hello",
            doc_type=DocumentType.PDF,
        )
        data = doc.to_dict()
        assert data["id"] == "test"
        assert data["content"] == "Hello"
        assert data["doc_type"] == "pdf"
        assert data["word_count"] == 1
        assert data["char_count"] == 5

    def test_document_to_json(self):
        """Test JSON serialization."""
        doc = Document(
            id="test",
            content="Test content",
            doc_type=DocumentType.TEXT,
        )
        json_str = doc.to_json()
        parsed = json.loads(json_str)
        assert parsed["id"] == "test"
        assert parsed["content"] == "Test content"

    def test_document_from_dict(self):
        """Test document deserialization from dict."""
        data = {
            "id": "test-id",
            "content": "Test content",
            "doc_type": "pdf",
            "metadata": {"title": "Test Title"},
            "chunks": [],
            "tables": [],
            "images": [],
        }
        doc = Document.from_dict(data)
        assert doc.id == "test-id"
        assert doc.content == "Test content"
        assert doc.doc_type == DocumentType.PDF
        assert doc.metadata.title == "Test Title"

    def test_document_from_json(self):
        """Test document deserialization from JSON."""
        json_str = '{"id": "test", "content": "Hello", "doc_type": "text", "metadata": {}, "chunks": [], "tables": [], "images": []}'
        doc = Document.from_json(json_str)
        assert doc.id == "test"
        assert doc.content == "Hello"
        assert doc.doc_type == DocumentType.TEXT

    def test_document_save_load_json(self):
        """Test saving and loading document as JSON."""
        doc = Document(
            id="save-test",
            content="Content to save",
            doc_type=DocumentType.TEXT,
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            doc.save_json(temp_path)
            loaded = Document.load_json(temp_path)
            assert loaded.id == doc.id
            assert loaded.content == doc.content
            assert loaded.doc_type == doc.doc_type
        finally:
            temp_path.unlink()

    def test_document_save_load_pickle(self):
        """Test saving and loading document as pickle."""
        doc = Document(
            id="pickle-test",
            content="Pickle content",
            doc_type=DocumentType.DOCX,
            raw_content=b"raw bytes",
        )

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            temp_path = Path(f.name)

        try:
            doc.save_pickle(temp_path)
            loaded = Document.load_pickle(temp_path)
            assert loaded.id == doc.id
            assert loaded.content == doc.content
            assert loaded.raw_content == doc.raw_content
        finally:
            temp_path.unlink()

    def test_document_with_tables_and_images(self):
        """Test document with tables and images."""
        doc = Document(
            id="complex",
            content="Document with tables",
            doc_type=DocumentType.PDF,
            tables=[{"page": 1, "data": [["A", "B"], ["1", "2"]]}],
            images=[{"page": 1, "format": "png"}],
        )
        assert len(doc.tables) == 1
        assert len(doc.images) == 1
        assert doc.tables[0]["page"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
