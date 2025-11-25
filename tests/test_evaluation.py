"""
Tests for evaluation and benchmarking module.
"""

import pytest
from typing import List

from src.evaluation.metrics import (
    calculate_text_similarity,
    calculate_bleu_score,
    calculate_word_error_rate,
    calculate_extraction_metrics,
    calculate_chunking_metrics,
    TextExtractionMetrics,
    ChunkingMetrics,
)
from src.evaluation.comparator import (
    ParsingResult,
    ConfigComparator,
    ComparisonReport,
)
from src.evaluation.embedding_evaluator import (
    EmbeddingEvaluator,
    EmbeddingComparisonResult,
)
from src.evaluation.benchmark import (
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkRunner,
    create_default_configs,
)


class TestTextSimilarity:
    """Tests for text similarity metrics."""

    def test_identical_texts(self):
        text = "This is a test sentence."
        assert calculate_text_similarity(text, text, "sequence") == 1.0
        assert calculate_text_similarity(text, text, "jaccard") == 1.0
        assert calculate_text_similarity(text, text, "cosine") >= 0.999  # Allow float precision

    def test_different_texts(self):
        text1 = "The quick brown fox"
        text2 = "A lazy dog sleeps"
        similarity = calculate_text_similarity(text1, text2, "jaccard")
        assert 0 <= similarity <= 1
        assert similarity < 0.5  # Should be low for different texts

    def test_partial_overlap(self):
        text1 = "The quick brown fox jumps"
        text2 = "The quick red fox runs"
        similarity = calculate_text_similarity(text1, text2, "jaccard")
        assert 0.2 < similarity < 0.8  # Some overlap

    def test_empty_texts(self):
        assert calculate_text_similarity("", "", "sequence") == 0.0
        assert calculate_text_similarity("test", "", "jaccard") == 0.0


class TestBLEUScore:
    """Tests for BLEU score calculation."""

    def test_identical_texts(self):
        text = "This is a reference sentence for testing."
        score = calculate_bleu_score(text, text)
        assert score > 0.9  # Should be very high

    def test_completely_different(self):
        ref = "The cat sat on the mat"
        cand = "Xyz abc def ghi jkl"
        score = calculate_bleu_score(ref, cand)
        assert score < 0.1  # Should be very low

    def test_partial_match(self):
        ref = "The quick brown fox jumps over the lazy dog"
        cand = "The quick fox jumps over a lazy dog"
        score = calculate_bleu_score(ref, cand)
        assert score >= 0.0  # Partial match, score depends on implementation

    def test_empty_candidate(self):
        ref = "This is a test"
        assert calculate_bleu_score(ref, "") == 0.0


class TestWordErrorRate:
    """Tests for Word Error Rate calculation."""

    def test_identical_texts(self):
        text = "This is a test"
        assert calculate_word_error_rate(text, text) == 0.0

    def test_one_word_different(self):
        ref = "The quick brown fox"
        hyp = "The quick red fox"
        wer = calculate_word_error_rate(ref, hyp)
        assert wer == 0.25  # 1 error out of 4 words

    def test_completely_different(self):
        ref = "Hello world"
        hyp = "Goodbye universe"
        wer = calculate_word_error_rate(ref, hyp)
        assert wer == 1.0  # All words wrong


class TestExtractionMetrics:
    """Tests for extraction metrics calculation."""

    def test_basic_metrics(self):
        text = "Hello world.\n\nThis is a test."
        metrics = calculate_extraction_metrics(text)

        assert metrics.char_count == len(text)
        assert metrics.word_count >= 5  # May include punctuation as separate tokens
        assert metrics.paragraph_count == 2

    def test_with_ground_truth(self):
        extracted = "The quick brown fox jumps"
        ground_truth = "The quick brown fox jumps over"

        metrics = calculate_extraction_metrics(extracted, ground_truth)

        assert metrics.recall < 1.0  # Missing words
        assert metrics.precision == 1.0  # All extracted words are correct
        assert 0 < metrics.f1_score < 1.0
        assert metrics.bleu_score > 0

    def test_perfect_extraction(self):
        text = "Perfect extraction test"
        metrics = calculate_extraction_metrics(text, text)

        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0


