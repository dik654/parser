"""
Base chunker interface for text splitting strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.document import TextChunk


@dataclass
class ChunkerConfig:
    """Configuration for chunking strategies."""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: Optional[int] = None
    separators: List[str] = field(
        default_factory=lambda: ["\n\n", "\n", ". ", " ", ""]
    )
    length_function: Optional[Callable[[str], int]] = None
    keep_separator: bool = True
    strip_whitespace: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        if self.min_chunk_size > self.chunk_size:
            raise ValueError("min_chunk_size must be less than or equal to chunk_size")
        if self.length_function is None:
            self.length_function = len


class BaseChunker(ABC):
    """Abstract base class for all text chunkers."""

    def __init__(self, config: Optional[ChunkerConfig] = None):
        """
        Initialize the chunker.

        Args:
            config: Chunker configuration. Uses defaults if not provided.
        """
        self.config = config or ChunkerConfig()

    @abstractmethod
    def chunk(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """
        Split text into chunks.

        Args:
            text: Input text to split
            **kwargs: Strategy-specific options

        Returns:
            List[TextChunk]: List of text chunks
        """
        pass

    def chunk_with_metadata(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[TextChunk]:
        """
        Split text into chunks with additional metadata.

        Args:
            text: Input text to split
            metadata: Additional metadata to include in each chunk
            **kwargs: Strategy-specific options

        Returns:
            List[TextChunk]: List of text chunks with metadata
        """
        chunks = self.chunk(text, **kwargs)
        if metadata:
            for chunk in chunks:
                chunk.metadata.update(metadata)
        return chunks

    @property
    def name(self) -> str:
        """Get the chunker name."""
        return self.__class__.__name__

    def _calculate_length(self, text: str) -> int:
        """Calculate text length using configured function."""
        if self.config.length_function:
            return self.config.length_function(text)
        return len(text)

    def _create_chunk(
        self,
        content: str,
        index: int,
        start_char: int,
        end_char: int,
        page_number: Optional[int] = None,
        section: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TextChunk:
        """
        Create a TextChunk with given parameters.

        Args:
            content: Chunk content
            index: Chunk index
            start_char: Start character position
            end_char: End character position
            page_number: Optional page number
            section: Optional section name
            metadata: Optional metadata dictionary

        Returns:
            TextChunk: Created chunk object
        """
        if self.config.strip_whitespace:
            content = content.strip()

        return TextChunk(
            content=content,
            index=index,
            start_char=start_char,
            end_char=end_char,
            page_number=page_number,
            section=section,
            metadata=metadata or {},
        )

    def _merge_splits(
        self,
        splits: List[str],
        separator: str,
    ) -> List[str]:
        """
        Merge smaller splits into chunks of appropriate size.

        Args:
            splits: List of text splits
            separator: Separator used between splits

        Returns:
            List[str]: Merged chunks
        """
        chunks = []
        current_chunk: List[str] = []
        current_length = 0

        for split in splits:
            split_length = self._calculate_length(split)

            if current_length + split_length > self.config.chunk_size:
                if current_chunk:
                    chunk_text = separator.join(current_chunk)
                    chunks.append(chunk_text)

                    # Handle overlap
                    if self.config.chunk_overlap > 0:
                        overlap_text = ""
                        for i in range(len(current_chunk) - 1, -1, -1):
                            candidate = separator.join(current_chunk[i:])
                            if self._calculate_length(candidate) <= self.config.chunk_overlap:
                                overlap_text = candidate
                            else:
                                break
                        if overlap_text:
                            current_chunk = [overlap_text]
                            current_length = self._calculate_length(overlap_text)
                        else:
                            current_chunk = []
                            current_length = 0
                    else:
                        current_chunk = []
                        current_length = 0

            current_chunk.append(split)
            current_length += split_length + (
                self._calculate_length(separator) if current_chunk else 0
            )

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        return chunks

    def __call__(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """Allow calling chunker as a function."""
        return self.chunk(text, **kwargs)
