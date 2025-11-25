"""
AI Document Preprocessing Parser

Parse and preprocess documents for AI/LLM applications.
"""

__version__ = "0.1.0"
__author__ = "AI Document Parser Team"

from src.document import Document, DocumentMetadata, DocumentType, TextChunk

__all__ = [
    "Document",
    "DocumentMetadata",
    "DocumentType",
    "TextChunk",
    "__version__",
]