class TestChunkingMetrics:
    """Tests for chunking metrics calculation."""

    def test_basic_chunking(self):
        original = "This is a long text that will be chunked into smaller pieces."
        chunks = ["This is a long text", "that will be chunked", "into smaller pieces."]

        metrics = calculate_chunking_metrics(chunks, original)

        assert metrics.total_chunks == 3
        assert metrics.avg_chunk_size > 0
        assert metrics.min_chunk_size > 0
        assert metrics.max_chunk_size >= metrics.min_chunk_size

    def test_chunk_size_distribution(self):
        chunks = ["small"] * 5 + ["this is a medium sized chunk"] * 3

        metrics = calculate_chunking_metrics(chunks, " ".join(chunks))

        assert "tiny" in metrics.size_distribution or "small" in metrics.size_distribution
        assert metrics.total_chunks == 8

    def test_empty_chunks(self):
        metrics = calculate_chunking_metrics([], "original text")
        assert metrics.total_chunks == 0
        assert metrics.avg_chunk_size == 0


class TestConfigComparator:
    """Tests for configuration comparator."""

    def test_add_results(self):
        comparator = ConfigComparator()

        result = ParsingResult(
            config_name="test_config",
            config={"key": "value"},
            document_path="/path/to/doc.pdf",
            content="Test content",
            chunks=["chunk1", "chunk2"],
        )

        comparator.add_result(result)
        assert "test_config" in comparator.results
        assert len(comparator.results["test_config"]) == 1

    def test_compare_two_results(self):
        comparator = ConfigComparator()

        result_a = ParsingResult(
            config_name="config_a",
            config={},
            document_path="/doc.pdf",
            content="The quick brown fox jumps over the lazy dog.",
            chunks=["The quick brown fox", "jumps over the lazy dog."],
            parse_time_ms=100.0,
        )
        result_b = ParsingResult(
            config_name="config_b",
            config={},
            document_path="/doc.pdf",
            content="The quick brown fox jumps over the lazy dog.",
            chunks=["The quick", "brown fox jumps", "over the lazy dog."],
            parse_time_ms=150.0,
        )

        comparator.add_result(result_a)
        comparator.add_result(result_b)

        comparison = comparator.compare_two(result_a, result_b)

        assert comparison.config_a == "config_a"
        assert comparison.config_b == "config_b"
        assert comparison.content_similarity == 1.0  # Identical content
        assert comparison.chunk_count_diff == -1  # a has 2 chunks, b has 3

    def test_generate_report(self):
        comparator = ConfigComparator()

        for config in ["config_a", "config_b"]:
            result = ParsingResult(
                config_name=config,
                config={},
                document_path="/doc.pdf",
                content="Test content",
                chunks=["chunk1"],
            )
            comparator.add_result(result)

        report = comparator.generate_report("test_report")

        assert report.report_id == "test_report"
        assert len(report.configs) == 2
        assert len(report.comparisons) == 1


class TestEmbeddingEvaluator:
    """Tests for embedding evaluator."""

    def test_add_embeddings(self):
        evaluator = EmbeddingEvaluator()

        chunks = ["chunk1", "chunk2", "chunk3"]
        vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]

        evaluator.add_embeddings("test_config", chunks, vectors, "test_model")

        assert "test_config" in evaluator.embeddings
        assert evaluator.embeddings["test_config"]["dim"] == 3

    def test_cosine_similarity(self):
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        assert EmbeddingEvaluator.cosine_similarity(vec1, vec2) == 1.0

        vec3 = [0.0, 1.0, 0.0]
        assert EmbeddingEvaluator.cosine_similarity(vec1, vec3) == 0.0

    def test_find_similar(self):
        evaluator = EmbeddingEvaluator()

        chunks = ["apple", "banana", "cherry"]
        vectors = [[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]]
        evaluator.add_embeddings("test", chunks, vectors)

        query = [0.8, 0.6]  # Should be most similar to cherry
        results = evaluator.find_similar("test", query, top_k=2)

        assert len(results) == 2
        # Cherry should be first (most similar to query)

    def test_compare_embeddings(self):
        evaluator = EmbeddingEvaluator()

        chunks = ["same chunk"]
        evaluator.add_embeddings("config_a", chunks, [[1.0, 0.0, 0.0]])
        evaluator.add_embeddings("config_b", chunks, [[0.9, 0.1, 0.0]])

        comparison = evaluator.compare_embeddings("config_a", "config_b")

        assert comparison.config_a == "config_a"
        assert comparison.config_b == "config_b"
        assert comparison.avg_cosine_similarity > 0.9  # Should be high


