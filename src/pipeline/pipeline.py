"""
Main pipeline orchestrator for document processing.
"""

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

from src.chunkers import BaseChunker, RecursiveChunker
from src.document import Document, DocumentType
from src.parsers import BaseParser, ParserRegistry
from src.preprocessors import BasePreprocessor, PreprocessorChain

logger = logging.getLogger(__name__)


class ErrorStrategy(Enum):
    """Strategy for handling errors during processing."""

    RAISE = "raise"  # Raise exception immediately
    SKIP = "skip"  # Skip failed documents, continue processing
    LOG = "log"  # Log error and continue


@dataclass
class PipelineConfig:
    """Configuration for the processing pipeline."""

    # Parser settings
    parser_options: Dict[str, Any] = field(default_factory=dict)

    # Preprocessor settings
    preprocessors: List[BasePreprocessor] = field(default_factory=list)

    # Chunker settings
    chunker: Optional[BaseChunker] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Error handling
    error_strategy: ErrorStrategy = ErrorStrategy.LOG

    # Processing options
    extract_tables: bool = True
    extract_images: bool = False
    ocr_enabled: bool = False
    ocr_language: str = "eng"

    # Callbacks
    on_progress: Optional[Callable[[int, int, str], None]] = None
    on_error: Optional[Callable[[str, Exception], None]] = None
    on_complete: Optional[Callable[[Document], None]] = None


@dataclass
class PipelineResult:
    """Result of pipeline processing."""

    document: Optional[Document]
    success: bool
    error: Optional[str] = None
    source_path: Optional[str] = None
    processing_time: float = 0.0


class Pipeline:
    """
    Document processing pipeline.

    Orchestrates parsing, preprocessing, and chunking of documents.
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize the pipeline.

        Args:
            config: Pipeline configuration
        """
        self.config = config or PipelineConfig()
        self._setup_components()

    def _setup_components(self) -> None:
        """Set up pipeline components based on configuration."""
        # Setup preprocessor chain
        if self.config.preprocessors:
            self.preprocessor_chain = PreprocessorChain(self.config.preprocessors)
        else:
            self.preprocessor_chain = None

        # Setup chunker
        if self.config.chunker:
            self.chunker = self.config.chunker
        else:
            self.chunker = RecursiveChunker(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
            )

    def process(
        self,
        source: Union[str, Path, bytes],
        doc_type: Optional[DocumentType] = None,
        **kwargs: Any,
    ) -> PipelineResult:
        """
        Process a single document through the pipeline.

        Args:
            source: File path or raw bytes
            doc_type: Document type (auto-detected if not provided)
            **kwargs: Additional options passed to parser

        Returns:
            PipelineResult: Processing result
        """
        import time

        start_time = time.time()
        source_path = str(source) if isinstance(source, (str, Path)) else None

        try:
            # Get parser
            parser = self._get_parser(source, doc_type)
            if not parser:
                raise ValueError(f"No parser available for: {source}")

            # Parse document
            parser_options = {**self.config.parser_options, **kwargs}
            if self.config.extract_tables:
                parser_options["extract_tables"] = True
            if self.config.extract_images:
                parser_options["extract_images"] = True
            if self.config.ocr_enabled:
                parser_options["ocr_enabled"] = True
                parser_options["ocr_language"] = self.config.ocr_language

            document = parser.parse(source, **parser_options)

            # Preprocess text
            if self.preprocessor_chain and document.content:
                document.content = self.preprocessor_chain.process(document.content)

            # Chunk text
            if self.chunker and document.content:
                document.chunks = self.chunker.chunk(document.content)

            # Update metadata
            document.metadata.word_count = len(document.content.split())
            document.metadata.char_count = len(document.content)

            processing_time = time.time() - start_time

            # Callback
            if self.config.on_complete:
                self.config.on_complete(document)

            return PipelineResult(
                document=document,
                success=True,
                source_path=source_path,
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)

            logger.error(f"Error processing {source_path}: {error_msg}")

            if self.config.on_error:
                self.config.on_error(source_path or "unknown", e)

            if self.config.error_strategy == ErrorStrategy.RAISE:
                raise

            return PipelineResult(
                document=None,
                success=False,
                error=error_msg,
                source_path=source_path,
                processing_time=processing_time,
            )

    def process_many(
        self,
        sources: List[Union[str, Path]],
        **kwargs: Any,
    ) -> List[PipelineResult]:
        """
        Process multiple documents sequentially.

        Args:
            sources: List of file paths
            **kwargs: Additional options

        Returns:
            List[PipelineResult]: List of processing results
        """
        results = []
        total = len(sources)

        for idx, source in enumerate(sources):
            if self.config.on_progress:
                self.config.on_progress(idx + 1, total, str(source))

            result = self.process(source, **kwargs)
            results.append(result)

        return results

    def _get_parser(
        self,
        source: Union[str, Path, bytes],
        doc_type: Optional[DocumentType] = None,
    ) -> Optional[BaseParser]:
        """Get appropriate parser for the source."""
        if doc_type:
            return ParserRegistry.get_parser_for_type(doc_type)

        if isinstance(source, (str, Path)):
            return ParserRegistry.get_parser_for_file(source)

        return None

    @classmethod
    def from_config(cls, config_path: Union[str, Path]) -> "Pipeline":
        """
        Create pipeline from configuration file.

        Args:
            config_path: Path to YAML or JSON config file

        Returns:
            Pipeline: Configured pipeline instance
        """
        from src.pipeline.config import ConfigLoader

        loader = ConfigLoader()
        settings = loader.load(config_path)
        return settings.to_pipeline()

    def add_preprocessor(self, preprocessor: BasePreprocessor) -> "Pipeline":
        """Add a preprocessor to the chain."""
        if self.preprocessor_chain is None:
            self.preprocessor_chain = PreprocessorChain([preprocessor])
        else:
            self.preprocessor_chain.add(preprocessor)
        return self

    def set_chunker(self, chunker: BaseChunker) -> "Pipeline":
        """Set the chunker for the pipeline."""
        self.chunker = chunker
        return self

    def set_error_strategy(self, strategy: ErrorStrategy) -> "Pipeline":
        """Set error handling strategy."""
        self.config.error_strategy = strategy
        return self
