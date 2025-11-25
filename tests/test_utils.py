"""
Comprehensive tests for Utils modules.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.document import Document, DocumentMetadata, DocumentType, TextChunk


class TestFileUtils:
    """Tests for file utility functions."""

    def test_get_document_type(self):
        """Test document type detection from path."""
        from src.utils.file_utils import get_document_type

        assert get_document_type("test.pdf") == DocumentType.PDF
        assert get_document_type("test.docx") == DocumentType.DOCX
        assert get_document_type("test.xlsx") == DocumentType.XLSX
        assert get_document_type("test.hwpx") == DocumentType.HWPX
        assert get_document_type("test.unknown") == DocumentType.UNKNOWN

    def test_is_supported_file(self):
        """Test supported file check."""
        from src.utils.file_utils import is_supported_file

        assert is_supported_file("test.pdf")
        assert is_supported_file("test.docx")
        assert is_supported_file("test.png")
        assert not is_supported_file("test.xyz")

    def test_is_supported_file_custom_types(self):
        """Test supported file check with custom types."""
        from src.utils.file_utils import is_supported_file

        assert is_supported_file("test.txt", supported_types=["txt", "md"])
        assert is_supported_file("test.md", supported_types=["txt", "md"])
        assert not is_supported_file("test.pdf", supported_types=["txt", "md"])

    def test_format_file_size(self):
        """Test file size formatting."""
        from src.utils.file_utils import format_file_size

        assert "B" in format_file_size(100)
        assert "KB" in format_file_size(1024)
        assert "MB" in format_file_size(1024 * 1024)
        assert "GB" in format_file_size(1024 * 1024 * 1024)

    def test_temp_file_manager(self):
        """Test temporary file manager."""
        from src.utils.file_utils import TempFileManager

        with TempFileManager() as manager:
            temp_file = manager.create_temp_file(suffix=".txt", content=b"test")
            assert temp_file.exists()
            assert temp_file.read_bytes() == b"test"

        # File should be cleaned up
        assert not temp_file.exists()

    def test_temp_dir_manager(self):
        """Test temporary directory manager."""
        from src.utils.file_utils import TempFileManager

        with TempFileManager() as manager:
            temp_dir = manager.create_temp_dir()
            assert temp_dir.exists()
            assert temp_dir.is_dir()

        # Directory should be cleaned up
        assert not temp_dir.exists()

    def test_iter_directory(self):
        """Test directory iteration."""
        from src.utils.file_utils import iter_directory

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create test files
            (tmpdir / "test1.txt").touch()
            (tmpdir / "test2.txt").touch()
            (tmpdir / "test3.md").touch()
            (tmpdir / "subdir").mkdir()
            (tmpdir / "subdir" / "test4.txt").touch()

            # Test basic iteration
            files = list(iter_directory(tmpdir, pattern="*.txt", recursive=False))
            assert len(files) == 2

            # Test recursive iteration
            files = list(iter_directory(tmpdir, pattern="*.txt", recursive=True))
            assert len(files) == 3

            # Test extension filter
            files = list(iter_directory(tmpdir, extensions=["md"]))
            assert len(files) == 1


class TestMetadataUtils:
    """Tests for metadata utility functions."""

    def test_metadata_extractor_basic(self):
        """Test basic metadata extraction."""
        from src.utils.metadata import MetadataExtractor

        extractor = MetadataExtractor(detect_language=False, extract_keywords=False)
        doc = Document(
            id="test",
            content="This is a test document with multiple sentences. It has some content.",
            doc_type=DocumentType.TEXT,
        )
        metadata = extractor.extract(doc)

        assert metadata.word_count > 0
        assert metadata.char_count > 0
        assert metadata.sentence_count > 0

    def test_metadata_extractor_keywords(self):
        """Test keyword extraction."""
        from src.utils.metadata import MetadataExtractor

        extractor = MetadataExtractor(extract_keywords=True, max_keywords=5)
        doc = Document(
            id="test",
            content="Python programming language is great. Python is used for data science. Python code is readable.",
            doc_type=DocumentType.TEXT,
        )
        metadata = extractor.extract(doc)

        assert len(metadata.keywords) > 0
        assert len(metadata.keywords) <= 5

    def test_reading_time(self):
        """Test reading time calculation."""
        from src.utils.metadata import MetadataExtractor

        extractor = MetadataExtractor()
        # ~200 words = ~1 minute reading time
        words = "word " * 200
        doc = Document(
            id="test",
            content=words,
            doc_type=DocumentType.TEXT,
        )
        metadata = extractor.extract(doc)

        assert 0.9 <= metadata.reading_time_minutes <= 1.1

    def test_merge_metadata(self):
        """Test metadata merging."""
        from src.utils.metadata import merge_metadata

        meta1 = DocumentMetadata(title="Title1", author="Author1")
        meta2 = DocumentMetadata(author="Author2", word_count=100)

        merged = merge_metadata(meta1, meta2)
        assert merged.title == "Title1"  # From meta1
        assert merged.author == "Author2"  # Overwritten by meta2
        assert merged.word_count == 100  # From meta2


class TestFormatters:
    """Tests for output formatters."""

    def test_json_formatter(self):
        """Test JSON formatter."""
        from src.utils.formatters import JSONFormatter

        formatter = JSONFormatter(indent=2)
        doc = Document(
            id="test",
            content="Test content",
            doc_type=DocumentType.TEXT,
        )
        result = formatter.format(doc)

        parsed = json.loads(result)
        assert parsed["id"] == "test"
        assert parsed["content"] == "Test content"

    def test_json_formatter_many(self):
        """Test JSON formatter with multiple documents."""
        from src.utils.formatters import JSONFormatter

        formatter = JSONFormatter()
        docs = [
            Document(id="1", content="First", doc_type=DocumentType.TEXT),
            Document(id="2", content="Second", doc_type=DocumentType.TEXT),
        ]
        result = formatter.format_many(docs)

        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["id"] == "1"
        assert parsed[1]["id"] == "2"

    def test_jsonl_formatter(self):
        """Test JSONL formatter."""
        from src.utils.formatters import JSONLFormatter

        formatter = JSONLFormatter()
        docs = [
            Document(id="1", content="First", doc_type=DocumentType.TEXT),
            Document(id="2", content="Second", doc_type=DocumentType.TEXT),
        ]
        result = formatter.format_many(docs)

        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["id"] == "1"
        assert json.loads(lines[1])["id"] == "2"

    def test_csv_formatter(self):
        """Test CSV formatter."""
        from src.utils.formatters import CSVFormatter

        formatter = CSVFormatter()
        docs = [
            Document(id="1", content="First doc", doc_type=DocumentType.TEXT),
            Document(id="2", content="Second doc", doc_type=DocumentType.PDF),
        ]
        result = formatter.format(docs)

        assert "id" in result  # Header
        assert "1" in result
        assert "2" in result
        assert "text" in result
        assert "pdf" in result

    def test_langchain_formatter(self):
        """Test LangChain formatter."""
        from src.utils.formatters import LangChainFormatter

        formatter = LangChainFormatter()
        doc = Document(
            id="test",
            content="Test content",
            doc_type=DocumentType.TEXT,
            chunks=[
                TextChunk(content="Chunk 1", index=0, start_char=0, end_char=7),
                TextChunk(content="Chunk 2", index=1, start_char=8, end_char=15),
            ],
        )
        result = formatter.format(doc)

        assert len(result) == 2
        assert result[0]["page_content"] == "Chunk 1"
        assert result[1]["page_content"] == "Chunk 2"
        assert "metadata" in result[0]
        assert result[0]["metadata"]["doc_id"] == "test"

    def test_langchain_formatter_no_chunks(self):
        """Test LangChain formatter without chunks."""
        from src.utils.formatters import LangChainFormatter

        formatter = LangChainFormatter()
        doc = Document(
            id="test",
            content="Full content",
            doc_type=DocumentType.TEXT,
        )
        result = formatter.format(doc)

        assert len(result) == 1
        assert result[0]["page_content"] == "Full content"

    def test_llamaindex_formatter(self):
        """Test LlamaIndex formatter."""
        from src.utils.formatters import LlamaIndexFormatter

        formatter = LlamaIndexFormatter()
        doc = Document(
            id="test",
            content="Test content",
            doc_type=DocumentType.TEXT,
            chunks=[
                TextChunk(content="Chunk 1", index=0, start_char=0, end_char=7),
            ],
        )
        result = formatter.format(doc)

        assert len(result) == 1
        assert result[0]["text"] == "Chunk 1"
        assert "doc_id" in result[0]
        assert "extra_info" in result[0]

    def test_formatter_save(self):
        """Test formatter save to file."""
        from src.utils.formatters import JSONFormatter

        formatter = JSONFormatter()
        doc = Document(
            id="save-test",
            content="Content",
            doc_type=DocumentType.TEXT,
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            formatter.save(doc, temp_path)
            content = temp_path.read_text()
            parsed = json.loads(content)
            assert parsed["id"] == "save-test"
        finally:
            temp_path.unlink()


class TestExtractedMetadata:
    """Tests for ExtractedMetadata dataclass."""

    def test_default_values(self):
        """Test default values."""
        from src.utils.metadata import ExtractedMetadata

        meta = ExtractedMetadata()
        assert meta.title is None
        assert meta.keywords == []
        assert meta.word_count == 0
        assert meta.custom == {}

    def test_with_values(self):
        """Test with values."""
        from src.utils.metadata import ExtractedMetadata

        meta = ExtractedMetadata(
            title="Test",
            keywords=["keyword1", "keyword2"],
            word_count=100,
            reading_time_minutes=0.5,
        )
        assert meta.title == "Test"
        assert len(meta.keywords) == 2
        assert meta.word_count == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