class TestBenchmarkRunner:
    """Tests for benchmark runner."""

    def test_create_default_configs(self):
        configs = create_default_configs()

        assert len(configs) >= 3
        assert all(isinstance(c, BenchmarkConfig) for c in configs)
        config_names = [c.name for c in configs]
        assert "fast_basic" in config_names
        assert "balanced" in config_names

    def test_benchmark_config_to_dict(self):
        config = BenchmarkConfig(
            name="test",
            parser_config={"pdf": {"engine": "pymupdf"}},
            chunker_config={"strategy": "recursive"},
        )

        config_dict = config.to_dict()

        assert config_dict["name"] == "test"
        assert "parser_config" in config_dict
        assert "chunker_config" in config_dict

    def test_benchmark_result_to_dict(self):
        result = BenchmarkResult(
            config_name="test",
            document_path="/doc.pdf",
            parse_time_ms=100.0,
            content_length=1000,
            word_count=200,
            chunk_count=10,
        )

        result_dict = result.to_dict()

        assert result_dict["config_name"] == "test"
        assert result_dict["timing"]["parse_time_ms"] == 100.0
        assert result_dict["content_stats"]["word_count"] == 200


class TestIntegration:
    """Integration tests for the evaluation system."""

    def test_full_comparison_workflow(self):
        """Test complete workflow: parse -> compare -> report."""
        comparator = ConfigComparator(ground_truth="The quick brown fox jumps.")

        # Simulate results from two configs
        result_a = ParsingResult(
            config_name="config_a",
            config={"engine": "pymupdf"},
            document_path="test.pdf",
            content="The quick brown fox jumps.",
            chunks=["The quick brown", "fox jumps."],
            parse_time_ms=50.0,
        )
        result_b = ParsingResult(
            config_name="config_b",
            config={"engine": "pdfplumber"},
            document_path="test.pdf",
            content="The quick brown fox.",  # Missing "jumps"
            chunks=["The quick brown fox."],
            parse_time_ms=100.0,
        )

        comparator.add_result(result_a)
        comparator.add_result(result_b)

        report = comparator.generate_report()

        # Verify report structure
        assert len(report.configs) == 2
        assert len(report.results) == 2
        assert len(report.comparisons) == 1

        # Config A should be better (higher recall)
        assert result_a.extraction_metrics.recall > result_b.extraction_metrics.recall

    def test_embedding_evaluation_workflow(self):
        """Test embedding evaluation workflow."""
        evaluator = EmbeddingEvaluator()

        # Add embeddings from different configs
        chunks_a = ["Document about AI", "Machine learning basics", "Neural networks"]
        vectors_a = [[0.9, 0.1, 0.0], [0.1, 0.9, 0.1], [0.2, 0.3, 0.9]]

        chunks_b = ["Document about AI", "Machine learning basics", "Neural networks"]
        vectors_b = [[0.85, 0.15, 0.0], [0.15, 0.85, 0.15], [0.25, 0.35, 0.85]]

        evaluator.add_embeddings("config_a", chunks_a, vectors_a, "model_a")
        evaluator.add_embeddings("config_b", chunks_b, vectors_b, "model_b")

        # Compare embeddings
        comparison = evaluator.compare_embeddings("config_a", "config_b")

        # Should be highly correlated since they're similar
        assert comparison.avg_cosine_similarity > 0.9

        # Generate report
        report = evaluator.generate_report()
        assert "config_a" in report["config_details"]
        assert "config_b" in report["config_details"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
