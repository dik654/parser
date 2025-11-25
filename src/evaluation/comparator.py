"""
Configuration comparator for comparing parsing results across different settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import json
import hashlib

from src.evaluation.metrics import (
    TextExtractionMetrics,
    ChunkingMetrics,
    calculate_extraction_metrics,
    calculate_chunking_metrics,
)


@dataclass
class ParsingResult:
    """Result of parsing a document with a specific configuration."""

    config_name: str
    config: Dict[str, Any]
    document_path: str
    content: str
    chunks: List[str] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Performance metrics
    parse_time_ms: float = 0.0
    memory_usage_mb: float = 0.0

    # Quality metrics (calculated)
    extraction_metrics: Optional[TextExtractionMetrics] = None
    chunking_metrics: Optional[ChunkingMetrics] = None

    # Embeddings (if generated)
    embeddings: Optional[List[List[float]]] = None
    embedding_model: str = ""

    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def config_hash(self) -> str:
        """Generate hash of configuration for comparison."""
        config_str = json.dumps(self.config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_name": self.config_name,
            "config_hash": self.config_hash,
            "config": self.config,
            "document_path": self.document_path,
            "content_length": len(self.content),
            "chunk_count": len(self.chunks),
            "table_count": len(self.tables),
            "image_count": len(self.images),
            "parse_time_ms": self.parse_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "extraction_metrics": (
                self.extraction_metrics.to_dict() if self.extraction_metrics else None
            ),
            "chunking_metrics": (
                self.chunking_metrics.to_dict() if self.chunking_metrics else None
            ),
            "embedding_model": self.embedding_model,
            "has_embeddings": self.embeddings is not None,
            "timestamp": self.timestamp,
        }


@dataclass
class ConfigComparison:
    """Comparison between two parsing results."""

    config_a: str
    config_b: str
    document_path: str

    # Content comparison
    content_similarity: float = 0.0
    content_diff_chars: int = 0
    content_diff_words: int = 0

    # Chunk comparison
    chunk_count_diff: int = 0
    avg_chunk_size_diff: float = 0.0

    # Performance comparison
    parse_time_diff_ms: float = 0.0
    memory_diff_mb: float = 0.0

    # Quality comparison (if ground truth available)
    f1_score_diff: float = 0.0
    bleu_score_diff: float = 0.0

    # Winner determination
    better_config: str = ""
    comparison_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_a": self.config_a,
            "config_b": self.config_b,
            "document_path": self.document_path,
            "content_similarity": round(self.content_similarity, 4),
            "content_diff_chars": self.content_diff_chars,
            "content_diff_words": self.content_diff_words,
            "chunk_count_diff": self.chunk_count_diff,
            "avg_chunk_size_diff": round(self.avg_chunk_size_diff, 2),
            "parse_time_diff_ms": round(self.parse_time_diff_ms, 2),
            "memory_diff_mb": round(self.memory_diff_mb, 2),
            "f1_score_diff": round(self.f1_score_diff, 4),
            "bleu_score_diff": round(self.bleu_score_diff, 4),
            "better_config": self.better_config,
            "comparison_notes": self.comparison_notes,
        }


@dataclass
class ComparisonReport:
    """Complete comparison report across multiple configurations."""

    report_id: str
    document_paths: List[str]
    configs: List[str]
    results: List[ParsingResult] = field(default_factory=list)
    comparisons: List[ConfigComparison] = field(default_factory=list)

    # Aggregated metrics
    summary: Dict[str, Any] = field(default_factory=dict)
    rankings: Dict[str, int] = field(default_factory=dict)  # config -> rank
    recommendations: List[str] = field(default_factory=list)

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "document_count": len(self.document_paths),
            "config_count": len(self.configs),
            "configs": self.configs,
            "results": [r.to_dict() for r in self.results],
            "comparisons": [c.to_dict() for c in self.comparisons],
            "summary": self.summary,
            "rankings": self.rankings,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: Union[str, Path]) -> None:
        """Save report to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())


