"""
Evaluation metrics for document parsing quality assessment.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Sequence
import re
from difflib import SequenceMatcher
from collections import Counter
import math


@dataclass
class TextExtractionMetrics:
    """Metrics for evaluating text extraction quality."""

    # Basic metrics
    char_count: int = 0
    word_count: int = 0
    line_count: int = 0
    paragraph_count: int = 0

    # Quality metrics (compared to ground truth)
    precision: float = 0.0  # Correctly extracted / Total extracted
    recall: float = 0.0  # Correctly extracted / Total in ground truth
    f1_score: float = 0.0  # Harmonic mean of precision and recall

    # Similarity metrics
    char_similarity: float = 0.0  # Character-level similarity
    word_similarity: float = 0.0  # Word-level similarity
    bleu_score: float = 0.0  # BLEU score for text quality

    # Error analysis
    missing_words: List[str] = field(default_factory=list)
    extra_words: List[str] = field(default_factory=list)
    error_rate: float = 0.0  # Word error rate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "char_count": self.char_count,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "paragraph_count": self.paragraph_count,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "char_similarity": round(self.char_similarity, 4),
            "word_similarity": round(self.word_similarity, 4),
            "bleu_score": round(self.bleu_score, 4),
            "error_rate": round(self.error_rate, 4),
            "missing_words_count": len(self.missing_words),
            "extra_words_count": len(self.extra_words),
        }


@dataclass
class ChunkingMetrics:
    """Metrics for evaluating chunking quality."""

    # Basic stats
    total_chunks: int = 0
    total_tokens: int = 0
    avg_chunk_size: float = 0.0
    min_chunk_size: int = 0
    max_chunk_size: int = 0
    std_chunk_size: float = 0.0

    # Distribution
    chunk_sizes: List[int] = field(default_factory=list)
    size_distribution: Dict[str, int] = field(default_factory=dict)

    # Quality metrics
    coverage: float = 0.0  # Total chunked text / Original text
    overlap_ratio: float = 0.0  # Average overlap between consecutive chunks
    semantic_coherence: float = 0.0  # Average semantic similarity within chunks

    # Boundary analysis
    sentence_boundary_ratio: float = 0.0  # Chunks ending at sentence boundaries
    paragraph_boundary_ratio: float = 0.0  # Chunks ending at paragraph boundaries

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_chunks": self.total_chunks,
            "total_tokens": self.total_tokens,
            "avg_chunk_size": round(self.avg_chunk_size, 2),
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
            "std_chunk_size": round(self.std_chunk_size, 2),
            "coverage": round(self.coverage, 4),
            "overlap_ratio": round(self.overlap_ratio, 4),
            "semantic_coherence": round(self.semantic_coherence, 4),
            "sentence_boundary_ratio": round(self.sentence_boundary_ratio, 4),
            "paragraph_boundary_ratio": round(self.paragraph_boundary_ratio, 4),
            "size_distribution": self.size_distribution,
        }


@dataclass
class EmbeddingMetrics:
    """Metrics for evaluating embedding quality."""

    # Basic info
    embedding_dim: int = 0
    num_embeddings: int = 0
    model_name: str = ""

    # Quality metrics
    avg_magnitude: float = 0.0  # Average vector magnitude
    variance: float = 0.0  # Variance in embeddings

    # Retrieval metrics (when ground truth is available)
    recall_at_k: Dict[int, float] = field(default_factory=dict)  # R@1, R@5, R@10
    precision_at_k: Dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg: float = 0.0  # Normalized Discounted Cumulative Gain

    # Similarity distribution
    avg_intra_similarity: float = 0.0  # Avg similarity within same document
    avg_inter_similarity: float = 0.0  # Avg similarity across documents
    similarity_distribution: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "embedding_dim": self.embedding_dim,
            "num_embeddings": self.num_embeddings,
            "model_name": self.model_name,
            "avg_magnitude": round(self.avg_magnitude, 4),
            "variance": round(self.variance, 4),
            "recall_at_k": {k: round(v, 4) for k, v in self.recall_at_k.items()},
            "precision_at_k": {k: round(v, 4) for k, v in self.precision_at_k.items()},
            "mrr": round(self.mrr, 4),
            "ndcg": round(self.ndcg, 4),
            "avg_intra_similarity": round(self.avg_intra_similarity, 4),
            "avg_inter_similarity": round(self.avg_inter_similarity, 4),
        }


def calculate_text_similarity(text1: str, text2: str, method: str = "sequence") -> float:
    """
    Calculate similarity between two texts.

    Args:
        text1: First text
        text2: Second text
        method: Similarity method ('sequence', 'jaccard', 'cosine')

    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    if method == "sequence":
        return SequenceMatcher(None, text1, text2).ratio()

    elif method == "jaccard":
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    elif method == "cosine":
        words1 = text1.lower().split()
        words2 = text2.lower().split()
        counter1 = Counter(words1)
        counter2 = Counter(words2)

        all_words = set(counter1.keys()) | set(counter2.keys())
        vec1 = [counter1.get(w, 0) for w in all_words]
        vec2 = [counter2.get(w, 0) for w in all_words]

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    else:
        raise ValueError(f"Unknown similarity method: {method}")


