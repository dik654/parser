"""
Example: Comparing parsing configurations and embedding quality.

This example demonstrates how to:
1. Define different parsing configurations
2. Run benchmarks across multiple documents
3. Compare text extraction quality
4. Compare embedding quality for RAG applications
5. Generate comparison reports
"""

from pathlib import Path
from typing import List, Dict, Tuple, Any

# Import evaluation modules
from src.evaluation.benchmark import (
    BenchmarkRunner,
    BenchmarkConfig,
    BenchmarkSuite,
    create_default_configs,
)
from src.evaluation.comparator import (
    ConfigComparator,
    ParsingResult,
    ComparisonReport,
)
from src.evaluation.embedding_evaluator import (
    EmbeddingEvaluator,
    RetrievalEvaluation,
)
from src.evaluation.metrics import (
    calculate_extraction_metrics,
    calculate_chunking_metrics,
)


# =============================================================================
# Example 1: Basic Configuration Comparison
# =============================================================================

def example_basic_comparison():
    """
    Compare parsing results from two different configurations.
    """
    print("=" * 60)
    print("Example 1: Basic Configuration Comparison")
    print("=" * 60)

    # Simulated parsing results (in real usage, these come from actual parsing)
    ground_truth = """
    Artificial Intelligence (AI) is transforming industries worldwide.
    Machine learning, a subset of AI, enables systems to learn from data.
    Deep learning uses neural networks with multiple layers.
    """

    # Config A: Fast, basic extraction
    result_a = ParsingResult(
        config_name="fast_basic",
        config={"engine": "pymupdf", "ocr": False},
        document_path="ai_document.pdf",
        content="""
        Artificial Intelligence (AI) is transforming industries worldwide.
        Machine learning, a subset of AI, enables systems to learn from data.
        Deep learning uses neural networks with multiple layers.
        """,
        chunks=[
            "Artificial Intelligence (AI) is transforming industries worldwide.",
            "Machine learning, a subset of AI, enables systems to learn from data.",
            "Deep learning uses neural networks with multiple layers.",
        ],
        parse_time_ms=50.0,
    )

    # Config B: High quality with OCR (simulating slightly different extraction)
    result_b = ParsingResult(
        config_name="high_quality",
        config={"engine": "pdfplumber", "ocr": True},
        document_path="ai_document.pdf",
        content="""
        Artificial Intelligence (AI) is transforming industries worldwide.
        Machine learning, a subset of AI, enables systems to learn from data.
        Deep learning uses neural networks with multiple layers.
        Natural language processing is another key AI application.
        """,  # Extracted more content
        chunks=[
            "Artificial Intelligence (AI) is transforming industries worldwide. Machine learning,",
            "a subset of AI, enables systems to learn from data. Deep learning uses",
            "neural networks with multiple layers. Natural language processing is another",
            "key AI application.",
        ],
        parse_time_ms=150.0,
    )

    # Create comparator
    comparator = ConfigComparator(ground_truth=ground_truth.strip())
    comparator.add_result(result_a)
    comparator.add_result(result_b)

    # Generate report
    report = comparator.generate_report("basic_comparison")

    print("\n📊 Comparison Results:")
    print(f"  Configs compared: {report.configs}")
    print(f"  Documents: {report.document_paths}")

    print("\n📈 Summary per config:")
    for config, stats in report.summary.items():
        print(f"\n  {config}:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"    {key}: {value:.4f}")
            else:
                print(f"    {key}: {value}")

    print("\n🏆 Rankings:", report.rankings)
    print("\n💡 Recommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")

    return report


# =============================================================================
# Example 2: Chunking Strategy Comparison
# =============================================================================

def example_chunking_comparison():
    """
    Compare different chunking strategies and their quality metrics.
    """
    print("\n" + "=" * 60)
    print("Example 2: Chunking Strategy Comparison")
    print("=" * 60)

    original_text = """
    Introduction to Machine Learning

    Machine learning is a method of data analysis that automates analytical model building.
    It is a branch of artificial intelligence based on the idea that systems can learn from data,
    identify patterns and make decisions with minimal human intervention.

    Types of Machine Learning

    There are three main types of machine learning: supervised learning, unsupervised learning,
    and reinforcement learning. Each type has its own use cases and applications.

    Supervised Learning

    In supervised learning, the algorithm learns from labeled training data, and makes predictions
    based on that data. Common applications include spam detection, image classification,
    and price prediction.
    """

    # Strategy 1: Fixed size chunks (512 tokens, no overlap)
    chunks_fixed = [
        "Introduction to Machine Learning\n\nMachine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
        "Types of Machine Learning\n\nThere are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Each type has its own use cases and applications.",
        "Supervised Learning\n\nIn supervised learning, the algorithm learns from labeled training data, and makes predictions based on that data. Common applications include spam detection, image classification, and price prediction.",
    ]

    # Strategy 2: Recursive with overlap
    chunks_recursive = [
        "Introduction to Machine Learning\n\nMachine learning is a method of data analysis that automates analytical model building.",
        "It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
        "Types of Machine Learning\n\nThere are three main types of machine learning: supervised learning, unsupervised learning,",
        "and reinforcement learning. Each type has its own use cases and applications.",
        "Supervised Learning\n\nIn supervised learning, the algorithm learns from labeled training data,",
        "and makes predictions based on that data. Common applications include spam detection, image classification, and price prediction.",
    ]

    # Strategy 3: Paragraph-based
    chunks_paragraph = [
        "Introduction to Machine Learning",
        "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
        "Types of Machine Learning",
        "There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Each type has its own use cases and applications.",
        "Supervised Learning",
        "In supervised learning, the algorithm learns from labeled training data, and makes predictions based on that data. Common applications include spam detection, image classification, and price prediction.",
    ]

    strategies = {
        "fixed_size": chunks_fixed,
        "recursive": chunks_recursive,
        "paragraph": chunks_paragraph,
    }

    print("\n📊 Chunking Metrics by Strategy:\n")

    for strategy_name, chunks in strategies.items():
        metrics = calculate_chunking_metrics(chunks, original_text)
        print(f"Strategy: {strategy_name}")
        print(f"  Total chunks: {metrics.total_chunks}")
        print(f"  Avg chunk size: {metrics.avg_chunk_size:.1f} words")
        print(f"  Min/Max size: {metrics.min_chunk_size}/{metrics.max_chunk_size}")
        print(f"  Std deviation: {metrics.std_chunk_size:.1f}")
        print(f"  Sentence boundary ratio: {metrics.sentence_boundary_ratio:.2%}")
        print(f"  Size distribution: {metrics.size_distribution}")
        print()

    return strategies


# =============================================================================
# Example 3: Embedding Quality Comparison
# =============================================================================

def example_embedding_comparison():
    """
    Compare embedding quality between different configurations for RAG.
    """
    print("\n" + "=" * 60)
    print("Example 3: Embedding Quality Comparison")
    print("=" * 60)

    evaluator = EmbeddingEvaluator()

    # Chunks from Config A (larger chunks)
    chunks_a = [
        "Machine learning is a subset of AI that enables systems to learn from data.",
        "Deep learning uses neural networks with many layers for complex pattern recognition.",
        "Natural language processing helps computers understand human language.",
    ]

    # Simulated embeddings (in real usage, these come from embedding models)
    # These are simplified 4-dimensional vectors for demonstration
    embeddings_a = [
        [0.8, 0.2, 0.1, 0.3],  # ML focused
        [0.7, 0.3, 0.2, 0.5],  # DL focused
        [0.3, 0.1, 0.9, 0.2],  # NLP focused
    ]

    # Chunks from Config B (smaller chunks)
    chunks_b = [
        "Machine learning enables systems to learn from data.",
        "It is a subset of artificial intelligence.",
        "Deep learning uses neural networks.",
        "Neural networks have many layers for pattern recognition.",
        "NLP helps computers understand language.",
    ]

    embeddings_b = [
        [0.75, 0.25, 0.1, 0.35],
        [0.6, 0.15, 0.1, 0.25],
        [0.65, 0.35, 0.2, 0.45],
        [0.5, 0.25, 0.15, 0.55],
        [0.35, 0.1, 0.85, 0.25],
    ]

    evaluator.add_embeddings("large_chunks", chunks_a, embeddings_a, "text-embedding-3-small")
    evaluator.add_embeddings("small_chunks", chunks_b, embeddings_b, "text-embedding-3-small")

    # Test retrieval with a query
    print("\n🔍 Retrieval Test:")
    query_vector = [0.7, 0.25, 0.15, 0.4]  # Query about ML/DL
    print(f"  Query vector: {query_vector}")

    print("\n  Results from 'large_chunks':")
    results_a = evaluator.find_similar("large_chunks", query_vector, top_k=3)
    for idx, sim, chunk in results_a:
        print(f"    [{sim:.4f}] {chunk[:50]}...")

    print("\n  Results from 'small_chunks':")
    results_b = evaluator.find_similar("small_chunks", query_vector, top_k=3)
    for idx, sim, chunk in results_b:
        print(f"    [{sim:.4f}] {chunk[:50]}...")

    # Generate comparison report
    report = evaluator.generate_report()

    print("\n📊 Configuration Details:")
    for config_name, details in report["config_details"].items():
        print(f"\n  {config_name}:")
        print(f"    Model: {details['model']}")
        print(f"    Chunks: {details['num_chunks']}")
        print(f"    Avg chunk length: {details['avg_chunk_length']:.1f} chars")

    return report


# =============================================================================
# Example 4: Full Benchmark Suite
# =============================================================================

def example_full_benchmark():
    """
    Run a complete benchmark suite comparing multiple configurations.
    """
    print("\n" + "=" * 60)
    print("Example 4: Full Benchmark Suite")
    print("=" * 60)

    # Define custom configurations
    configs = [
        BenchmarkConfig(
            name="speed_optimized",
            parser_config={"pdf": {"engine": "pymupdf", "ocr_enabled": False}},
            chunker_config={"strategy": "fixed_size", "chunk_size": 512},
            enable_ocr=False,
        ),
        BenchmarkConfig(
            name="quality_optimized",
            parser_config={"pdf": {"engine": "pdfplumber", "ocr_enabled": True}},
            chunker_config={"strategy": "recursive", "chunk_size": 400, "overlap": 80},
            enable_ocr=True,
            extract_tables=True,
        ),
        BenchmarkConfig(
            name="rag_optimized",
            parser_config={"pdf": {"engine": "pymupdf", "ocr_enabled": True}},
            chunker_config={"strategy": "semantic", "chunk_size": 512},
            enable_ocr=True,
            embedding_config={"model": "text-embedding-3-small"},
        ),
    ]

    print("\n📋 Benchmark Configurations:")
    for config in configs:
        print(f"\n  {config.name}:")
        print(f"    Parser: {config.parser_config}")
        print(f"    Chunker: {config.chunker_config}")
        print(f"    OCR: {config.enable_ocr}")

    # Note: In real usage, you would run actual benchmarks like this:
    # runner = BenchmarkRunner(
    #     parse_fn=my_parse_function,
    #     chunk_fn=my_chunk_function,
    # )
    # suite = runner.run(configs, documents, ground_truth)

    print("\n💡 Default benchmark configurations available:")
    default_configs = create_default_configs()
    for config in default_configs:
        print(f"  - {config.name}")

    return configs


# =============================================================================
# Example 5: A/B Test with Ground Truth
# =============================================================================

def example_ab_test():
    """
    Perform A/B testing between two configurations with ground truth evaluation.
    """
    print("\n" + "=" * 60)
    print("Example 5: A/B Testing with Ground Truth")
    print("=" * 60)

    # Ground truth for evaluation
    ground_truth = {
        "doc1.pdf": "Artificial intelligence is revolutionizing healthcare. Machine learning models can now diagnose diseases with high accuracy.",
        "doc2.pdf": "Climate change poses significant challenges. Renewable energy sources are becoming more cost-effective.",
    }

    # Simulated results from Config A
    results_a = {
        "doc1.pdf": "Artificial intelligence is revolutionizing healthcare. Machine learning models can now diagnose diseases with high accuracy.",
        "doc2.pdf": "Climate change poses significant challenges. Renewable energy sources are becoming more cost effective.",  # Missing hyphen
    }

    # Simulated results from Config B
    results_b = {
        "doc1.pdf": "Artificial intelligence is revolutionizing healthcare. ML models can diagnose diseases.",  # Abbreviated, missing words
        "doc2.pdf": "Climate change poses significant challenges. Renewable energy sources are becoming more cost-effective.",
    }

    print("\n📊 A/B Test Results:\n")

    for doc_name in ground_truth.keys():
        gt = ground_truth[doc_name]
        text_a = results_a[doc_name]
        text_b = results_b[doc_name]

        metrics_a = calculate_extraction_metrics(text_a, gt)
        metrics_b = calculate_extraction_metrics(text_b, gt)

        print(f"Document: {doc_name}")
        print(f"  Config A - F1: {metrics_a.f1_score:.4f}, BLEU: {metrics_a.bleu_score:.4f}")
        print(f"  Config B - F1: {metrics_b.f1_score:.4f}, BLEU: {metrics_b.bleu_score:.4f}")

        winner = "A" if metrics_a.f1_score > metrics_b.f1_score else "B"
        print(f"  Winner: Config {winner}")
        print()

    return ground_truth


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all examples."""
    print("\n🚀 Document Parser Evaluation Examples\n")

    # Run examples
    example_basic_comparison()
    example_chunking_comparison()
    example_embedding_comparison()
    example_full_benchmark()
    example_ab_test()

    print("\n" + "=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
