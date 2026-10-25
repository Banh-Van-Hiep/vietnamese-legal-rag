import pytest
from pydantic import ValidationError

from team2_rag.mock import make_mock_response
from team2_rag.models.response import Citation, RAGResponse

URL = "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"


def cit(cid="C1", **over):
    base = {
        "citation_id": cid,
        "chunk_id": "luat-59-2020-qh14-v1__dieu-1__k0__0",
        "document_id": "luat-59-2020-qh14-v1",
        "article_id": "dieu-1",
        "document_title": "Luật Doanh nghiệp",
        "article": "Điều 1",
        "clause": None,
        "point": None,
        "source_url": URL,
    }
    base.update(over)
    return base


def answered(answer="Nội dung [C1].", *cits):
    return {"status": "answered", "answer": answer, "citations": list(cits) or [cit()]}


def test_valid_answered_roundtrip_keeps_null_fields():
    payload = RAGResponse.model_validate(answered()).to_payload()
    assert set(payload) == {"status", "answer", "citations"}
    assert set(payload["citations"][0]) == {
        "citation_id", "chunk_id", "document_id", "article_id", "document_title",
        "article", "clause", "point", "source_url",
    }
    assert payload["citations"][0]["clause"] is None and payload["citations"][0]["point"] is None


def test_valid_insufficient():
    r = RAGResponse.model_validate({"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []})
    assert r.citations == [] and r.cited_chunk_ids() == []


@pytest.mark.parametrize("scenario", ["answered", "insufficient_context"])
def test_mock_responses_match_models(scenario):
    RAGResponse.model_validate(make_mock_response(scenario))


def test_multi_citation_order_and_chunk_ids():
    c2 = cit("C2", chunk_id="x__dieu-2__k1__0", article_id="dieu-2", article="Điều 2", clause="Khoản 1")
    r = RAGResponse.model_validate(answered("A [C1] B [C2] C [C1].", cit(), c2))
    assert r.cited_chunk_ids() == ["luat-59-2020-qh14-v1__dieu-1__k0__0", "x__dieu-2__k1__0"]


@pytest.mark.parametrize(
    "bad",
    [
        {**answered(), "extra": 1},
        {"status": "answered", "answer": "A [C1].", "citations": [{"ref": 1, "chunk_id": "x"}]},
        {"status": "unknown", "answer": "A", "citations": []},
        {"status": "answered", "answer": "Không có marker.", "citations": [cit()]},
        {"status": "answered", "answer": "A [C1].", "citations": []},
        {"status": "answered", "answer": "A [C2].", "citations": [cit()]},
        {"status": "answered", "answer": "A [C1] [C2].", "citations": [cit()]},
        {"status": "answered", "answer": "A [C2] [C1].", "citations": [cit("C1"), cit("C2", chunk_id="y")]},
        {"status": "answered", "answer": "A [C1].", "citations": [cit("C1"), cit("C1")]},
        {"status": "answered", "answer": "A [C2].", "citations": [cit("C2")]},
        {"status": "insufficient_context", "answer": "A.", "citations": [cit()]},
        {"status": "insufficient_context", "answer": "A [C1].", "citations": []},
        {"status": "answered", "answer": "  ", "citations": [cit()]},
    ],
)
def test_invalid_responses_rejected(bad):
    with pytest.raises(ValidationError):
        RAGResponse.model_validate(bad)


@pytest.mark.parametrize(
    "over",
    [
        {"citation_id": "1"},
        {"citation_id": "C0"},
        {"source_url": "http://vbpl.vn/x"},
        {"source_url": "/relative"},
        {"document_id": "tài-liệu"},
        {"article_id": "dieu 1"},
        {"clause": ""},
        {"point": "   "},
        {"article": ""},
        {"chunk_id": "x" * 201},
    ],
)
def test_invalid_citation_fields_rejected(over):
    with pytest.raises(ValidationError):
        Citation.model_validate(cit(**over))


@pytest.mark.parametrize("missing", ["clause", "point", "source_url", "chunk_id", "article_id"])
def test_missing_citation_field_rejected(missing):
    data = cit()
    data.pop(missing)
    with pytest.raises(ValidationError):
        Citation.model_validate(data)
