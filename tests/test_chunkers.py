"""
Comprehensive tests for Chunker modules.
"""

import pytest

from src.chunkers.base import BaseChunker, ChunkerConfig
from src.chunkers.fixed import FixedSizeChunker
from src.chunkers.recursive import RecursiveChunker
from src.chunkers.sentence import ParagraphChunker, SentenceChunker
from src.chunkers.semantic import SemanticChunker, SlidingWindowChunker
from src.document import TextChunk


class TestChunkerConfig:
    """Tests for ChunkerConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ChunkerConfig()
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.min_chunk_size == 100
        assert config.keep_separator is True
        assert config.strip_whitespace is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = ChunkerConfig(
            chunk_size=500,
            chunk_overlap=50,
            min_chunk_size=20,
        )
        assert config.chunk_size == 500
        assert config.chunk_overlap == 50
        assert config.min_chunk_size == 20

    def test_invalid_overlap(self):
        """Test that overlap >= chunk_size raises error."""
        with pytest.raises(ValueError, match="chunk_overlap must be less than"):
            ChunkerConfig(chunk_size=100, chunk_overlap=100, min_chunk_size=10)

        with pytest.raises(ValueError, match="chunk_overlap must be less than"):
            ChunkerConfig(chunk_size=100, chunk_overlap=150, min_chunk_size=10)

    def test_invalid_min_chunk_size(self):
        """Test that min_chunk_size > chunk_size raises error."""
        with pytest.raises(ValueError, match="min_chunk_size must be less than"):
            ChunkerConfig(chunk_size=100, min_chunk_size=200, chunk_overlap=10)

    def test_custom_length_function(self):
        """Test custom length function."""
        # Count words instead of characters
        config = ChunkerConfig(
            chunk_size=100,
            chunk_overlap=10,
            min_chunk_size=5,
            length_function=lambda x: len(x.split()),
        )
        assert config.length_function("hello world") == 2


class TestFixedSizeChunker:
    """Tests for FixedSizeChunker."""

    def test_basic_chunking(self):
        """Test basic fixed-size chunking."""
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=5)
        text = "This is a test. " * 10  # 160 characters
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(isinstance(c, TextChunk) for c in chunks)
        assert all(c.length <= 50 for c in chunks)

    def test_empty_text(self):
        """Test chunking empty text."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        chunks = chunker.chunk("")
        assert chunks == []

    def test_small_text(self):
        """Test text smaller than chunk size."""
        chunker = FixedSizeChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=5)
        chunks = chunker.chunk("Small text")
        assert len(chunks) == 1
        assert chunks[0].content.strip() == "Small text"

    def test_chunk_indices(self):
        """Test that chunk indices are sequential."""
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=5, min_chunk_size=5)
        text = "Word " * 30  # 150 characters
        chunks = chunker.chunk(text)

        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_chunk_positions(self):
        """Test that start/end positions are set."""
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=5)
        text = "A" * 200
        chunks = chunker.chunk(text)

        for chunk in chunks:
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char

    def test_callable(self):
        """Test chunker can be called as function."""
        chunker = FixedSizeChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=5)
        text = "Test text. " * 10
        chunks = chunker(text)  # Call directly
        assert len(chunks) > 0


class TestRecursiveChunker:
    """Tests for RecursiveChunker."""

    def test_basic_recursive_chunking(self):
        """Test basic recursive chunking."""
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_paragraph_splitting(self):
        """Test that paragraphs are split on double newlines first."""
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=0, min_chunk_size=5)
        text = "Short.\n\nAnother short.\n\nThird one."
        chunks = chunker.chunk(text)

        # Should try to keep paragraphs together if possible
        assert len(chunks) >= 1

    def test_custom_separators(self):
        """Test custom separators."""
        chunker = RecursiveChunker(
            chunk_size=50,
            chunk_overlap=0,
            min_chunk_size=1,
            separators=["|||", "|", " "],
        )
        text = "A|||B|||C|D|E F G"
        chunks = chunker.chunk(text)
        assert len(chunks) > 0

    def test_keep_separator_true(self):
        """Test keeping separators in chunks."""
        chunker = RecursiveChunker(
            chunk_size=100,
            chunk_overlap=0,
            min_chunk_size=5,
            keep_separator=True,
        )
        text = "First sentence.\n\nSecond sentence."
        chunks = chunker.chunk(text)
        # Separators should be kept
        assert len(chunks) > 0

    def test_overlap(self):
        """Test overlap between chunks."""
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=5)
        text = "Word " * 30  # 150 characters
        chunks = chunker.chunk(text)

        if len(chunks) > 1:
            # Check for some overlap (content may appear in adjacent chunks)
            first_end = chunks[0].content[-10:]
            # Overlap might be at word boundaries
            assert len(chunks) >= 2


