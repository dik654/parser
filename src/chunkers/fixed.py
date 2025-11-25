"""
Fixed-size text chunker.
"""

from typing import Any, List, Optional

from src.chunkers.base import BaseChunker, ChunkerConfig
from src.document import TextChunk


class FixedSizeChunker(BaseChunker):
    """
    Split text into fixed-size chunks.

    Splits text based on character count or token count.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function: Optional[callable] = None,
    ):
        """
        Initialize fixed-size chunker.

        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters/tokens to overlap between chunks
            length_function: Function to calculate text length (default: len)
        """
        config = ChunkerConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function,
        )
        super().__init__(config)

    def chunk(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """
        Split text into fixed-size chunks.

        Args:
            text: Input text to split
            **kwargs: Additional options

        Returns:
            List[TextChunk]: List of text chunks
        """
        if not text:
            return []

        chunk_size = kwargs.get("chunk_size", self.config.chunk_size)
        chunk_overlap = kwargs.get("chunk_overlap", self.config.chunk_overlap)

        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = start + chunk_size

            # Don't split in the middle of a word if possible
            if end < len(text):
                # Try to find a space to break at
                space_pos = text.rfind(" ", start, end)
                if space_pos > start + chunk_size // 2:
                    end = space_pos + 1

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

            # Move start position with overlap
            start = end - chunk_overlap

            # Ensure we make progress
            if start <= chunks[-1].start_char if chunks else True:
                start = end

        return chunks


class TokenChunker(BaseChunker):
    """
    Split text into chunks based on token count.

    Uses tiktoken or other tokenizers for accurate token counting.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        encoding: str = "cl100k_base",
        model: Optional[str] = None,
    ):
        """
        Initialize token-based chunker.

        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of tokens to overlap
            encoding: tiktoken encoding name
            model: Model name to get encoding for (overrides encoding)
        """
        self.encoding_name = encoding
        self.model = model
        self._tokenizer = None

        config = ChunkerConfig(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._token_length,
        )
        super().__init__(config)

    @property
    def tokenizer(self):
        """Lazy load tokenizer."""
        if self._tokenizer is None:
            try:
                import tiktoken

                if self.model:
                    self._tokenizer = tiktoken.encoding_for_model(self.model)
                else:
                    self._tokenizer = tiktoken.get_encoding(self.encoding_name)
            except ImportError:
                raise ImportError(
                    "tiktoken is required for token chunking. "
                    "Install with: pip install tiktoken"
                )
        return self._tokenizer

    def _token_length(self, text: str) -> int:
        """Get token count for text."""
        return len(self.tokenizer.encode(text))

    def chunk(self, text: str, **kwargs: Any) -> List[TextChunk]:
        """
        Split text into token-based chunks.

        Args:
            text: Input text to split
            **kwargs: Additional options

        Returns:
            List[TextChunk]: List of text chunks
        """
        if not text:
            return []

        chunk_size = kwargs.get("chunk_size", self.config.chunk_size)
        chunk_overlap = kwargs.get("chunk_overlap", self.config.chunk_overlap)

        # Encode text to tokens
        tokens = self.tokenizer.encode(text)

        if len(tokens) <= chunk_size:
            return [
                self._create_chunk(
                    content=text,
                    index=0,
                    start_char=0,
                    end_char=len(text),
                )
            ]

        chunks = []
        start_token = 0
        index = 0

        while start_token < len(tokens):
            end_token = min(start_token + chunk_size, len(tokens))

            # Decode chunk tokens to text
            chunk_tokens = tokens[start_token:end_token]
            chunk_text = self.tokenizer.decode(chunk_tokens)

            # Calculate character positions (approximate)
            start_char = len(self.tokenizer.decode(tokens[:start_token]))
            end_char = start_char + len(chunk_text)

            if chunk_text.strip():
                chunks.append(
                    self._create_chunk(
                        content=chunk_text,
                        index=index,
                        start_char=start_char,
                        end_char=end_char,
                    )
                )
                index += 1

            # Move with overlap
            start_token = end_token - chunk_overlap

            # Ensure progress
            if end_token >= len(tokens):
                break

        return chunks