def calculate_bleu_score(
    reference: str,
    candidate: str,
    max_n: int = 4,
    weights: Optional[Sequence[float]] = None,
) -> float:
    """
    Calculate BLEU score for text quality evaluation.

    Args:
        reference: Reference (ground truth) text
        candidate: Candidate (extracted) text
        max_n: Maximum n-gram size
        weights: Weights for each n-gram (default: uniform)

    Returns:
        BLEU score between 0 and 1
    """
    if weights is None:
        weights = [1.0 / max_n] * max_n

    def get_ngrams(text: str, n: int) -> Counter:
        words = text.lower().split()
        return Counter(tuple(words[i : i + n]) for i in range(len(words) - n + 1))

    ref_words = reference.lower().split()
    cand_words = candidate.lower().split()

    if len(cand_words) == 0:
        return 0.0

    # Brevity penalty
    bp = 1.0
    if len(cand_words) < len(ref_words):
        bp = math.exp(1 - len(ref_words) / len(cand_words))

    # N-gram precisions
    precisions = []
    for n in range(1, max_n + 1):
        ref_ngrams = get_ngrams(reference, n)
        cand_ngrams = get_ngrams(candidate, n)

        if not cand_ngrams:
            precisions.append(0.0)
            continue

        matches = sum(
            min(cand_ngrams[ng], ref_ngrams.get(ng, 0)) for ng in cand_ngrams
        )
        total = sum(cand_ngrams.values())
        precisions.append(matches / total if total > 0 else 0.0)

    # Geometric mean with weights
    if any(p == 0 for p in precisions):
        return 0.0

    log_precisions = [w * math.log(p) for w, p in zip(weights, precisions) if p > 0]
    return bp * math.exp(sum(log_precisions))


