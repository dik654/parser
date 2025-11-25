"""
AI Document Preprocessing Parser

Parse and preprocess documents for AI/LLM applications.
"""

__version__ = "0.1.0"
__author__ = "AI Document Parser Team"

# Core imports (always available)
from src.document import Document, DocumentMetadata, DocumentType, TextChunk

__all__ = [
    # Core
    "Document",
    "DocumentMetadata",
    "DocumentType",
    "TextChunk",
    # Version
    "__version__",
]

# Optional imports - available when dependencies are installed
try:
    from src.parsers import ParserRegistry
    __all__.append("ParserRegistry")
except ImportError:
    pass

try:
    from src.pipeline import Pipeline, PipelineConfig, BatchProcessor
    __all__.extend(["Pipeline", "PipelineConfig", "BatchProcessor"])
except ImportError:
    pass
