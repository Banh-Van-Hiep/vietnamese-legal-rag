"""Parse/validate LLM output theo contract v1.2 trong docs/team2/."""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from team2_rag.llm.errors import LLMBadOutputError
from team2_rag.llm.types import CitationCandidate, Claim, LLMOutput, STATUS_ANSWERED, STATUS_INSUFFICIENT

_CORE_KEYS = {"status", "answer", "citations"}
_CLAIM_KEYS = {"claim_id", "text", "citation_ids"}
_CLAIM_RE = re.compile(r"^K[1-9][0-9]*$")
MAX_CLAIMS = 30
MAX_CLAIM_CHARS = 2000
_CITATION_RE = re.compile(r"^C[1-9][0-9]*$")
_MARKER_RE = re.compile(r"\[C([1-9][0-9]*)\]")
_REQUIRED_CITATION_FIELDS = {
    "citation_id", "chunk_id", "document_id", "article_id", "document_title",
    "article", "clause", "point", "source_url",
}


def _bad(msg: str, provider: str, text: str) -> LLMBadOutputError:
    return LLMBadOutputError(msg, provider=provider, raw_text=text)


def _str_field(obj: dict, name: str, provider: str, text: str, *, max_len: int) -> str:
    value = obj.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise _bad(f"citation.{name} không hợp lệ.", provider, text)
    return value


def _parse_claims(raw: Any, citation_ids: set, status: str, provider: str, text: str) -> tuple[Claim, ...]:
    """`claims` là tùy chọn; khi có thì mỗi claim phải trỏ về citation đã khai báo và id không trùng."""
    if not isinstance(raw, list) or len(raw) > MAX_CLAIMS:
        raise _bad("claims không hợp lệ.", provider, text)
    if status == STATUS_INSUFFICIENT and raw:
        raise _bad("insufficient_context phải có claims=[].", provider, text)
    claims, seen = [], set()
    for c in raw:
        if not isinstance(c, dict) or set(c) != _CLAIM_KEYS:
            raise _bad("claim có field sai hoặc thiếu.", provider, text)
        claim_id, claim_text, refs = c["claim_id"], c["text"], c["citation_ids"]
        if not isinstance(claim_id, str) or not _CLAIM_RE.fullmatch(claim_id) or claim_id in seen:
            raise _bad("claim_id không hợp lệ hoặc bị trùng.", provider, text)
        if not isinstance(claim_text, str) or not claim_text.strip() or len(claim_text) > MAX_CLAIM_CHARS:
            raise _bad("claim.text không hợp lệ.", provider, text)
        if (not isinstance(refs, list) or not refs or len(set(refs)) != len(refs)
                or any(not isinstance(r, str) or r not in citation_ids for r in refs)):
            raise _bad("claim.citation_ids phải là danh sách nhãn có trong citations, không trùng.", provider, text)
        seen.add(claim_id)
        claims.append(Claim(claim_id, claim_text, tuple(refs)))
    return tuple(claims)


def parse_llm_output(text: str, *, provider: str = "") -> LLMOutput:
    try:
        data = json.loads(text.strip())
    except (TypeError, ValueError):
        raise _bad("Output của LLM không phải JSON hợp lệ.", provider, text) from None
    if not isinstance(data, dict) or not _CORE_KEYS <= set(data) <= _CORE_KEYS | {"claims"}:
        raise _bad("Output phải có status, answer, citations (và có thể có claims), không thêm field khác.", provider, text)
    status, answer, citations = data["status"], data["answer"], data["citations"]
    if status not in (STATUS_ANSWERED, STATUS_INSUFFICIENT):
        raise _bad("status không hợp lệ.", provider, text)
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 12000:
        raise _bad("answer không hợp lệ.", provider, text)
    if not isinstance(citations, list) or len(citations) > 10:
        raise _bad("citations không hợp lệ.", provider, text)
    if status == STATUS_INSUFFICIENT and (citations or _MARKER_RE.search(answer)):
        raise _bad("insufficient_context phải có citations=[] và không có marker.", provider, text)
    if status == STATUS_ANSWERED and not citations:
        raise _bad("answered phải có ít nhất một citation.", provider, text)

    parsed = []
    ids = set()
    for c in citations:
        if not isinstance(c, dict) or set(c) != _REQUIRED_CITATION_FIELDS:
            raise _bad("citation có field sai hoặc thiếu.", provider, text)
        cid = _str_field(c, "citation_id", provider, text, max_len=20)
        if not _CITATION_RE.fullmatch(cid) or cid in ids:
            raise _bad("citation_id không liên tục hoặc bị trùng.", provider, text)
        ids.add(cid)
        chunk_id = _str_field(c, "chunk_id", provider, text, max_len=200)
        document_id = _str_field(c, "document_id", provider, text, max_len=200)
        article_id = _str_field(c, "article_id", provider, text, max_len=100)
        document_title = _str_field(c, "document_title", provider, text, max_len=500)
        article = _str_field(c, "article", provider, text, max_len=100)
        clause = c["clause"]
        point = c["point"]
        for name, value in (("clause", clause), ("point", point)):
            if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 100):
                raise _bad(f"citation.{name} không hợp lệ.", provider, text)
        url = _str_field(c, "source_url", provider, text, max_len=2048)
        parsed_url = urlparse(url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise _bad("citation.source_url phải là HTTPS tuyệt đối.", provider, text)
        parsed.append(CitationCandidate(cid, chunk_id, document_id, article_id, document_title, article, clause, point, url))

    marker_ids = [f"C{x}" for x in _MARKER_RE.findall(answer)]
    if status == STATUS_ANSWERED and not marker_ids:
        raise _bad("answered phải có marker [Ck].", provider, text)
    if any(mid not in ids for mid in marker_ids):
        raise _bad("answer dùng citation_id không có trong citations.", provider, text)
    claims = _parse_claims(data["claims"], ids, status, provider, text) if "claims" in data else ()
    return LLMOutput(status=status, answer=answer, citations=tuple(parsed), claims=claims)


def provider_output_schema() -> dict:
    """Provider chỉ yêu cầu JSON object; contract được validate sau khi nhận output."""
