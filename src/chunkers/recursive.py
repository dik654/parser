"""
Recursive character text splitter.
"""

from typing import Any, Callable, List, Optional

from src.chunkers.base import BaseChunker, ChunkerConfig
from src.document import TextChunk


class RecursiveChunker(BaseChunker):
    """
    Recursively split text using a hierarchy of separators.

    This is the recommended chunker for most use cases.
    Compatible with LangChain's RecursiveCharacterTextSplitter.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        keep_separator: bool = True,
        length_function: Optional[Callable[[str], int]] = None,
    ):
        """
        Initialize recursive chunker.

        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to try (in order)
            keep_separator: Whether to keep separators in chunks
            length_function: Function to calculate text length
        """
        config = ChunkerConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators or self.DEFAULT_SEPARATORS,
            keep_separator=keep_separator,
            length_function=length_function,
        )
        super().__init__(config)

    def chunk(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """
        Recursively split text into chunks.

        Args:
            text: Input text to split
            **kwargs: Additional options

        Returns:
            List[TextChunk]: List of text chunks
        """
        if not text:
            return []

        separators = kwargs.get("separators", self.config.separators)
        chunk_texts = self._split_text(text, separators)

        # Convert to TextChunk objects
        chunks = []
        char_pos = 0

        for idx, chunk_text in enumerate(chunk_texts):
            if chunk_text.strip():
                # Find actual position in original text
                start_char = text.find(chunk_text, char_pos)
                if start_char == -1:
                    start_char = char_pos
                end_char = start_char + len(chunk_text)

                chunks.append(
                    self._create_chunk(
                        content=chunk_text,
                        index=idx,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )
                char_pos = start_char + 1

        return chunks

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using separators."""
        if not text:
            return []

        # Check if text is already small enough
        if self._calculate_length(text) <= self.config.chunk_size:
            return [text]

        # Find the best separator
        separator = separators[-1]  # Default to last (most granular)
        new_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = sep
                new_separators = []
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        # Split on the chosen separator
        splits = self._split_on_separator(text, separator)

        # Merge small splits and recursively process large ones
        final_chunks = []
        current_chunk: List[str] = []
        current_length = 0

        for split in splits:
            split_length = self._calculate_length(split)

            # If single split is too large, recursively split it
            if split_length > self.config.chunk_size:
                # First, flush current chunk
                if current_chunk:
                    merged = self._merge_with_separator(current_chunk, separator)
                    final_chunks.append(merged)
                    current_chunk = []
                    current_length = 0

                # Recursively split the large piece
                if new_separators:
                    sub_chunks = self._split_text(split, new_separators)
                    final_chunks.extend(sub_chunks)
                else:
                    # Force split by characters
                    final_chunks.extend(self._force_split(split))
                continue

            # Check if adding this split exceeds chunk size
            sep_length = self._calculate_length(separator) if current_chunk else 0
            if current_length + split_length + sep_length > self.config.chunk_size:
                if current_chunk:
                    merged = self._merge_with_separator(current_chunk, separator)
                    final_chunks.append(merged)

                    # Handle overlap
                    current_chunk, current_length = self._get_overlap_content(
                        current_chunk, separator
                    )

            current_chunk.append(split)
            current_length += split_length + (
                self._calculate_length(separator) if len(current_chunk) > 1 else 0
            )

        # Don't forget the last chunk
        if current_chunk:
            merged = self._merge_with_separator(current_chunk, separator)
            final_chunks.append(merged)

        return final_chunks

    def _split_on_separator(self, text: str, separator: str) -> List[str]:
        """Split text on separator, optionally keeping it."""
        if separator == "":
            return list(text)

        if self.config.keep_separator:
            # Keep separator at end of each split
            parts = text.split(separator)
            result = []
            for i, part in enumerate(parts):
                if i < len(parts) - 1:
                    result.append(part + separator)
                elif part:
                    result.append(part)
            return result
        else:
            return text.split(separator)

    def _merge_with_separator(self, splits: List[str], separator: str) -> str:
        """Merge splits with separator."""
        if self.config.keep_separator:
            # Separator already included
            return "".join(splits)
        return separator.join(splits)

    def _get_overlap_content(
        self, chunks: List[str], separator: str
    ) -> tuple:
        """Get overlapping content from previous chunks."""
        if self.config.chunk_overlap <= 0:
            return [], 0

        overlap_text = ""
        overlap_chunks = []

        for chunk in reversed(chunks):
            potential = self._merge_with_separator([chunk] + overlap_chunks, separator)
            if self._calculate_length(potential) <= self.config.chunk_overlap:
                overlap_chunks.insert(0, chunk)
                overlap_text = potential
            else:
                break

        return overlap_chunks, self._calculate_length(overlap_text)

    def _force_split(self, text: str) -> List[str]:
        """Force split text by character count."""
        chunks = []
        start = 0
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - overlap
            if start <= 0 or end >= len(text):
                break

        return chunks
