"""Parse/validate LLM output theo contract v1.2 trong docs/team2/."""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from team2_rag.llm.errors import LLMBadOutputError
from team2_rag.llm.types import CitationCandidate, LLMOutput, STATUS_ANSWERED, STATUS_INSUFFICIENT

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


def parse_llm_output(text: str, *, provider: str = "") -> LLMOutput:
    try:
        data = json.loads(text.strip())
    except (TypeError, ValueError):
        raise _bad("Output của LLM không phải JSON hợp lệ.", provider, text) from None
    if not isinstance(data, dict) or set(data) != {"status", "answer", "citations"}:
        raise _bad("Output phải chỉ có status, answer, citations.", provider, text)
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
    return LLMOutput(status=status, answer=answer, citations=tuple(parsed))


def provider_output_schema() -> dict:
    """Provider chỉ yêu cầu JSON object; contract được validate sau khi nhận output."""
