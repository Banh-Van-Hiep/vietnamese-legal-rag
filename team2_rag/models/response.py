from __future__ import annotations

import re
from typing import Any, Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Status = Literal["answered", "insufficient_context"]

_ID = r"^[A-Za-z0-9_-]+$"
_MARKER = re.compile(r"\[C([1-9][0-9]*)\]")


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    citation_id: str = Field(pattern=r"^C[1-9][0-9]*$", max_length=20)
    chunk_id: str = Field(min_length=1, max_length=200)
    document_id: str = Field(min_length=1, max_length=200, pattern=_ID)
    article_id: str = Field(min_length=1, max_length=100, pattern=_ID)
    document_title: str = Field(min_length=1, max_length=500)
    article: str = Field(min_length=1, max_length=100)
    clause: Optional[str] = Field(max_length=100)
    point: Optional[str] = Field(max_length=100)
    source_url: str = Field(min_length=1, max_length=2048)

    @field_validator("chunk_id", "document_title", "article", "clause", "point")
    @classmethod
    def _not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("không được rỗng")
        return v

    @field_validator("source_url")
    @classmethod
    def _https(cls, v: str) -> str:
        p = urlparse(v)
        if p.scheme != "https" or not p.netloc:
            raise ValueError("source_url phải là URL HTTPS tuyệt đối")
        return v


class RAGResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Status
    answer: str = Field(min_length=1, max_length=12000)
    citations: list[Citation] = Field(max_length=10)

    @field_validator("answer")
    @classmethod
    def _answer_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("answer không được rỗng")
        return v

    @model_validator(mode="after")
    def _check_citations(self) -> "RAGResponse":
        markers: list[str] = []
        for m in _MARKER.finditer(self.answer):
            label = f"C{m.group(1)}"
            if label not in markers:
                markers.append(label)
        ids = [c.citation_id for c in self.citations]
        if len(set(ids)) != len(ids):
            raise ValueError("citation_id bị trùng")
        if self.status == "insufficient_context":
            if ids or markers:
                raise ValueError("insufficient_context phải có citations=[] và không có marker")
            return self
        if not ids:
            raise ValueError("answered phải có ít nhất một citation")
        if markers != ids:
            raise ValueError("citations phải khớp marker [Ck] theo thứ tự xuất hiện đầu tiên")
        if ids != [f"C{i}" for i in range(1, len(ids) + 1)]:
            raise ValueError("citation_id phải liên tục C1..Cn")
        return self

    def cited_chunk_ids(self) -> list[str]:
        return [c.chunk_id for c in self.citations]

    def to_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
