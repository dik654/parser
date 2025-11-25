"""
Benchmark runner for automated evaluation of parsing configurations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from datetime import datetime
import json
import time
import traceback
import sys

from src.evaluation.metrics import (
    calculate_extraction_metrics,
    calculate_chunking_metrics,
    TextExtractionMetrics,
    ChunkingMetrics,
)
from src.evaluation.comparator import ParsingResult, ConfigComparator, ComparisonReport


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""

    name: str
    parser_config: Dict[str, Any]
    chunker_config: Optional[Dict[str, Any]] = None
    preprocessor_config: Optional[Dict[str, Any]] = None
    embedding_config: Optional[Dict[str, Any]] = None

    # Options
    enable_ocr: bool = True
    extract_tables: bool = True
    extract_images: bool = False
    ocr_images: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "parser_config": self.parser_config,
            "chunker_config": self.chunker_config,
            "preprocessor_config": self.preprocessor_config,
            "embedding_config": self.embedding_config,
            "enable_ocr": self.enable_ocr,
            "extract_tables": self.extract_tables,
            "extract_images": self.extract_images,
            "ocr_images": self.ocr_images,
        }


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""

    config_name: str
    document_path: str
    success: bool = True
    error_message: str = ""

    # Timing
    parse_time_ms: float = 0.0
    preprocess_time_ms: float = 0.0
    chunk_time_ms: float = 0.0
    embed_time_ms: float = 0.0
    total_time_ms: float = 0.0

    # Memory (if tracked)
    peak_memory_mb: float = 0.0

    # Content stats
    content_length: int = 0
    word_count: int = 0
    chunk_count: int = 0
    table_count: int = 0
    image_count: int = 0

    # Quality metrics
    extraction_metrics: Optional[TextExtractionMetrics] = None
    chunking_metrics: Optional[ChunkingMetrics] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_name": self.config_name,
            "document_path": self.document_path,
            "success": self.success,
            "error_message": self.error_message,
            "timing": {
                "parse_time_ms": round(self.parse_time_ms, 2),
                "preprocess_time_ms": round(self.preprocess_time_ms, 2),
                "chunk_time_ms": round(self.chunk_time_ms, 2),
                "embed_time_ms": round(self.embed_time_ms, 2),
                "total_time_ms": round(self.total_time_ms, 2),
            },
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "content_stats": {
                "content_length": self.content_length,
                "word_count": self.word_count,
                "chunk_count": self.chunk_count,
                "table_count": self.table_count,
                "image_count": self.image_count,
            },
            "extraction_metrics": (
                self.extraction_metrics.to_dict()
                if self.extraction_metrics
                else None
            ),
            "chunking_metrics": (
                self.chunking_metrics.to_dict() if self.chunking_metrics else None
            ),
        }


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results."""

    suite_id: str
    configs: List[BenchmarkConfig]
    documents: List[str]
    results: List[BenchmarkResult] = field(default_factory=list)
    comparison_report: Optional[ComparisonReport] = None

    # Aggregated stats
    summary: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    rankings: Dict[str, int] = field(default_factory=dict)

    # Metadata
    start_time: str = ""
    end_time: str = ""
    total_duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "configs": [c.to_dict() for c in self.configs],
            "documents": self.documents,
            "num_results": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "rankings": self.rankings,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())


