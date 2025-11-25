"""
Configuration system for pipeline settings.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, Field, validator


class ParserSettings(BaseModel):
    """Settings for document parsers."""

    extract_tables: bool = True
    extract_images: bool = False
    ocr_enabled: bool = False
    ocr_language: str = "eng"
    ocr_engine: str = "tesseract"

    # Format-specific settings
    pdf: Dict[str, Any] = Field(default_factory=dict)
    docx: Dict[str, Any] = Field(default_factory=dict)
    pptx: Dict[str, Any] = Field(default_factory=dict)
    xlsx: Dict[str, Any] = Field(default_factory=dict)
    html: Dict[str, Any] = Field(default_factory=dict)
    hwpx: Dict[str, Any] = Field(default_factory=dict)


class PreprocessorSettings(BaseModel):
    """Settings for text preprocessors."""

    # Cleaner settings
    remove_html_tags: bool = True
    remove_urls: bool = False
    remove_emails: bool = False
    remove_extra_whitespace: bool = True
    remove_emojis: bool = False

    # Normalizer settings
    unicode_form: str = "NFC"
    lowercase: bool = False
    normalize_quotes: bool = True
    normalize_dashes: bool = True
    expand_contractions: bool = False


class ChunkerSettings(BaseModel):
    """Settings for text chunking."""

    strategy: str = "recursive"  # recursive, fixed, sentence, paragraph, semantic
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    separators: List[str] = Field(default_factory=lambda: ["\n\n", "\n", ". ", " ", ""])
    keep_separator: bool = True

    # Token-based chunking
    encoding: str = "cl100k_base"
    model: Optional[str] = None

    @validator("strategy")
    def validate_strategy(cls, v):
        valid = ["recursive", "fixed", "token", "sentence", "paragraph", "semantic", "sliding"]
        if v not in valid:
            raise ValueError(f"Invalid strategy: {v}. Must be one of {valid}")
        return v


class BatchSettings(BaseModel):
    """Settings for batch processing."""

    parallel: bool = False
    max_workers: int = 4
    show_progress: bool = True
    output_format: str = "json"  # json, jsonl
    output_dir: Optional[str] = None


class PipelineSettings(BaseModel):
    """Complete pipeline configuration."""

    parser: ParserSettings = Field(default_factory=ParserSettings)
    preprocessor: PreprocessorSettings = Field(default_factory=PreprocessorSettings)
    chunker: ChunkerSettings = Field(default_factory=ChunkerSettings)
    batch: BatchSettings = Field(default_factory=BatchSettings)
    error_strategy: str = "log"  # raise, skip, log

    def to_pipeline(self) -> "Pipeline":
        """Convert settings to Pipeline instance."""
        from src.chunkers import (
            FixedSizeChunker,
            ParagraphChunker,
            RecursiveChunker,
            SemanticChunker,
            SentenceChunker,
            SlidingWindowChunker,
            TokenChunker,
        )
        from src.pipeline.pipeline import ErrorStrategy, Pipeline, PipelineConfig
        from src.preprocessors import (
            CleanerConfig,
            NormalizerConfig,
            TextCleaner,
            TextNormalizer,
        )

        # Create preprocessors
        preprocessors = []

        cleaner_config = CleanerConfig(
            remove_html_tags=self.preprocessor.remove_html_tags,
            remove_urls=self.preprocessor.remove_urls,
            remove_emails=self.preprocessor.remove_emails,
            remove_extra_whitespace=self.preprocessor.remove_extra_whitespace,
            remove_emojis=self.preprocessor.remove_emojis,
        )
        preprocessors.append(TextCleaner(cleaner_config))

        normalizer_config = NormalizerConfig(
            unicode_form=self.preprocessor.unicode_form,
            lowercase=self.preprocessor.lowercase,
            normalize_quotes=self.preprocessor.normalize_quotes,
            normalize_dashes=self.preprocessor.normalize_dashes,
            expand_contractions=self.preprocessor.expand_contractions,
        )
        preprocessors.append(TextNormalizer(normalizer_config))

        # Create chunker
        chunker = None
        if self.chunker.strategy == "recursive":
            chunker = RecursiveChunker(
                chunk_size=self.chunker.chunk_size,
                chunk_overlap=self.chunker.chunk_overlap,
                separators=self.chunker.separators,
                keep_separator=self.chunker.keep_separator,
            )
        elif self.chunker.strategy == "fixed":
            chunker = FixedSizeChunker(
                chunk_size=self.chunker.chunk_size,
                chunk_overlap=self.chunker.chunk_overlap,
            )
        elif self.chunker.strategy == "token":
            chunker = TokenChunker(
                chunk_size=self.chunker.chunk_size,
                chunk_overlap=self.chunker.chunk_overlap,
                encoding=self.chunker.encoding,
                model=self.chunker.model,
            )
        elif self.chunker.strategy == "sentence":
            chunker = SentenceChunker(
                chunk_size=self.chunker.chunk_size,
                chunk_overlap=self.chunker.chunk_overlap,
            )
        elif self.chunker.strategy == "paragraph":
            chunker = ParagraphChunker(
                chunk_size=self.chunker.chunk_size,
                chunk_overlap=self.chunker.chunk_overlap,
            )
        elif self.chunker.strategy == "semantic":
            chunker = SemanticChunker(
                min_chunk_size=self.chunker.min_chunk_size,
                max_chunk_size=self.chunker.chunk_size,
            )
        elif self.chunker.strategy == "sliding":
            step_size = self.chunker.chunk_size - self.chunker.chunk_overlap
            chunker = SlidingWindowChunker(
                window_size=self.chunker.chunk_size,
                step_size=step_size,
            )

        # Create pipeline config
        error_strategy = ErrorStrategy(self.error_strategy)

        config = PipelineConfig(
            preprocessors=preprocessors,
            chunker=chunker,
            chunk_size=self.chunker.chunk_size,
            chunk_overlap=self.chunker.chunk_overlap,
            extract_tables=self.parser.extract_tables,
            extract_images=self.parser.extract_images,
            ocr_enabled=self.parser.ocr_enabled,
            ocr_language=self.parser.ocr_language,
            error_strategy=error_strategy,
        )

        return Pipeline(config)


class ConfigLoader:
    """Load pipeline configuration from files."""

    def load(self, path: Union[str, Path]) -> PipelineSettings:
        """
        Load configuration from file.

        Args:
            path: Path to YAML or JSON config file

        Returns:
            PipelineSettings: Loaded configuration
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        content = path.read_text()

        # Expand environment variables
        content = self._expand_env_vars(content)

        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        elif path.suffix == ".json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported config format: {path.suffix}")

        return PipelineSettings(**data)

    def load_from_dict(self, data: Dict[str, Any]) -> PipelineSettings:
        """
        Load configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            PipelineSettings: Loaded configuration
        """
        return PipelineSettings(**data)

    def _expand_env_vars(self, content: str) -> str:
        """Expand environment variables in config content."""
        import re

        pattern = r"\$\{([^}]+)\}"

        def replace(match):
            var_name = match.group(1)
            default = None
            if ":-" in var_name:
                var_name, default = var_name.split(":-", 1)
            return os.environ.get(var_name, default or "")

        return re.sub(pattern, replace, content)

    def save(
        self,
        settings: PipelineSettings,
        path: Union[str, Path],
        format: str = "yaml",
    ) -> None:
        """
        Save configuration to file.

        Args:
            settings: Configuration to save
            path: Output path
            format: Output format (yaml or json)
        """
        path = Path(path)
        data = settings.dict()

        if format == "yaml":
            content = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:
            content = json.dumps(data, indent=2, ensure_ascii=False)

        path.write_text(content)
