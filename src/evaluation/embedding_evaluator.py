"""
Embedding evaluation module for comparing embedding quality across configurations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
import math
import json
from pathlib import Path


@dataclass
class EmbeddingComparisonResult:
    """Result of comparing embeddings between two configurations."""

    config_a: str
    config_b: str

    # Similarity metrics
    avg_cosine_similarity: float = 0.0  # How similar are the embeddings?
    correlation: float = 0.0  # Pearson correlation

    # Retrieval comparison
    retrieval_agreement: float = 0.0  # How often do they retrieve same docs?
    ranking_correlation: float = 0.0  # Spearman correlation of rankings

    # Per-query comparison
    query_comparisons: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_a": self.config_a,
            "config_b": self.config_b,
            "avg_cosine_similarity": round(self.avg_cosine_similarity, 4),
            "correlation": round(self.correlation, 4),
            "retrieval_agreement": round(self.retrieval_agreement, 4),
            "ranking_correlation": round(self.ranking_correlation, 4),
            "num_query_comparisons": len(self.query_comparisons),
        }


@dataclass
class RetrievalEvaluation:
    """Evaluation results for retrieval quality."""

    config_name: str
    model_name: str

    # Retrieval metrics
    recall_at_1: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_1: float = 0.0
    precision_at_5: float = 0.0
    precision_at_10: float = 0.0
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg_at_10: float = 0.0  # Normalized DCG

    # Query-level results
    num_queries: int = 0
    query_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "config_name": self.config_name,
            "model_name": self.model_name,
            "recall@1": round(self.recall_at_1, 4),
            "recall@5": round(self.recall_at_5, 4),
            "recall@10": round(self.recall_at_10, 4),
            "precision@1": round(self.precision_at_1, 4),
            "precision@5": round(self.precision_at_5, 4),
            "precision@10": round(self.precision_at_10, 4),
            "mrr": round(self.mrr, 4),
            "ndcg@10": round(self.ndcg_at_10, 4),
            "num_queries": self.num_queries,
        }


class EmbeddingEvaluator:
    """
    Evaluate and compare embedding quality for RAG applications.

    Usage:
        evaluator = EmbeddingEvaluator()

        # Add embeddings from different configs
        evaluator.add_embeddings("config_a", chunks_a, embeddings_a, model="text-embedding-3-small")
        evaluator.add_embeddings("config_b", chunks_b, embeddings_b, model="text-embedding-3-small")

        # Evaluate retrieval quality
        queries = [("What is X?", ["relevant_chunk_1", "relevant_chunk_2"])]
        eval_result = evaluator.evaluate_retrieval("config_a", queries)

        # Compare embeddings between configs
        comparison = evaluator.compare_embeddings("config_a", "config_b")
    """

    def __init__(self):
        self.embeddings: Dict[str, Dict[str, Any]] = {}
        # Structure: {config_name: {"chunks": [...], "vectors": [...], "model": str}}

    def add_embeddings(
        self,
        config_name: str,
        chunks: List[str],
        vectors: List[List[float]],
        model: str = "unknown",
    ) -> None:
        """
        Add embeddings for a configuration.

        Args:
            config_name: Name of the configuration
            chunks: List of text chunks
            vectors: List of embedding vectors
            model: Name of the embedding model used
        """
        if len(chunks) != len(vectors):
            raise ValueError(
                f"Number of chunks ({len(chunks)}) must match "
                f"number of vectors ({len(vectors)})"
            )

        self.embeddings[config_name] = {
            "chunks": chunks,
            "vectors": vectors,
            "model": model,
            "dim": len(vectors[0]) if vectors else 0,
        }

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    @staticmethod
    def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance between two vectors."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))

    def find_similar(
        self,
        config_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Tuple[int, float, str]]:
        """
        Find most similar chunks to a query vector.

        Args:
            config_name: Configuration to search in
            query_vector: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of (index, similarity, chunk_text) tuples
        """
        if config_name not in self.embeddings:
            raise ValueError(f"Unknown configuration: {config_name}")

        data = self.embeddings[config_name]
        similarities = []

        for i, vec in enumerate(data["vectors"]):
            sim = self.cosine_similarity(query_vector, vec)
            similarities.append((i, sim, data["chunks"][i]))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def evaluate_retrieval(
        self,
        config_name: str,
        queries: List[Tuple[str, List[str]]],
        embed_fn: Callable[[str], List[float]],
        top_k_values: List[int] = [1, 5, 10],
    ) -> RetrievalEvaluation:
        """
        Evaluate retrieval quality using ground truth queries.

        Args:
            config_name: Configuration to evaluate
            queries: List of (query_text, relevant_chunks) tuples
            embed_fn: Function to embed query text
            top_k_values: K values for recall/precision calculation

        Returns:
            RetrievalEvaluation with metrics
        """
        if config_name not in self.embeddings:
            raise ValueError(f"Unknown configuration: {config_name}")

        data = self.embeddings[config_name]
        evaluation = RetrievalEvaluation(
            config_name=config_name,
            model_name=data["model"],
            num_queries=len(queries),
        )

        recalls = {k: [] for k in top_k_values}
        precisions = {k: [] for k in top_k_values}
        reciprocal_ranks = []
        ndcg_scores = []

        for query_text, relevant_chunks in queries:
            query_vec = embed_fn(query_text)
            results = self.find_similar(config_name, query_vec, max(top_k_values))
            retrieved_chunks = [r[2] for r in results]

            # Calculate metrics for this query
            relevant_set = set(relevant_chunks)
            query_result = {
                "query": query_text,
                "relevant_count": len(relevant_chunks),
                "results": [],
            }

            # Recall and Precision at K
            for k in top_k_values:
                retrieved_at_k = set(retrieved_chunks[:k])
                relevant_retrieved = retrieved_at_k & relevant_set
                recall = len(relevant_retrieved) / len(relevant_set) if relevant_set else 0
                precision = len(relevant_retrieved) / k
                recalls[k].append(recall)
                precisions[k].append(precision)

            # Mean Reciprocal Rank
            rr = 0.0
            for rank, chunk in enumerate(retrieved_chunks, 1):
                if chunk in relevant_set:
                    rr = 1.0 / rank
                    break
            reciprocal_ranks.append(rr)

            # NDCG@10
            dcg = 0.0
            idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant_set), 10)))
            for rank, chunk in enumerate(retrieved_chunks[:10], 1):
                if chunk in relevant_set:
                    dcg += 1.0 / math.log2(rank + 1)
            ndcg = dcg / idcg if idcg > 0 else 0
            ndcg_scores.append(ndcg)

            query_result["mrr"] = rr
            query_result["ndcg@10"] = ndcg
            evaluation.query_results.append(query_result)

        # Aggregate metrics
        evaluation.recall_at_1 = sum(recalls[1]) / len(recalls[1]) if recalls[1] else 0
        evaluation.recall_at_5 = sum(recalls[5]) / len(recalls[5]) if recalls[5] else 0
        evaluation.recall_at_10 = sum(recalls[10]) / len(recalls[10]) if recalls[10] else 0
        evaluation.precision_at_1 = sum(precisions[1]) / len(precisions[1]) if precisions[1] else 0
        evaluation.precision_at_5 = sum(precisions[5]) / len(precisions[5]) if precisions[5] else 0
        evaluation.precision_at_10 = sum(precisions[10]) / len(precisions[10]) if precisions[10] else 0
        evaluation.mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0
        evaluation.ndcg_at_10 = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0

        return evaluation

    def compare_embeddings(
        self,
        config_a: str,
        config_b: str,
    ) -> EmbeddingComparisonResult:
        """
        Compare embeddings between two configurations.

        Args:
            config_a: First configuration
            config_b: Second configuration

        Returns:
            EmbeddingComparisonResult with comparison metrics
        """
        if config_a not in self.embeddings:
            raise ValueError(f"Unknown configuration: {config_a}")
        if config_b not in self.embeddings:
            raise ValueError(f"Unknown configuration: {config_b}")

        data_a = self.embeddings[config_a]
        data_b = self.embeddings[config_b]

        result = EmbeddingComparisonResult(config_a=config_a, config_b=config_b)

        # Find matching chunks (by content)
        chunks_a = {chunk: i for i, chunk in enumerate(data_a["chunks"])}
        matching_pairs = []

        for i, chunk_b in enumerate(data_b["chunks"]):
            if chunk_b in chunks_a:
                idx_a = chunks_a[chunk_b]
                matching_pairs.append((idx_a, i))

        if not matching_pairs:
            return result

        # Calculate average cosine similarity for matching chunks
        similarities = []
        for idx_a, idx_b in matching_pairs:
            sim = self.cosine_similarity(
                data_a["vectors"][idx_a], data_b["vectors"][idx_b]
            )
            similarities.append(sim)

        result.avg_cosine_similarity = sum(similarities) / len(similarities)

        # Calculate correlation
        if len(matching_pairs) > 2:
            # Flatten vectors for correlation
            vecs_a = [data_a["vectors"][i] for i, _ in matching_pairs]
            vecs_b = [data_b["vectors"][j] for _, j in matching_pairs]

            result.correlation = self._pearson_correlation_vectors(vecs_a, vecs_b)

        return result

    @staticmethod
    def _pearson_correlation_vectors(
        vecs_a: List[List[float]], vecs_b: List[List[float]]
    ) -> float:
        """Calculate average Pearson correlation between vector pairs."""
        if not vecs_a or not vecs_b:
            return 0.0

        correlations = []
        for va, vb in zip(vecs_a, vecs_b):
            mean_a = sum(va) / len(va)
            mean_b = sum(vb) / len(vb)

            num = sum((a - mean_a) * (b - mean_b) for a, b in zip(va, vb))
            den_a = math.sqrt(sum((a - mean_a) ** 2 for a in va))
            den_b = math.sqrt(sum((b - mean_b) ** 2 for b in vb))

            if den_a > 0 and den_b > 0:
                correlations.append(num / (den_a * den_b))

        return sum(correlations) / len(correlations) if correlations else 0.0

    def compare_retrieval(
        self,
        config_a: str,
        config_b: str,
        query_vectors: List[List[float]],
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Compare retrieval results between two configurations.

        Args:
            config_a: First configuration
            config_b: Second configuration
            query_vectors: Query embedding vectors
            top_k: Number of results to compare

        Returns:
            Dictionary with comparison metrics
        """
        agreements = []
        ranking_correlations = []

        for query_vec in query_vectors:
            results_a = self.find_similar(config_a, query_vec, top_k)
            results_b = self.find_similar(config_b, query_vec, top_k)

            # Calculate set agreement (Jaccard similarity of retrieved sets)
            set_a = {r[2] for r in results_a}
            set_b = {r[2] for r in results_b}
            intersection = len(set_a & set_b)
            union = len(set_a | set_b)
            agreement = intersection / union if union > 0 else 0
            agreements.append(agreement)

            # Calculate ranking correlation (for common items)
            common_chunks = set_a & set_b
            if len(common_chunks) > 2:
                ranks_a = {r[2]: i for i, r in enumerate(results_a) if r[2] in common_chunks}
                ranks_b = {r[2]: i for i, r in enumerate(results_b) if r[2] in common_chunks}

                # Spearman correlation
                rank_pairs = [(ranks_a[c], ranks_b[c]) for c in common_chunks]
                corr = self._spearman_correlation(rank_pairs)
                ranking_correlations.append(corr)

        return {
            "avg_agreement": sum(agreements) / len(agreements) if agreements else 0,
            "avg_ranking_correlation": (
                sum(ranking_correlations) / len(ranking_correlations)
                if ranking_correlations
                else 0
            ),
            "num_queries": len(query_vectors),
        }

    @staticmethod
    def _spearman_correlation(rank_pairs: List[Tuple[int, int]]) -> float:
        """Calculate Spearman rank correlation."""
        n = len(rank_pairs)
        if n < 2:
            return 0.0

        d_squared_sum = sum((a - b) ** 2 for a, b in rank_pairs)
        return 1 - (6 * d_squared_sum) / (n * (n ** 2 - 1))

    def generate_report(self, output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive embedding evaluation report.

        Args:
            output_path: Optional path to save report JSON

        Returns:
            Report dictionary
        """
        report = {
            "configs": list(self.embeddings.keys()),
            "config_details": {},
            "comparisons": [],
        }

        # Config details
        for config_name, data in self.embeddings.items():
            report["config_details"][config_name] = {
                "model": data["model"],
                "dim": data["dim"],
                "num_chunks": len(data["chunks"]),
                "avg_chunk_length": (
                    sum(len(c) for c in data["chunks"]) / len(data["chunks"])
                    if data["chunks"]
                    else 0
                ),
            }

        # Pairwise comparisons
        configs = list(self.embeddings.keys())
        for i, config_a in enumerate(configs):
            for config_b in configs[i + 1 :]:
                comparison = self.compare_embeddings(config_a, config_b)
                report["comparisons"].append(comparison.to_dict())

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

        return report
