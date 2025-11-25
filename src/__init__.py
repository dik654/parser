"""
AI Document Preprocessing Parser

Parse and preprocess documents for AI/LLM applications.
"""

__version__ = "0.1.0"
__author__ = "AI Document Parser Team"

from src.document import Document, DocumentMetadata, DocumentType, TextChunk
from src.parsers import ParserRegistry
from src.pipeline import Pipeline, PipelineConfig, BatchProcessor

__all__ = [
    # Core
    "Document",
    "DocumentMetadata",
    "DocumentType",
    "TextChunk",
    # Pipeline
    "Pipeline",
    "PipelineConfig",
    "BatchProcessor",
    # Registry
    "ParserRegistry",
    # Version
    "__version__",
]
