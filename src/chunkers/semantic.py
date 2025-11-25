"""
Semantic text chunker using embeddings.
"""

from typing import Any, Callable, List, Optional

import numpy as np

from src.chunkers.base import BaseChunker, ChunkerConfig
from src.document import TextChunk


class SemanticChunker(BaseChunker):
    """
    Split text into semantically coherent chunks using embeddings.

    Uses sentence embeddings to find natural breakpoints where
    the topic or meaning changes significantly.
    """

    def __init__(
        self,
        embedding_function: Optional[Callable[[List[str]], List[List[float]]]] = None,
        similarity_threshold: float = 0.5,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
        buffer_size: int = 1,
    ):
        """
        Initialize semantic chunker.

        Args:
            embedding_function: Function that takes list of texts and returns embeddings
            similarity_threshold: Minimum similarity to keep sentences together
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk
            buffer_size: Number of sentences to consider for similarity
        """
        config = ChunkerConfig(
            chunk_size=max_chunk_size,
            min_chunk_size=min_chunk_size,
        )
        super().__init__(config)
        self.embedding_function = embedding_function
        self.similarity_threshold = similarity_threshold
        self.buffer_size = buffer_size

    def chunk(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """
        Split text into semantically coherent chunks.

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

        if len(sentences) <= 1:
            return [
                self._create_chunk(
                    content=text,
                    index=0,
                    start_char=0,
                    end_char=len(text),
                )
            ]

        # Get embeddings if function provided
        if self.embedding_function:
            embeddings = self.embedding_function(sentences)
            breakpoints = self._find_semantic_breakpoints(sentences, embeddings)
        else:
            # Fall back to simple sentence grouping
            breakpoints = self._find_simple_breakpoints(sentences)

        # Create chunks from breakpoints
        return self._create_chunks_from_breakpoints(text, sentences, breakpoints)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re

        # Simple sentence splitting
        pattern = r"(?<=[.!?])\s+(?=[A-Z가-힣])|(?<=\n)\n+"
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    def _find_semantic_breakpoints(
        self,
        sentences: List[str],
        embeddings: List[List[float]],
    ) -> List[int]:
        """Find breakpoints using embedding similarity."""
        breakpoints = []
        embeddings_array = np.array(embeddings)

        for i in range(1, len(sentences)):
            # Get embeddings for buffer around current position
            start_idx = max(0, i - self.buffer_size)
            end_idx = min(len(sentences), i + self.buffer_size)

            # Calculate similarity between adjacent sentence groups
            before_emb = np.mean(embeddings_array[start_idx:i], axis=0)
            after_emb = np.mean(embeddings_array[i:end_idx], axis=0)

            similarity = self._cosine_similarity(before_emb, after_emb)

            # If similarity is below threshold, mark as breakpoint
            if similarity < self.similarity_threshold:
                breakpoints.append(i)

        return breakpoints

    def _find_simple_breakpoints(self, sentences: List[str]) -> List[int]:
        """Find breakpoints based on length only."""
        breakpoints = []
        current_length = 0

        for i, sentence in enumerate(sentences):
            current_length += len(sentence)
            if current_length >= self.config.chunk_size:
                breakpoints.append(i + 1)
                current_length = 0

        return breakpoints

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _create_chunks_from_breakpoints(
        self,
        text: str,
        sentences: List[str],
        breakpoints: List[int],
    ) -> List[TextChunk]:
        """Create TextChunk objects from sentences and breakpoints."""
        chunks = []
        chunk_indices = [0] + breakpoints + [len(sentences)]

        char_pos = 0
        for idx in range(len(chunk_indices) - 1):
            start_sent = chunk_indices[idx]
            end_sent = chunk_indices[idx + 1]

            chunk_sentences = sentences[start_sent:end_sent]
            chunk_text = " ".join(chunk_sentences)

            # Find position in original text
            start_char = text.find(chunk_sentences[0], char_pos) if chunk_sentences else char_pos
            if start_char == -1:
                start_char = char_pos
            end_char = start_char + len(chunk_text)

            if chunk_text.strip():
                chunks.append(
                    self._create_chunk(
                        content=chunk_text,
                        index=idx,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )
            char_pos = end_char

        return chunks


class SlidingWindowChunker(BaseChunker):
    """
    Split text using a sliding window approach.

    Creates overlapping chunks that slide through the text.
    """

    def __init__(
        self,
        window_size: int = 1000,
        step_size: int = 500,
    ):
        """
        Initialize sliding window chunker.

        Args:
            window_size: Size of each window/chunk
            step_size: How much to move the window each step
        """
        overlap = window_size - step_size
        config = ChunkerConfig(
            chunk_size=window_size,
            chunk_overlap=overlap,
        )
        super().__init__(config)
        self.step_size = step_size

    def chunk(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """
        Split text using sliding window.

        Args:
            text: Input text to split
            **kwargs: Additional options

        Returns:
            List[TextChunk]: List of text chunks
        """
        if not text:
            return []

        window_size = kwargs.get("window_size", self.config.chunk_size)
        step_size = kwargs.get("step_size", self.step_size)

        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + window_size, len(text))
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append(
                    self._create_chunk(
                        content=chunk_text,
                        index=index,
                        start_char=start,
                        end_char=end,
                    )
                )
                index += 1

            start += step_size

            # Stop if we've passed the end
            if end >= len(text):
                break

        return chunks