class ConfigComparator:
    """
    Compare parsing results across different configurations.

    Usage:
        comparator = ConfigComparator()

        # Add parsing results
        comparator.add_result(result_config_a)
        comparator.add_result(result_config_b)

        # Generate comparison report
        report = comparator.compare(ground_truth="expected_text.txt")
        report.save("comparison_report.json")
    """

    def __init__(
        self,
        ground_truth: Optional[str] = None,
        token_counter: Optional[callable] = None,
    ):
        """
        Initialize comparator.

        Args:
            ground_truth: Optional ground truth text for quality evaluation
            token_counter: Optional function to count tokens
        """
        self.ground_truth = ground_truth
        self.token_counter = token_counter or (lambda x: len(x.split()))
        self.results: Dict[str, List[ParsingResult]] = {}  # config_name -> results

    def add_result(self, result: ParsingResult) -> None:
        """Add a parsing result for comparison."""
        if result.config_name not in self.results:
            self.results[result.config_name] = []
        self.results[result.config_name].append(result)

        # Calculate metrics if not already done
        if result.extraction_metrics is None:
            result.extraction_metrics = calculate_extraction_metrics(
                result.content, self.ground_truth
            )
        if result.chunking_metrics is None and result.chunks:
            result.chunking_metrics = calculate_chunking_metrics(
                result.chunks, result.content, self.token_counter
            )

    def compare_two(
        self, result_a: ParsingResult, result_b: ParsingResult
    ) -> ConfigComparison:
        """Compare two specific parsing results."""
        from src.evaluation.metrics import calculate_text_similarity

        comparison = ConfigComparison(
            config_a=result_a.config_name,
            config_b=result_b.config_name,
            document_path=result_a.document_path,
        )

        # Content comparison
        comparison.content_similarity = calculate_text_similarity(
            result_a.content, result_b.content, "sequence"
        )
        comparison.content_diff_chars = abs(len(result_a.content) - len(result_b.content))
        comparison.content_diff_words = abs(
            len(result_a.content.split()) - len(result_b.content.split())
        )

        # Chunk comparison
        comparison.chunk_count_diff = len(result_a.chunks) - len(result_b.chunks)
        if result_a.chunking_metrics and result_b.chunking_metrics:
            comparison.avg_chunk_size_diff = (
                result_a.chunking_metrics.avg_chunk_size
                - result_b.chunking_metrics.avg_chunk_size
            )

        # Performance comparison
        comparison.parse_time_diff_ms = result_a.parse_time_ms - result_b.parse_time_ms
        comparison.memory_diff_mb = result_a.memory_usage_mb - result_b.memory_usage_mb

        # Quality comparison
        if result_a.extraction_metrics and result_b.extraction_metrics:
            comparison.f1_score_diff = (
                result_a.extraction_metrics.f1_score
                - result_b.extraction_metrics.f1_score
            )
            comparison.bleu_score_diff = (
                result_a.extraction_metrics.bleu_score
                - result_b.extraction_metrics.bleu_score
            )

        # Determine better config
        notes = []
        a_score, b_score = 0, 0

        if comparison.content_diff_words > 0:
            notes.append(f"{result_a.config_name} extracts {comparison.content_diff_words} more words")
            a_score += 1
        elif comparison.content_diff_words < 0:
            notes.append(f"{result_b.config_name} extracts {-comparison.content_diff_words} more words")
            b_score += 1

        if comparison.f1_score_diff > 0.01:
            notes.append(f"{result_a.config_name} has higher F1 score (+{comparison.f1_score_diff:.4f})")
            a_score += 2
        elif comparison.f1_score_diff < -0.01:
            notes.append(f"{result_b.config_name} has higher F1 score (+{-comparison.f1_score_diff:.4f})")
            b_score += 2

        if comparison.parse_time_diff_ms < -100:
            notes.append(f"{result_a.config_name} is faster by {-comparison.parse_time_diff_ms:.0f}ms")
            a_score += 1
        elif comparison.parse_time_diff_ms > 100:
            notes.append(f"{result_b.config_name} is faster by {comparison.parse_time_diff_ms:.0f}ms")
            b_score += 1

        comparison.comparison_notes = notes
        if a_score > b_score:
            comparison.better_config = result_a.config_name
        elif b_score > a_score:
            comparison.better_config = result_b.config_name
        else:
            comparison.better_config = "tie"

        return comparison

    def generate_report(self, report_id: Optional[str] = None) -> ComparisonReport:
        """Generate comprehensive comparison report."""
        if report_id is None:
            report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Collect all document paths and configs
        all_docs = set()
        all_configs = list(self.results.keys())
        all_results = []

        for config_name, results in self.results.items():
            for result in results:
                all_docs.add(result.document_path)
                all_results.append(result)

        report = ComparisonReport(
            report_id=report_id,
            document_paths=list(all_docs),
            configs=all_configs,
            results=all_results,
        )

        # Generate pairwise comparisons
        for i, config_a in enumerate(all_configs):
            for config_b in all_configs[i + 1 :]:
                # Find matching documents
                results_a = {r.document_path: r for r in self.results[config_a]}
                results_b = {r.document_path: r for r in self.results[config_b]}

                common_docs = set(results_a.keys()) & set(results_b.keys())
                for doc_path in common_docs:
                    comparison = self.compare_two(results_a[doc_path], results_b[doc_path])
                    report.comparisons.append(comparison)

        # Calculate summary statistics
        report.summary = self._calculate_summary(report)
        report.rankings = self._calculate_rankings(report)
        report.recommendations = self._generate_recommendations(report)

        return report

    def _calculate_summary(self, report: ComparisonReport) -> Dict[str, Any]:
        """Calculate summary statistics per configuration."""
        summary = {}

        for config_name in report.configs:
            config_results = [r for r in report.results if r.config_name == config_name]
            if not config_results:
                continue

            summary[config_name] = {
                "document_count": len(config_results),
                "avg_parse_time_ms": sum(r.parse_time_ms for r in config_results)
                / len(config_results),
                "avg_content_length": sum(len(r.content) for r in config_results)
                / len(config_results),
                "avg_chunk_count": sum(len(r.chunks) for r in config_results)
                / len(config_results),
            }

            # Average quality metrics
            extraction_metrics = [
                r.extraction_metrics
                for r in config_results
                if r.extraction_metrics
            ]
            if extraction_metrics:
                summary[config_name]["avg_f1_score"] = sum(
                    m.f1_score for m in extraction_metrics
                ) / len(extraction_metrics)
                summary[config_name]["avg_bleu_score"] = sum(
                    m.bleu_score for m in extraction_metrics
                ) / len(extraction_metrics)

        return summary

    def _calculate_rankings(self, report: ComparisonReport) -> Dict[str, int]:
        """Calculate rankings based on overall performance."""
        scores = {config: 0 for config in report.configs}

        for comparison in report.comparisons:
            if comparison.better_config and comparison.better_config != "tie":
                scores[comparison.better_config] += 1

        # Sort by score and assign ranks
        sorted_configs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        rankings = {}
        for rank, (config, _) in enumerate(sorted_configs, 1):
            rankings[config] = rank

        return rankings

    def _generate_recommendations(self, report: ComparisonReport) -> List[str]:
        """Generate recommendations based on comparison results."""
        recommendations = []

        if not report.rankings:
            return ["Insufficient data for recommendations"]

        best_config = min(report.rankings, key=report.rankings.get)
        recommendations.append(
            f"Best overall configuration: {best_config} (Rank #{report.rankings[best_config]})"
        )

        # Speed recommendation
        if report.summary:
            fastest = min(
                report.summary.items(),
                key=lambda x: x[1].get("avg_parse_time_ms", float("inf")),
            )
            recommendations.append(
                f"Fastest configuration: {fastest[0]} "
                f"({fastest[1].get('avg_parse_time_ms', 0):.0f}ms avg)"
            )

            # Quality recommendation
            best_quality = max(
                report.summary.items(),
                key=lambda x: x[1].get("avg_f1_score", 0),
            )
            if best_quality[1].get("avg_f1_score", 0) > 0:
                recommendations.append(
                    f"Highest quality: {best_quality[0]} "
                    f"(F1: {best_quality[1].get('avg_f1_score', 0):.4f})"
                )

        return recommendations
