from __future__ import annotations

from collections.abc import Sequence
from numbers import Real
from time import monotonic


from concurrent.futures import ThreadPoolExecutor, TimeoutError
from math import isfinite

from .common import MAX_TOP_K, validate_query
from .errors import RetrievalUnavailableError

CANDIDATE_LIMIT = 100
RETRIEVAL_TIMEOUT = 5
# BM25 : Dense, chọn theo VLRA-53 (team1_data/retrieval/retrieval_v2.json).
DEFAULT_WEIGHTS = (0.5, 1.0)


def rrf_fuse(
    ranked_lists: Sequence[Sequence[dict]],
    k: int = 60,
    weights: Sequence[float] | None = None,
    top_k: int = 20,
) -> list[dict]:
    """Gộp các danh sách kết quả đã xếp hạng bằng Reciprocal Rank Fusion."""
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("k must be a positive integer")

    if (
        isinstance(top_k, bool)
        or not isinstance(top_k, int)
        or not 1 <= top_k <= MAX_TOP_K
    ):
        raise ValueError(f"top_k must be an integer from 1 to {MAX_TOP_K}")

    if weights is None:
        weights = [1.0] * len(ranked_lists)

    if len(weights) != len(ranked_lists):
        raise ValueError("weights and ranked_lists must have the same length")

    scores: dict[str, float] = {}
    best_ranks: dict[str, int] = {}
    chunks: dict[str, dict] = {}

    for results, weight in zip(ranked_lists, weights):
        if isinstance(weight, bool) or not isinstance(weight, Real):
            raise ValueError("weights must be real numbers")
        if weight < 0:
            raise ValueError("weights must be non-negative")

        seen: set[str] = set()

        for rank, row in enumerate(results, start=1):
            chunk_id = row["chunk_id"]

            # Không tính trùng một chunk nhiều lần trong cùng một nhánh.
            if chunk_id in seen:
                continue
            seen.add(chunk_id)

            scores[chunk_id] = (
                scores.get(chunk_id, 0.0) + float(weight) / (k + rank)
            )
            best_ranks[chunk_id] = min(
                best_ranks.get(chunk_id, rank), rank
            )
            chunks.setdefault(chunk_id, row)

    ordered_ids = sorted(
        scores,
        key=lambda chunk_id: (
            -scores[chunk_id],
            best_ranks[chunk_id],
            chunk_id,
        ),
    )

    fused = []
    for rank, chunk_id in enumerate(ordered_ids[:top_k], start=1):
        row = dict(chunks[chunk_id])
        row["score"] = scores[chunk_id]
        row["rank"] = rank
        row["retrieval_method"] = "hybrid_rrf"
        fused.append(row)

    return fused

class HybridRetriever:
    """Kết hợp BM25 và Dense bằng Reciprocal Rank Fusion."""

    def __init__(
        self,
        bm25_retriever,
        dense_retriever,
        rrf_k: int = 60,
        weights: Sequence[float] = DEFAULT_WEIGHTS,
        timeout: float = RETRIEVAL_TIMEOUT,
    ):
        if isinstance(rrf_k, bool) or not isinstance(rrf_k, int) or rrf_k < 1:
            raise ValueError("rrf_k must be a positive integer")
        if len(weights) != 2:
            raise ValueError("weights must contain BM25 and Dense weights")
        if (
            not isfinite(timeout)
            or isinstance(timeout, bool)
            or timeout <= 0
        ):
            raise ValueError("timeout must be positive and finite")

        self.bm25_retriever = bm25_retriever
        self.dense_retriever = dense_retriever
        self.rrf_k = rrf_k
        self.weights = tuple(weights)
        self.timeout = timeout

    
    def retrieve(self, question: str, top_k: int = 20) -> dict:
        question = validate_query(question, top_k)

        executor = ThreadPoolExecutor(max_workers=2)
        start = monotonic()

        try:
            bm25_future = executor.submit(
                self.bm25_retriever._search,
                question,
                CANDIDATE_LIMIT,
            )
            dense_future = executor.submit(
                self.dense_retriever._search,
                question,
                CANDIDATE_LIMIT,
            )

            bm25_results = bm25_future.result(timeout=self.timeout)

            remaining = self.timeout - (monotonic() - start)
            if remaining <= 0:
                raise TimeoutError()

            dense_results = dense_future.result(timeout=remaining)

        except TimeoutError as exc:
            raise RetrievalUnavailableError(
                "Hybrid retrieval timed out"
            ) from exc

        except Exception as exc:
            raise RetrievalUnavailableError(
                "A retrieval branch failed"
            ) from exc

        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        results = rrf_fuse(
            [bm25_results, dense_results],
            k=self.rrf_k,
            weights=self.weights,
            top_k=top_k,
        )

        return {"question": question, "results": results}

