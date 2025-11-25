"""
Utility functions and helpers.
"""

from src.utils.file_utils import (
    TempFileManager,
    detect_encoding,
    detect_file_type,
    extract_archive,
    format_file_size,
    get_document_type,
    get_file_size,
    is_supported_file,
    iter_directory,
)
from src.utils.formatters import (
    CSVFormatter,
    JSONFormatter,
    JSONLFormatter,
    LangChainFormatter,
    LlamaIndexFormatter,
)
from src.utils.metadata import (
    ExtractedMetadata,
    MetadataExtractor,
    merge_metadata,
)

__all__ = [
    # File utilities
    "detect_file_type",
    "detect_encoding",
    "get_document_type",
    "is_supported_file",
    "TempFileManager",
    "extract_archive",
    "iter_directory",
    "get_file_size",
    "format_file_size",
    # Formatters
    "JSONFormatter",
    "JSONLFormatter",
    "CSVFormatter",
    "LangChainFormatter",
    "LlamaIndexFormatter",
    # Metadata
    "MetadataExtractor",
    "ExtractedMetadata",
    "merge_metadata",
]
