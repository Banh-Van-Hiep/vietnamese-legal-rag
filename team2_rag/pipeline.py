"""VLRA-38: compose Team 1 retrieval and existing Team 2 modules.

No model or provider is loaded at import time. Dependencies are injected so
tests can exercise the complete flow without pretending to run real models.
"""
from __future__ import annotations

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Protocol

from .answer import NO_CONTEXT_ANSWER, generate_answer
from .llm.service import LLMService
from .llm.errors import LLMBadOutputError
from .llm.output_parser import parse_llm_output
from .reranker import PairScorer, rerank_with_details

log = logging.getLogger(__name__)
_REFERENCE = re.compile(
    r"\b(vừa nêu|vừa nói|nói trên|trường hợp (đó|trên)|công ty (đó|này)|"
    r"doanh nghiệp (đó|này)|như vậy|việc đó)\b", re.IGNORECASE,
)


def validate_generated_response(response, *, response_model=None):
    """Check the final boundary and optionally use Person 2's shared model.

    The legacy parser only recognizes positive markers, so explicitly reject
    malformed C-markers rather than overlooking [C0]/[C01] next to [C1].
    This guard supplements, and does not impersonate, the pending RAGResponse.
    """
    import json
    if response_model is not None:
        checked = response_model.model_validate(response)
        response = checked.model_dump(mode="json")
    if not isinstance(response, Mapping):
        raise LLMBadOutputError("RAG output must be an object")
    parsed = parse_llm_output(json.dumps(response, ensure_ascii=False))
    markers = re.findall(r"\[\s*[Cc][^\[\]\r\n]*\]", parsed.answer)
    if any(not re.fullmatch(r"\[C[1-9][0-9]*\]", marker) for marker in markers):
        raise LLMBadOutputError("Invalid citation marker")
    without_markers = re.sub(r"\[C[1-9][0-9]*\]", "", parsed.answer)
    if re.search(r"\[\s*[Cc](?:\d|\s|$)", without_markers):
        raise LLMBadOutputError("Unclosed citation marker")
    order = list(dict.fromkeys(re.findall(r"\[C([1-9][0-9]*)\]", parsed.answer)))
    expected = [str(i) for i in range(1, len(parsed.citations) + 1)]
    if order != expected or [c.citation_id for c in parsed.citations] != [f"C{i}" for i in expected]:
        raise LLMBadOutputError("Citation markers must be exact, consecutive and in appearance order")
    if len({c.chunk_id for c in parsed.citations}) != len(parsed.citations):
        raise LLMBadOutputError("Duplicate cited chunk")
    return dict(response)


class Retriever(Protocol):
    def retrieve(self, question: str, top_k: int = 20) -> dict: ...


def validate_input(question, history=None):
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 2000:
        raise ValueError("question must contain 1..2000 characters after trimming")
    history = [] if history is None else history
    if not isinstance(history, (list, tuple)) or len(history) > 10 or len(history) % 2:
        raise ValueError("history must contain at most five complete user/assistant pairs")
    turns = []
    for i, turn in enumerate(history):
        if not isinstance(turn, Mapping) or set(turn) != {"role", "content"}:
            raise ValueError("history items must contain exactly role and content")
        if turn["role"] != ("user" if i % 2 == 0 else "assistant"):
            raise ValueError("history must alternate user then assistant")
        if not isinstance(turn["content"], str) or not turn["content"].strip():
            raise ValueError("history content must be a nonempty string")
        turns.append(dict(turn))
    if sum(len(t["content"]) for t in turns) > 20000:
        raise ValueError("history content exceeds 20000 characters")
    return question.strip(), turns


class RAGPipeline:
    def __init__(self, retriever: Retriever, llm_service: LLMService, *,
                 scorer: PairScorer | None = None, top_k: int = 20,
                 settings=None, token_budget=None, response_model=None,
                 strict_rerank: bool = True):
        if type(top_k) is not int or not 1 <= top_k <= 50:
            raise ValueError("top_k must be an integer from 1 to 50")
        self.retriever, self.llm_service = retriever, llm_service
        self.scorer, self.top_k = scorer, top_k
        self.settings, self.token_budget = settings, token_budget
        self.response_model = response_model
        self.strict_rerank = strict_rerank

    def query(self, question: str, history: Sequence[Mapping] | None = None, *, request_id=None):
        question, history = validate_input(question, history)
        # No query rewriter has been agreed yet. Ask instead of inventing a
        # referent or treating a previous assistant answer as legal evidence.
        if _REFERENCE.search(question):
            return {"status": "insufficient_context", "citations": [],
                    "answer": "Bạn hãy nêu rõ doanh nghiệp hoặc tình huống pháp lý cần hỏi để tra cứu đúng nguồn."}
        retrieved = self.retriever.retrieve(question, top_k=self.top_k)
        if not isinstance(retrieved, Mapping) or retrieved.get("question") != question:
            raise ValueError("retrieval must echo the actual query")
        # Graceful degradation (VLRA-T2-16): falls back to retrieval order when strict_rerank=False
        details = rerank_with_details(retrieved, scorer=self.scorer, strict=self.strict_rerank)
        if details.fallback_reason:
            log.warning("reranker_degraded_fallback reason=%s request_id=%s degraded=true",
                        details.fallback_reason, request_id)
        if not details.output["results"]:
            return {"status": "insufficient_context", "answer": NO_CONTEXT_ANSWER, "citations": []}
        response = generate_answer(details.output, history, llm_service=self.llm_service,
                                   settings=self.settings, token_budget=self.token_budget,
                                   request_id=request_id)
        response = validate_generated_response(response, response_model=self.response_model)
        log.info("rag_completed request_id=%s candidates=%d citations=%d status=%s",
                 request_id, len(details.output["results"]), len(response["citations"]), response["status"])
        return response


class BM25SearchAdapter:
    """Normalize the current Team 1 BM25 _search envelope for Hybrid RRF.

    BM25._search currently returns {question, results}, while Hybrid expects
    a list. Keep this compatibility at the integration boundary, not in
    Team 1's ranking implementation. Accept a future corrected list as well.
    """
    def __init__(self, retriever):
        self.retriever = retriever

    def _search(self, question, limit=100):
        found = self.retriever._search(question, limit)
        if isinstance(found, Mapping):
            if found.get("question") != question:
                raise ValueError("BM25 returned a different query")
            found = found.get("results")
        if not isinstance(found, list):
            raise ValueError("BM25 search must return a candidate list or envelope")
        return found
