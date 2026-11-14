"""Domain types cho LLM layer; contract hành vi lấy từ docs/team2/."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

STATUS_ANSWERED = "answered"
STATUS_INSUFFICIENT = "insufficient_context"
STATUSES = (STATUS_ANSWERED, STATUS_INSUFFICIENT)


@dataclass(frozen=True)
class HistoryTurn:
    role: str
    content: str


@dataclass(frozen=True)
class LLMParams:
    temperature: Optional[float] = 0.0
    max_output_tokens: Optional[int] = 1500


@dataclass(frozen=True)
class LLMInput:
    system_instruction: str
    legal_context: str
    user_question: str
    output_instruction: str
    history: Tuple[HistoryTurn, ...] = ()
    original_question: Optional[str] = None
    prompt_version: str = "prompt_v3"
    params: LLMParams = field(default_factory=LLMParams)

    @property
    def question(self) -> str:
        return self.user_question

    @property
    def context(self) -> str:
        return self.legal_context

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_instruction": self.system_instruction,
            "legal_context": self.legal_context,
            "user_question": self.user_question,
            "output_instruction": self.output_instruction,
            "history": [{"role": t.role, "content": t.content} for t in self.history],
            "original_question": self.original_question,
            "prompt_version": self.prompt_version,
        }


@dataclass(frozen=True)
class CitationCandidate:
    citation_id: str
    chunk_id: str
    document_id: str
    article_id: str
    document_title: str
    article: str
    clause: Optional[str]
    point: Optional[str]
    source_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "article_id": self.article_id,
            "document_title": self.document_title,
            "article": self.article,
            "clause": self.clause,
            "point": self.point,
            "source_url": self.source_url,
        }


@dataclass(frozen=True)
class Claim:
    """Một nhận định pháp lý trong answer, kèm nhãn citation hỗ trợ nó. Chỉ dùng nội bộ để thẩm định; không ra API."""
    claim_id: str
    text: str
    citation_ids: Tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"claim_id": self.claim_id, "text": self.text, "citation_ids": list(self.citation_ids)}


@dataclass(frozen=True)
class LLMOutput:
    status: str
    answer: str
    citations: Tuple[CitationCandidate, ...] = ()
    claims: Tuple[Claim, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = {
            "status": self.status,
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
        }
        if self.claims:
            data["claims"] = [c.to_dict() for c in self.claims]
        return data


@dataclass(frozen=True)
class Usage:
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


@dataclass(frozen=True)
class LLMResult:
    output: LLMOutput
    raw_text: str
    provider: str
    model: str
    usage: Usage
    latency_ms: int
    finish_reason: Optional[str]
    retries: int = 0
