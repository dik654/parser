"""
Base parser interface for all document parsers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List, Union

from src.document import Document


class BaseParser(ABC):
    """Abstract base class for all document parsers."""

    @abstractmethod
    def parse(
        self,
        source: Union[str, Path, BinaryIO, bytes],
        **kwargs,
    ) -> Document:
        """
        Parse a document and return a Document object.

        Args:
            source: File path, file object, or raw bytes
            **kwargs: Parser-specific options

        Returns:
            Document: Parsed document object

        Raises:
            ParseException: If parsing fails
            UnsupportedFormatException: If format is not supported
        """
        pass

    @abstractmethod
    def supports(self, source: Union[str, Path]) -> bool:
        """
        Check if this parser supports the given file.

        Args:
            source: File path to check

        Returns:
            bool: True if supported, False otherwise
        """
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List[str]: List of extensions (e.g., ['.pdf', '.PDF'])
        """
        pass

    @property
    def name(self) -> str:
        """Get the parser name."""
        return self.__class__.__name__

    def _get_extension(self, source: Union[str, Path]) -> str:
        """Extract file extension from source."""
        if isinstance(source, str):
            source = Path(source)
        return source.suffix.lower()