class BenchmarkRunner:
    """
    Run benchmarks comparing different parsing configurations.

    Usage:
        runner = BenchmarkRunner()

        # Define configurations to compare
        config_a = BenchmarkConfig(
            name="default",
            parser_config={"pdf": {"engine": "pymupdf"}},
            chunker_config={"strategy": "recursive", "chunk_size": 512},
        )
        config_b = BenchmarkConfig(
            name="high_quality",
            parser_config={"pdf": {"engine": "pdfplumber", "ocr_enabled": True}},
            chunker_config={"strategy": "semantic", "chunk_size": 512},
        )

        # Run benchmark
        suite = runner.run(
            configs=[config_a, config_b],
            documents=["doc1.pdf", "doc2.pdf"],
            ground_truth={"doc1.pdf": "expected text..."},
        )

        # Save results
        suite.save("benchmark_results.json")
    """

    def __init__(
        self,
        parse_fn: Optional[Callable] = None,
        preprocess_fn: Optional[Callable] = None,
        chunk_fn: Optional[Callable] = None,
        embed_fn: Optional[Callable] = None,
        token_counter: Optional[Callable] = None,
    ):
        """
        Initialize benchmark runner.

        Args:
            parse_fn: Function to parse documents: (path, config) -> (content, tables, images)
            preprocess_fn: Function to preprocess text: (text, config) -> text
            chunk_fn: Function to chunk text: (text, config) -> List[str]
            embed_fn: Function to embed chunks: (chunks, config) -> List[List[float]]
            token_counter: Function to count tokens: (text) -> int
        """
        self.parse_fn = parse_fn
        self.preprocess_fn = preprocess_fn
        self.chunk_fn = chunk_fn
        self.embed_fn = embed_fn
        self.token_counter = token_counter or (lambda x: len(x.split()))

    def run_single(
        self,
        config: BenchmarkConfig,
        document_path: str,
        ground_truth: Optional[str] = None,
    ) -> BenchmarkResult:
        """
        Run benchmark for a single document with a single configuration.

        Args:
            config: Benchmark configuration
            document_path: Path to document
            ground_truth: Optional ground truth text

        Returns:
            BenchmarkResult
        """
        result = BenchmarkResult(
            config_name=config.name,
            document_path=document_path,
        )

        total_start = time.perf_counter()

        try:
            content = ""
            tables = []
            images = []
            chunks = []

            # Parse
            if self.parse_fn:
                start = time.perf_counter()
                parse_result = self.parse_fn(document_path, config.parser_config)
                result.parse_time_ms = (time.perf_counter() - start) * 1000

                if isinstance(parse_result, tuple):
                    content, tables, images = parse_result
                else:
                    content = parse_result

            # Preprocess
            if self.preprocess_fn and content:
                start = time.perf_counter()
                content = self.preprocess_fn(content, config.preprocessor_config or {})
                result.preprocess_time_ms = (time.perf_counter() - start) * 1000

            # Chunk
            if self.chunk_fn and content:
                start = time.perf_counter()
                chunks = self.chunk_fn(content, config.chunker_config or {})
                result.chunk_time_ms = (time.perf_counter() - start) * 1000

            # Embed (optional)
            if self.embed_fn and chunks and config.embedding_config:
                start = time.perf_counter()
                _ = self.embed_fn(chunks, config.embedding_config)
                result.embed_time_ms = (time.perf_counter() - start) * 1000

            # Record stats
            result.content_length = len(content)
            result.word_count = len(content.split())
            result.chunk_count = len(chunks)
            result.table_count = len(tables) if tables else 0
            result.image_count = len(images) if images else 0

            # Calculate metrics
            result.extraction_metrics = calculate_extraction_metrics(
                content, ground_truth
            )
            if chunks:
                result.chunking_metrics = calculate_chunking_metrics(
                    chunks, content, self.token_counter
                )

        except Exception as e:
            result.success = False
            result.error_message = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

        result.total_time_ms = (time.perf_counter() - total_start) * 1000
        return result

    def run(
        self,
        configs: List[BenchmarkConfig],
        documents: List[str],
        ground_truth: Optional[Dict[str, str]] = None,
        suite_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> BenchmarkSuite:
        """
        Run complete benchmark suite.

        Args:
            configs: List of configurations to benchmark
            documents: List of document paths
            ground_truth: Optional dict mapping document paths to ground truth text
            suite_id: Optional suite identifier
            progress_callback: Optional callback(current, total, message)

        Returns:
            BenchmarkSuite with all results
        """
        if suite_id is None:
            suite_id = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        suite = BenchmarkSuite(
            suite_id=suite_id,
            configs=configs,
            documents=documents,
            start_time=datetime.now().isoformat(),
        )

        ground_truth = ground_truth or {}
        total_runs = len(configs) * len(documents)
        current_run = 0

        for config in configs:
            for doc_path in documents:
                current_run += 1
                if progress_callback:
                    progress_callback(
                        current_run,
                        total_runs,
                        f"Running {config.name} on {Path(doc_path).name}",
                    )

                gt = ground_truth.get(doc_path)
                result = self.run_single(config, doc_path, gt)
                suite.results.append(result)

        suite.end_time = datetime.now().isoformat()
        suite.total_duration_seconds = sum(r.total_time_ms for r in suite.results) / 1000

        # Calculate summary and rankings
        suite.summary = self._calculate_summary(suite)
        suite.rankings = self._calculate_rankings(suite)

        # Generate comparison report
        comparator = ConfigComparator(token_counter=self.token_counter)
        for result in suite.results:
            parsing_result = ParsingResult(
                config_name=result.config_name,
                config=next(
                    c.to_dict() for c in configs if c.name == result.config_name
                ),
                document_path=result.document_path,
                content="",  # Not stored in benchmark result
                parse_time_ms=result.parse_time_ms,
            )
            parsing_result.extraction_metrics = result.extraction_metrics
            parsing_result.chunking_metrics = result.chunking_metrics
            comparator.add_result(parsing_result)

        suite.comparison_report = comparator.generate_report(f"{suite_id}_comparison")

        return suite

    def _calculate_summary(self, suite: BenchmarkSuite) -> Dict[str, Dict[str, Any]]:
        """Calculate summary statistics per configuration."""
        summary = {}

        for config in suite.configs:
            config_results = [
                r for r in suite.results if r.config_name == config.name and r.success
            ]
            if not config_results:
                continue

            summary[config.name] = {
                "total_runs": len(config_results),
                "success_rate": len(config_results)
                / len([r for r in suite.results if r.config_name == config.name]),
                "avg_parse_time_ms": sum(r.parse_time_ms for r in config_results)
                / len(config_results),
                "avg_total_time_ms": sum(r.total_time_ms for r in config_results)
                / len(config_results),
                "avg_content_length": sum(r.content_length for r in config_results)
                / len(config_results),
                "avg_chunk_count": sum(r.chunk_count for r in config_results)
                / len(config_results),
            }

            # Quality metrics
            metrics_with_f1 = [
                r.extraction_metrics
                for r in config_results
                if r.extraction_metrics and r.extraction_metrics.f1_score > 0
            ]
            if metrics_with_f1:
                summary[config.name]["avg_f1_score"] = sum(
                    m.f1_score for m in metrics_with_f1
                ) / len(metrics_with_f1)
                summary[config.name]["avg_bleu_score"] = sum(
                    m.bleu_score for m in metrics_with_f1
                ) / len(metrics_with_f1)

        return summary

    def _calculate_rankings(self, suite: BenchmarkSuite) -> Dict[str, int]:
        """Calculate rankings based on composite score."""
        if not suite.summary:
            return {}

        scores = {}
        for config_name, stats in suite.summary.items():
            # Composite score: quality (70%) + speed (30%)
            quality_score = stats.get("avg_f1_score", 0) * 100
            speed_score = max(0, 100 - stats.get("avg_total_time_ms", 1000) / 10)
            scores[config_name] = quality_score * 0.7 + speed_score * 0.3

        sorted_configs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return {config: rank + 1 for rank, (config, _) in enumerate(sorted_configs)}


def create_default_configs() -> List[BenchmarkConfig]:
    """Create a set of default benchmark configurations for comparison."""
    configs = [
        # Fast, basic extraction
        BenchmarkConfig(
            name="fast_basic",
            parser_config={
                "pdf": {"engine": "pymupdf", "ocr_enabled": False},
            },
            chunker_config={
                "strategy": "fixed_size",
                "chunk_size": 512,
                "chunk_overlap": 0,
            },
            enable_ocr=False,
            extract_tables=False,
        ),
        # Balanced configuration
        BenchmarkConfig(
            name="balanced",
            parser_config={
                "pdf": {"engine": "pymupdf", "ocr_enabled": True},
            },
            chunker_config={
                "strategy": "recursive",
                "chunk_size": 512,
                "chunk_overlap": 50,
            },
            enable_ocr=True,
            extract_tables=True,
        ),
        # High quality, slower
        BenchmarkConfig(
            name="high_quality",
            parser_config={
                "pdf": {"engine": "pdfplumber", "ocr_enabled": True},
            },
            chunker_config={
                "strategy": "recursive",
                "chunk_size": 400,
                "chunk_overlap": 80,
            },
            enable_ocr=True,
            extract_tables=True,
            extract_images=True,
            ocr_images=True,
        ),
        # Small chunks for precise retrieval
        BenchmarkConfig(
            name="small_chunks",
            parser_config={
                "pdf": {"engine": "pymupdf", "ocr_enabled": True},
            },
            chunker_config={
                "strategy": "recursive",
                "chunk_size": 256,
                "chunk_overlap": 50,
            },
            enable_ocr=True,
        ),
        # Large chunks for context preservation
        BenchmarkConfig(
            name="large_chunks",
            parser_config={
                "pdf": {"engine": "pymupdf", "ocr_enabled": True},
            },
            chunker_config={
                "strategy": "recursive",
                "chunk_size": 1024,
                "chunk_overlap": 100,
            },
            enable_ocr=True,
        ),
    ]
    return configs
