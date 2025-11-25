"""
Sentence-based text chunker.
"""

import re
from typing import Any, List, Optional

from src.chunkers.base import BaseChunker, ChunkerConfig
from src.document import TextChunk


class SentenceChunker(BaseChunker):
    """
    Split text into chunks based on sentences.

    Groups sentences together until chunk size is reached.
    """

    # Sentence ending patterns
    SENTENCE_ENDINGS = re.compile(
        r"(?<=[.!?])\s+(?=[A-Z가-힣])|"  # Standard sentence end
        r"(?<=[.!?])\s*\n|"  # Sentence end before newline
        r"(?<=\n)\n+"  # Paragraph breaks
    )

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
        min_chunk_size: int = 100,
        min_sentences: int = 1,
        max_sentences: Optional[int] = None,
    ):
        """
        Initialize sentence-based chunker.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of sentences to overlap
            min_chunk_size: Minimum size of each chunk
            min_sentences: Minimum sentences per chunk
            max_sentences: Maximum sentences per chunk (None for unlimited)
        """
        config = ChunkerConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
        )
        super().__init__(config)
        self.min_sentences = min_sentences
        self.max_sentences = max_sentences

    def chunk(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """
        Split text into sentence-based chunks.

        Args:
            text: Input text to split
            **kwargs: Additional options

        Returns:
            List[TextChunk]: List of text chunks
        """
        if not text:
            return []

        # Split into sentences
        sentences = self._split_sentences(text)

        if not sentences:
            return []

        chunk_size = kwargs.get("chunk_size", self.config.chunk_size)

        chunks = []
        current_sentences: List[str] = []
        current_length = 0
        chunk_start = 0
        index = 0
        char_pos = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # Check if adding this sentence exceeds size
            should_create_chunk = False

            if current_sentences:
                if current_length + sentence_length > chunk_size:
                    should_create_chunk = True
                elif self.max_sentences and len(current_sentences) >= self.max_sentences:
                    should_create_chunk = True

            if should_create_chunk and len(current_sentences) >= self.min_sentences:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    self._create_chunk(
                        content=chunk_text,
                        index=index,
                        start_char=chunk_start,
                        end_char=chunk_start + len(chunk_text),
                    )
                )
                index += 1

                # Handle overlap (keep last N sentences)
                overlap_count = self.config.chunk_overlap
                if overlap_count > 0 and overlap_count < len(current_sentences):
                    current_sentences = current_sentences[-overlap_count:]
                    current_length = sum(len(s) + 1 for s in current_sentences)
                    chunk_start = char_pos - current_length
                else:
                    current_sentences = []
                    current_length = 0
                    chunk_start = char_pos

            current_sentences.append(sentence)
            current_length += sentence_length + 1
            char_pos += sentence_length + 1

        # Create final chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(
                self._create_chunk(
                    content=chunk_text,
                    index=index,
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                )
            )

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Use regex to split on sentence boundaries
        sentences = self.SENTENCE_ENDINGS.split(text)
        # Clean up and filter empty sentences
        return [s.strip() for s in sentences if s.strip()]


class ParagraphChunker(BaseChunker):
    """
    Split text into chunks based on paragraphs.

    Groups paragraphs together until chunk size is reached.
    """

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 0,
        min_chunk_size: int = 100,
        min_paragraphs: int = 1,
    ):
        """
        Initialize paragraph-based chunker.

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of paragraphs to overlap
            min_chunk_size: Minimum size of each chunk
            min_paragraphs: Minimum paragraphs per chunk
        """
        config = ChunkerConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
        )
        super().__init__(config)
        self.min_paragraphs = min_paragraphs

    def chunk(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """
        Split text into paragraph-based chunks.

        Args:
            text: Input text to split
            **kwargs: Additional options

        Returns:
            List[TextChunk]: List of text chunks
        """
        if not text:
            return []

        # Split into paragraphs
        paragraphs = self._split_paragraphs(text)

        if not paragraphs:
            return []

        chunk_size = kwargs.get("chunk_size", self.config.chunk_size)

        chunks = []
        current_paragraphs: List[str] = []
        current_length = 0
        chunk_start = 0
        index = 0
        char_pos = 0

        for para in paragraphs:
            para_length = len(para)

            # Check if adding this paragraph exceeds size
            if current_paragraphs and current_length + para_length > chunk_size:
                if len(current_paragraphs) >= self.min_paragraphs:
                    # Create chunk
                    chunk_text = "\n\n".join(current_paragraphs)
                    chunks.append(
                        self._create_chunk(
                            content=chunk_text,
                            index=index,
                            start_char=chunk_start,
                            end_char=chunk_start + len(chunk_text),
                        )
                    )
                    index += 1

                    # Handle overlap
                    overlap_count = self.config.chunk_overlap
                    if overlap_count > 0 and overlap_count < len(current_paragraphs):
                        current_paragraphs = current_paragraphs[-overlap_count:]
                        current_length = sum(len(p) + 2 for p in current_paragraphs)
                    else:
                        current_paragraphs = []
                        current_length = 0

                    chunk_start = char_pos

            current_paragraphs.append(para)
            current_length += para_length + 2
            char_pos += para_length + 2

        # Create final chunk
        if current_paragraphs:
            chunk_text = "\n\n".join(current_paragraphs)
            chunks.append(
                self._create_chunk(
                    content=chunk_text,
                    index=index,
                    start_char=chunk_start,
                    end_char=chunk_start + len(chunk_text),
                )
            )

        return chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines
        paragraphs = re.split(r"\n\s*\n", text)
        # Clean up and filter empty paragraphs
        return [p.strip() for p in paragraphs if p.strip()]
