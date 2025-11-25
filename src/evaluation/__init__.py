"""
Evaluation and benchmarking module for AI Document Preprocessing Parser.

This module provides tools for:
- Comparing parsing results across different configurations
- Evaluating text extraction quality
- Comparing embedding results for RAG applications
- Generating benchmark reports
"""

from src.evaluation.metrics import (
    TextExtractionMetrics,
    ChunkingMetrics,
    EmbeddingMetrics,
    calculate_text_similarity,
    calculate_bleu_score,
)
from src.evaluation.comparator import (
    ConfigComparator,
    ParsingResult,
    ComparisonReport,
)
from src.evaluation.embedding_evaluator import (
    EmbeddingEvaluator,
    EmbeddingComparisonResult,
)
from src.evaluation.benchmark import (
    BenchmarkRunner,
    BenchmarkConfig,
    BenchmarkResult,
)

__all__ = [
    # Metrics
    "TextExtractionMetrics",
    "ChunkingMetrics",
    "EmbeddingMetrics",
    "calculate_text_similarity",
    "calculate_bleu_score",
    # Comparator
    "ConfigComparator",
    "ParsingResult",
    "ComparisonReport",
    # Embedding
    "EmbeddingEvaluator",
    "EmbeddingComparisonResult",
    # Benchmark
    "BenchmarkRunner",
    "BenchmarkConfig",
    "BenchmarkResult",
]
