"""Rerank Team 1 candidates without changing their content or metadata.

Only results order changes. Original retrieval rank/score remain intact;
rerank_with_details() exposes model scores separately for diagnostics.
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import math
from dataclasses import dataclass
from functools import lru_cache
from numbers import Real
from pathlib import Path
import re
from typing import Callable, Mapping, Sequence
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)
PairScorer = Callable[[list[tuple[str, str]]], Sequence[float]]
_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_LIMITS = {
    "chunk_id": 200, "document_id": 200, "article_id": 100,
    "content": 20000, "document_title": 500, "article": 100,
    "clause": 100, "point": 100, "source_url": 2048,
}
_FIELDS = set(_LIMITS) | {"score", "rank", "retrieval_method"}


class RerankInputError(ValueError):
    """Invalid upstream input; never hidden by model fallback."""


class RerankModelError(RuntimeError):
    """Model unavailable, input too long, or invalid model scores."""


@dataclass(frozen=True)
class RerankDetails:
    output: dict
    scores: dict[str, float]
    fallback_reason: str | None = None


def _validate(payload: Mapping) -> None:
    if not isinstance(payload, Mapping) or set(payload) != {"question", "results"}:
        raise RerankInputError("Expected exactly question and results.")
    q, rows = payload["question"], payload["results"]
    if not isinstance(q, str) or not q.strip() or len(q) > 4000:
        raise RerankInputError("question must contain 1–4000 characters.")
    if not isinstance(rows, list) or len(rows) > 50:
        raise RerankInputError("results must be a list of at most 50 candidates.")
    seen = set()
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, Mapping) or set(item) != _FIELDS:
            raise RerankInputError(f"Candidate {index} must have all 12 contract fields.")
        for key, limit in _LIMITS.items():
            value = item[key]
            if key in {"clause", "point"} and value is None:
                continue
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise RerankInputError(f"Candidate {index}: invalid {key}.")
        for key in ("document_id", "article_id"):
            if not _ID.fullmatch(item[key]):
                raise RerankInputError(f"Candidate {index}: invalid {key} format.")
        try:
            url = urlsplit(item["source_url"])
            valid_url = (item["source_url"].startswith("https://") and url.hostname
                         and not any(c.isspace() for c in item["source_url"]))
        except ValueError:
            valid_url = False
        if not valid_url:
            raise RerankInputError(f"Candidate {index}: source_url must be absolute HTTPS.")
        score, rank = item["score"], item["rank"]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
            raise RerankInputError(f"Candidate {index}: score must be finite.")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank != index:
            raise RerankInputError("Input ranks must be 1..N in retrieval order.")
        if item["retrieval_method"] not in ("bm25", "dense", "hybrid_rrf"):
            raise RerankInputError(f"Candidate {index}: invalid retrieval_method.")
        if item["chunk_id"] in seen:
            raise RerankInputError("Duplicate chunk_id in retrieval output.")
        seen.add(item["chunk_id"])


class BGEScorer:
    """Lazy CPU adapter for BAAI/bge-reranker-v2-m3; no silent truncation.

    The first nonempty call downloads/loads the model. Unit tests inject a
    scorer instead, so importing this module never loads torch or a model.
    """

    def __init__(self, *, batch_size: int = 2, max_length: int = 512):
        if type(batch_size) is not int or batch_size < 1:
            raise ValueError("batch_size must be a positive integer.")
        if type(max_length) is not int or not 1 <= max_length <= 512:
            raise ValueError("max_length must be between 1 and 512.")
        self.batch_size = batch_size
        self.max_length = max_length
        self._tokenizer = self._model = self._torch = None

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise RerankModelError('Install model packages with pip install -e ".[reranker]".') from exc
        name = "BAAI/bge-reranker-v2-m3"
        tokenizer = AutoTokenizer.from_pretrained(name, trust_remote_code=False)
        model = AutoModelForSequenceClassification.from_pretrained(
            name, trust_remote_code=False, use_safetensors=True,
        )
        model.to("cpu")
        model.eval()
        self._torch, self._tokenizer, self._model = torch, tokenizer, model

    def __call__(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        self._load()
        scores = []
        for offset in range(0, len(pairs), self.batch_size):
            batch = pairs[offset:offset + self.batch_size]
            encoded = self._tokenizer(
                [q for q, _ in batch], [text for _, text in batch],
                padding=False, truncation=False,
            )
            if any(len(ids) > self.max_length for ids in encoded["input_ids"]):
                raise RerankModelError("A question/content pair exceeds the model token limit.")
            inputs = self._tokenizer.pad(encoded, padding=True, return_tensors="pt")
            with self._torch.inference_mode():
                logits = self._model(**inputs, return_dict=True).logits
            scores.extend(logits.reshape(-1).float().cpu().tolist())
        return scores


@lru_cache(maxsize=1)
def _default_scorer() -> BGEScorer:
    return BGEScorer()


def rerank_with_details(
    retrieval_output: Mapping, *, scorer: PairScorer | None = None, strict: bool = False,
) -> RerankDetails:
    """Validate retrieval input, score pairs, and return a copied full pool.

    Input/contract errors always raise. Inference failure falls back to the
    original pool unless strict=True. No partial scores survive a failure.
    """
    _validate(retrieval_output)
    output = copy.deepcopy(dict(retrieval_output))
    rows = output["results"]
    if not rows:
        return RerankDetails(output, {})
    pairs = [(output["question"], item["content"]) for item in rows]
    try:
        raw_scores = list((scorer if scorer is not None else _default_scorer())(pairs))
        if len(raw_scores) != len(rows):
            raise RerankModelError("The number of model scores does not match the candidate pool.")
        if any(isinstance(s, bool) or not isinstance(s, Real) or not math.isfinite(s) for s in raw_scores):
            raise RerankModelError("Model scores must be finite numbers.")
        scores = {row["chunk_id"]: float(score) for row, score in zip(rows, raw_scores)}
    except Exception as exc:
        # Keep diagnostics free of query text, content, and raw provider messages.
        reason = type(exc).__name__
        if strict:
            raise RerankModelError(f"Reranking failed ({reason}).") from exc
        logger.warning("reranker fallback reason=%s candidates=%d", reason, len(rows))
        return RerankDetails(output, {}, reason)
    rows.sort(key=lambda row: (-scores[row["chunk_id"]], row["rank"]))
    return RerankDetails(output, scores)


def rerank(
    retrieval_output: Mapping, *, scorer: PairScorer | None = None, strict: bool = False,
) -> dict:
    """Public interface: rerank(retrieval_output) -> {question, results}.

    results is in rerank order, but each candidate's rank remains its original
    retrieval rank. Context Builder must iterate the list without sorting rank.
    """
    return rerank_with_details(retrieval_output, scorer=scorer, strict=strict).output


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Retrieval Output JSON file")
    parser.add_argument("--mock", action="store_true", help="Reverse order using fake scores; no model")
    parser.add_argument("--strict", action="store_true", help="Fail instead of falling back")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    fake = (lambda pairs: list(range(len(pairs)))) if args.mock else None
    details = rerank_with_details(payload, scorer=fake, strict=args.strict)
    print(json.dumps({"mode": "mock" if args.mock else "bge",
                      "scores": details.scores, "fallback_reason": details.fallback_reason,
                      "output": details.output}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()
