"""Reranked candidates -> Context Builder -> Prompt -> LLMService -> verified RAGResponse.

Kết quả đúng contracts/v0.1/rag_response.schema.json (`status`, `answer`, `citations`), không thêm field.
`chunk_id` nguồn nằm trong từng citation; dùng `cited_chunk_ids()` để lấy danh sách.
"""
from __future__ import annotations

import logging
import re
from typing import Iterable, Mapping, Optional, Union

from team2_rag.config.settings import DEFAULT_MAX_CONTEXT_CHARS, DEFAULT_MAX_CONTEXT_CHUNKS
from team2_rag.llm.errors import CitationInvalidError
from team2_rag.llm.service import LLMService
from team2_rag.llm.tokens import TokenBudget
from team2_rag.llm.types import STATUS_ANSWERED, STATUS_INSUFFICIENT, HistoryTurn
from team2_rag.prompts.builder import PromptBuilder
from team2_rag.prompts.context import ContextBudgetError, ContextBuildError, build_context
from team2_rag.prompts.render import render_prompt
from team2_rag.types import RAGResponse

logger = logging.getLogger("team2_rag.answer")
logger.addHandler(logging.NullHandler())

NO_CONTEXT_ANSWER = "Tài liệu được truy xuất chưa đủ căn cứ để trả lời."
MAX_QUESTION_CHARS = 4000  # câu hỏi gửi retrieval (docs/team1_data/retrieval-design.md)
_MARKER = re.compile(r"\[C([1-9][0-9]*)\]")


def cited_chunk_ids(response: Mapping) -> list[str]:
    """chunk_id của các nguồn được trích dẫn, theo thứ tự citation."""
    return [c["chunk_id"] for c in response.get("citations", [])]


def _insufficient(answer: str = NO_CONTEXT_ANSWER) -> RAGResponse:
    return {"status": STATUS_INSUFFICIENT, "answer": answer, "citations": []}


def answer_from_rerank(
    rerank_output: Mapping,
    llm_service: LLMService,
    history: Optional[Iterable[Union[HistoryTurn, Mapping]]] = None,
    *,
    max_chunks: int = DEFAULT_MAX_CONTEXT_CHUNKS,
    max_context_chars: Optional[int] = DEFAULT_MAX_CONTEXT_CHARS,
    token_budget: Optional[TokenBudget] = None,
    request_id: Optional[str] = None,
) -> RAGResponse:
    """Sinh câu trả lời từ output của Reranker (candidate 12 trường của Team 1, đã xếp theo rerank).

    Lỗi: input sai contract -> ValueError/ContextBuildError; lỗi gọi LLM -> LLMError hiện có;
    JSON/form sai -> LLMBadOutputError (INVALID_LLM_OUTPUT); provenance sai -> CitationInvalidError
    (CITATION_INVALID). Không có chunk dùng được -> insufficient_context mà không gọi LLM.

    Budget: truyền `token_budget` để đếm bằng tokenizer của LLM (đúng spec context-builder.md). Không truyền thì
    dùng `max_context_chars` (xấp xỉ, KHÔNG đáp ứng spec token; chỉ dùng cho dev/test). Prompt cố định
    (system/question/history) chiếm hết budget -> ContextBudgetError, không gửi prompt vượt giới hạn.
    """
    if not isinstance(rerank_output, Mapping):
        raise ValueError("rerank_output phải là object có question và results")
    question = rerank_output.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    if len(question.strip()) > MAX_QUESTION_CHARS:
        raise ValueError(f"question must not exceed {MAX_QUESTION_CHARS} characters after trimming")
    if "results" not in rerank_output:
        raise ValueError("rerank_output thiếu results")

    if token_budget is None:
        logger.warning("answer_from_rerank chạy với budget ký tự xấp xỉ, chưa đáp ứng spec token (context-builder.md).")
        context = build_context(rerank_output["results"], max_chunks=max_chunks, max_chars=max_context_chars)
    else:
        # Token cố định = system + user (tag, history, question, output_instruction) với context giữ chỗ "-" (dư ≤ vài token).
        fixed = render_prompt(PromptBuilder().build(question, "-", history))
        fixed_tokens = token_budget.counter.count(fixed.system) + token_budget.counter.count(fixed.user)
        available = token_budget.available_for_context(fixed_tokens)
        if available < 1:
            raise ContextBudgetError(
                f"Prompt cố định {fixed_tokens} token vượt giới hạn {token_budget.prompt_limit}; không còn chỗ cho nguồn.")
        context = build_context(rerank_output["results"], max_chunks=max_chunks,
                                token_counter=token_budget.counter, max_tokens=available)
        if not context.is_empty:  # chốt chặn: đếm lại toàn bộ prompt thật, vì token không cộng tính tuyệt đối
            full = render_prompt(PromptBuilder().build(question, context.text, history))
            total = token_budget.counter.count(full.system) + token_budget.counter.count(full.user)
            if total > token_budget.prompt_limit:
                raise ContextBudgetError(f"Prompt {total} token vượt giới hạn {token_budget.prompt_limit}.")
    if context.is_empty:
        return _insufficient()

    result = llm_service.ask(question, context.text, history, request_id=request_id)
    out = result.output
    if out.status != STATUS_ANSWERED:
        return _insufficient(out.answer)

    by_label = context.by_label()
    for cand in out.citations:
        src = by_label.get(cand.citation_id)
        got = cand.to_dict()
        got.pop("citation_id")
        if src is None or got != src.source_metadata():
            raise CitationInvalidError(
                f"{cand.citation_id}: nhãn lạ hoặc metadata không khớp chunk đã gửi cho LLM.", provider=result.provider)

    # Mỗi citation phải có marker và ngược lại; đánh lại C1..Cn theo lần xuất hiện đầu tiên trong answer.
    order: list[str] = []
    for m in _MARKER.finditer(out.answer):
        label = f"C{m.group(1)}"
        if label not in order:
            order.append(label)
    if set(order) != {c.citation_id for c in out.citations}:
        raise CitationInvalidError("citation thừa hoặc marker không có citation.", provider=result.provider)
    new_id = {old: f"C{i}" for i, old in enumerate(order, 1)}
    answer = _MARKER.sub(lambda m: f"[{new_id['C' + m.group(1)]}]", out.answer)  # một lượt, không va chạm nhãn
    citations = []
    for old in order:
        meta = by_label[old].source_metadata()
        citations.append({"citation_id": new_id[old], **meta})
    return {"status": STATUS_ANSWERED, "answer": answer, "citations": citations}


__all__ = ["ContextBudgetError", "ContextBuildError", "NO_CONTEXT_ANSWER", "answer_from_rerank", "cited_chunk_ids"]
