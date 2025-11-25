"""
Parser registry for automatic parser discovery and selection.
"""

from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from src.document import DocumentType
from src.parsers.base import BaseParser


class ParserRegistry:
    """
    Registry for document parsers.

    Provides automatic parser discovery and selection based on file type.
    """

    _instance: Optional["ParserRegistry"] = None
    _parsers: Dict[str, Type[BaseParser]] = {}
    _extension_mapping: Dict[str, str] = {}

    def __new__(cls) -> "ParserRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(
        cls,
        name: str,
        parser_class: Type[BaseParser],
        extensions: Optional[List[str]] = None,
    ) -> None:
        """
        Register a parser class.

        Args:
            name: Unique name for the parser
            parser_class: Parser class to register
            extensions: List of file extensions this parser handles
        """
        cls._parsers[name] = parser_class

        if extensions:
            for ext in extensions:
                ext = ext.lower().lstrip(".")
                cls._extension_mapping[ext] = name

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister a parser.

        Args:
            name: Name of the parser to remove
        """
        if name in cls._parsers:
            del cls._parsers[name]
            # Remove extension mappings
            cls._extension_mapping = {
                ext: parser_name
                for ext, parser_name in cls._extension_mapping.items()
                if parser_name != name
            }

    @classmethod
    def get_parser(cls, name: str, **kwargs) -> BaseParser:
        """
        Get a parser instance by name.

        Args:
            name: Parser name
            **kwargs: Arguments to pass to parser constructor

        Returns:
            BaseParser: Parser instance

        Raises:
            KeyError: If parser name is not registered
        """
        if name not in cls._parsers:
            raise KeyError(f"Parser '{name}' is not registered")
        return cls._parsers[name](**kwargs)

    @classmethod
    def get_parser_for_file(
        cls,
        file_path: Union[str, Path],
        **kwargs,
    ) -> Optional[BaseParser]:
        """
        Get appropriate parser for a file based on extension.

        Args:
            file_path: Path to the file
            **kwargs: Arguments to pass to parser constructor

        Returns:
            BaseParser: Appropriate parser instance, or None if not found
        """
        path = Path(file_path)
        ext = path.suffix.lower().lstrip(".")

        if ext in cls._extension_mapping:
            parser_name = cls._extension_mapping[ext]
            return cls.get_parser(parser_name, **kwargs)

        return None

    @classmethod
    def get_parser_for_type(
        cls,
        doc_type: DocumentType,
        **kwargs,
    ) -> Optional[BaseParser]:
        """
        Get parser for a specific document type.

        Args:
            doc_type: Document type enum
            **kwargs: Arguments to pass to parser constructor

        Returns:
            BaseParser: Appropriate parser instance, or None if not found
        """
        ext = doc_type.value
        if ext in cls._extension_mapping:
            parser_name = cls._extension_mapping[ext]
            return cls.get_parser(parser_name, **kwargs)
        return None

    @classmethod
    def list_parsers(cls) -> List[str]:
        """
        List all registered parser names.

        Returns:
            List[str]: List of parser names
        """
        return list(cls._parsers.keys())

    @classmethod
    def list_supported_extensions(cls) -> List[str]:
        """
        List all supported file extensions.

        Returns:
            List[str]: List of extensions (without dot)
        """
        return list(cls._extension_mapping.keys())

    @classmethod
    def is_supported(cls, file_path: Union[str, Path]) -> bool:
        """
        Check if a file type is supported.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if supported, False otherwise
        """
        path = Path(file_path)
        ext = path.suffix.lower().lstrip(".")
        return ext in cls._extension_mapping

    @classmethod
    def clear(cls) -> None:
        """Clear all registered parsers."""
        cls._parsers.clear()
        cls._extension_mapping.clear()


def register_parser(
    name: str,
    extensions: Optional[List[str]] = None,
):
    """
    Decorator to register a parser class.

    Usage:
        @register_parser("pdf", extensions=[".pdf"])
        class PDFParser(BaseParser):
            ...

    Args:
        name: Unique name for the parser
        extensions: List of file extensions this parser handles

    Returns:
        Decorator function
    """
    def decorator(cls: Type[BaseParser]) -> Type[BaseParser]:
        ParserRegistry.register(name, cls, extensions)
        return cls
    return decorator