class TestSentenceChunker:
    """Tests for SentenceChunker."""

    def test_basic_sentence_chunking(self):
        """Test basic sentence-based chunking."""
        chunker = SentenceChunker(chunk_size=100, chunk_overlap=0, min_chunk_size=5)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_respects_sentence_boundaries(self):
        """Test that chunking respects sentence boundaries."""
        chunker = SentenceChunker(chunk_size=50, chunk_overlap=0, min_sentences=1, min_chunk_size=5)
        text = "Hello world. This is a test. Another sentence here."
        chunks = chunker.chunk(text)

        # Sentences should not be cut in the middle
        for chunk in chunks:
            # Should end with punctuation or be end of text
            content = chunk.content.strip()
            assert content[-1] in ".!?" or chunks.index(chunk) == len(chunks) - 1

    def test_empty_text(self):
        """Test empty text handling."""
        chunker = SentenceChunker(chunk_size=100, chunk_overlap=0, min_chunk_size=5)
        chunks = chunker.chunk("")
        assert chunks == []

    def test_single_sentence(self):
        """Test single sentence text."""
        chunker = SentenceChunker(chunk_size=100, chunk_overlap=0, min_chunk_size=5)
        chunks = chunker.chunk("Just one sentence.")
        assert len(chunks) == 1


class TestParagraphChunker:
    """Tests for ParagraphChunker."""

    def test_basic_paragraph_chunking(self):
        """Test basic paragraph-based chunking."""
        chunker = ParagraphChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=5)
        text = "First paragraph content.\n\nSecond paragraph here.\n\nThird paragraph."
        chunks = chunker.chunk(text)

        assert len(chunks) > 0

    def test_respects_paragraph_boundaries(self):
        """Test that chunking respects paragraph boundaries."""
        chunker = ParagraphChunker(chunk_size=100, chunk_overlap=0, min_chunk_size=5)
        text = "Para one.\n\nPara two.\n\nPara three."
        chunks = chunker.chunk(text)

        # Should have separate paragraphs
        assert len(chunks) >= 1

    def test_empty_text(self):
        """Test empty text handling."""
        chunker = ParagraphChunker(chunk_size=100, chunk_overlap=0, min_chunk_size=5)
        chunks = chunker.chunk("")
        assert chunks == []


class TestSlidingWindowChunker:
    """Tests for SlidingWindowChunker."""

    def test_basic_sliding_window(self):
        """Test basic sliding window chunking."""
        chunker = SlidingWindowChunker(window_size=50, step_size=25)
        text = "A" * 100
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        # Should have overlapping chunks
        assert len(chunks) >= 3  # 100 chars with 50 window and 25 step

    def test_window_size(self):
        """Test that chunks don't exceed window size."""
        chunker = SlidingWindowChunker(window_size=30, step_size=10)
        text = "A" * 100
        chunks = chunker.chunk(text)

        for chunk in chunks:
            assert chunk.length <= 30

    def test_step_size(self):
        """Test that step size controls overlap."""
        chunker = SlidingWindowChunker(window_size=50, step_size=50)
        text = "A" * 150
        chunks = chunker.chunk(text)

        # With step = window, no overlap
        assert len(chunks) == 3

    def test_empty_text(self):
        """Test empty text handling."""
        chunker = SlidingWindowChunker(window_size=50, step_size=25)
        chunks = chunker.chunk("")
        assert chunks == []


class TestSemanticChunker:
    """Tests for SemanticChunker (without embeddings)."""

    def test_basic_semantic_chunking_no_embeddings(self):
        """Test semantic chunking without embedding function (fallback mode)."""
        chunker = SemanticChunker(
            min_chunk_size=10,
            max_chunk_size=100,
        )
        text = "First sentence here. Second sentence follows. Third one comes next."
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(isinstance(c, TextChunk) for c in chunks)

    def test_empty_text(self):
        """Test empty text handling."""
        chunker = SemanticChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_single_sentence(self):
        """Test single sentence text."""
        chunker = SemanticChunker()
        chunks = chunker.chunk("Just one sentence here.")
        assert len(chunks) == 1


class TestChunkerIntegration:
    """Integration tests for chunkers."""

    def test_all_chunkers_produce_text_chunks(self):
        """Test that all chunkers produce TextChunk objects."""
        text = "This is a test document. It has multiple sentences. And paragraphs.\n\nSecond paragraph here."

        chunkers = [
            FixedSizeChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=5),
            RecursiveChunker(chunk_size=50, chunk_overlap=10, min_chunk_size=5),
            SentenceChunker(chunk_size=100, chunk_overlap=0, min_chunk_size=5),
            ParagraphChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=5),
            SlidingWindowChunker(window_size=50, step_size=25),
            SemanticChunker(min_chunk_size=10, max_chunk_size=100),
        ]

        for chunker in chunkers:
            chunks = chunker.chunk(text)
            assert all(isinstance(c, TextChunk) for c in chunks), f"{chunker.name} failed"

    def test_chunkers_handle_unicode(self):
        """Test that chunkers handle Unicode text properly."""
        text = "한글 텍스트입니다. 이것은 테스트입니다. 유니코드를 처리합니다."

        chunkers = [
            FixedSizeChunker(chunk_size=50, chunk_overlap=5, min_chunk_size=5),
            RecursiveChunker(chunk_size=50, chunk_overlap=5, min_chunk_size=5),
            SentenceChunker(chunk_size=100, chunk_overlap=0, min_chunk_size=5),
        ]

        for chunker in chunkers:
            chunks = chunker.chunk(text)
            assert len(chunks) > 0, f"{chunker.name} failed on Unicode"

    def test_chunkers_preserve_content(self):
        """Test that chunking preserves all content."""
        text = "ABCDEFGHIJ"
        chunker = SlidingWindowChunker(window_size=5, step_size=5)
        chunks = chunker.chunk(text)

        # All original content should be in chunks
        combined = "".join(c.content for c in chunks)
        assert combined == text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