def calculate_word_error_rate(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate (WER) using Levenshtein distance.

    Args:
        reference: Reference text
        hypothesis: Hypothesis (extracted) text

    Returns:
        WER score (lower is better, 0 = perfect)
    """
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    if len(ref_words) == 0:
        return 1.0 if len(hyp_words) > 0 else 0.0

    # Dynamic programming for edit distance
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(
                    d[i - 1][j] + 1,  # deletion
                    d[i][j - 1] + 1,  # insertion
                    d[i - 1][j - 1] + 1,  # substitution
                )

    return d[len(ref_words)][len(hyp_words)] / len(ref_words)


def calculate_extraction_metrics(
    extracted_text: str,
    ground_truth: Optional[str] = None,
) -> TextExtractionMetrics:
    """
    Calculate comprehensive text extraction metrics.

    Args:
        extracted_text: Extracted text from parser
        ground_truth: Optional ground truth text for comparison

    Returns:
        TextExtractionMetrics object
    """
    metrics = TextExtractionMetrics()

    # Basic metrics
    metrics.char_count = len(extracted_text)
    metrics.word_count = len(extracted_text.split())
    metrics.line_count = extracted_text.count("\n") + 1
    metrics.paragraph_count = len(re.split(r"\n\s*\n", extracted_text))

    if ground_truth:
        # Word-level analysis
        extracted_words = set(extracted_text.lower().split())
        truth_words = set(ground_truth.lower().split())

        common_words = extracted_words & truth_words
        metrics.missing_words = list(truth_words - extracted_words)[:100]  # Limit
        metrics.extra_words = list(extracted_words - truth_words)[:100]

        # Precision, Recall, F1
        if len(extracted_words) > 0:
            metrics.precision = len(common_words) / len(extracted_words)
        if len(truth_words) > 0:
            metrics.recall = len(common_words) / len(truth_words)
        if metrics.precision + metrics.recall > 0:
            metrics.f1_score = (
                2 * metrics.precision * metrics.recall
                / (metrics.precision + metrics.recall)
            )

        # Similarity metrics
        metrics.char_similarity = calculate_text_similarity(
            extracted_text, ground_truth, "sequence"
        )
        metrics.word_similarity = calculate_text_similarity(
            extracted_text, ground_truth, "jaccard"
        )
        metrics.bleu_score = calculate_bleu_score(ground_truth, extracted_text)
        metrics.error_rate = calculate_word_error_rate(ground_truth, extracted_text)

    return metrics


def calculate_chunking_metrics(
    chunks: List[str],
    original_text: str,
    token_counter: Optional[callable] = None,
) -> ChunkingMetrics:
    """
    Calculate comprehensive chunking metrics.

    Args:
        chunks: List of text chunks
        original_text: Original text before chunking
        token_counter: Optional function to count tokens (default: word count)

    Returns:
        ChunkingMetrics object
    """
    if token_counter is None:
        token_counter = lambda x: len(x.split())

    metrics = ChunkingMetrics()
    metrics.total_chunks = len(chunks)

    if not chunks:
        return metrics

    # Calculate chunk sizes
    chunk_sizes = [token_counter(chunk) for chunk in chunks]
    metrics.chunk_sizes = chunk_sizes
    metrics.total_tokens = sum(chunk_sizes)
    metrics.avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)
    metrics.min_chunk_size = min(chunk_sizes)
    metrics.max_chunk_size = max(chunk_sizes)

    # Standard deviation
    variance = sum((s - metrics.avg_chunk_size) ** 2 for s in chunk_sizes) / len(
        chunk_sizes
    )
    metrics.std_chunk_size = math.sqrt(variance)

    # Size distribution
    size_ranges = [
        ("tiny", 0, 50),
        ("small", 50, 200),
        ("medium", 200, 500),
        ("large", 500, 1000),
        ("huge", 1000, float("inf")),
    ]
    for name, low, high in size_ranges:
        count = sum(1 for s in chunk_sizes if low <= s < high)
        metrics.size_distribution[name] = count

    # Coverage
    total_chunked_chars = sum(len(c) for c in chunks)
    if len(original_text) > 0:
        metrics.coverage = min(1.0, total_chunked_chars / len(original_text))

    # Boundary analysis
    sentence_end_pattern = re.compile(r"[.!?]\s*$")
    paragraph_end_pattern = re.compile(r"\n\s*$")

    sentence_ends = sum(1 for c in chunks if sentence_end_pattern.search(c))
    paragraph_ends = sum(1 for c in chunks if paragraph_end_pattern.search(c))

    metrics.sentence_boundary_ratio = sentence_ends / len(chunks)
    metrics.paragraph_boundary_ratio = paragraph_ends / len(chunks)

    return metrics
