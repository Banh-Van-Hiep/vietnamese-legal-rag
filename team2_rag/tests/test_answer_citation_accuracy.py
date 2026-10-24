import json
from pathlib import Path

import pytest

from team2_rag.answer import NO_CONTEXT_ANSWER, answer_from_rerank, cited_chunk_ids
from team2_rag.llm.errors import CitationInvalidError, LLMBadOutputError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.models.response import RAGResponse

GOLDEN = Path(__file__).resolve().parents[1] / "data" / "golden" / "golden_sample_5qa.json"
ITEMS = json.loads(GOLDEN.read_text(encoding="utf-8"))
REQUIRED = {
    "id", "question", "expected_status", "ground_truth", "gold_chunk_ids",
    "citation", "category", "author", "gold_citations",
}
URL = "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"
DISTRACTOR = {
    "chunk_id": "luat-59-2020-qh14-v1__dieu-9__k1__0", "document_id": "luat-59-2020-qh14-v1",
    "article_id": "dieu-9", "content": "Nội dung không liên quan.", "document_title": "Luật Doanh nghiệp",
    "article": "Điều 9", "clause": "Khoản 1", "point": None, "source_url": URL,
    "score": 0.001, "rank": 99, "retrieval_method": "hybrid_rrf",
}


def rerank_output(item):
    results = []
    for i, c in enumerate(item["gold_citations"], 1):
        row = {k: v for k, v in c.items() if k != "citation_id"}
        row.update(content=item["ground_truth"], score=1.0 / (i + 1), rank=i, retrieval_method="hybrid_rrf")
        results.append(row)
    if results:
        results.append({**DISTRACTOR, "rank": len(results) + 1})
    return {"question": item["question"], "results": results}


def llm_for(item):
    cits = item["gold_citations"]
    answer = item["ground_truth"] + " " + "".join(f"[{c['citation_id']}]" for c in cits)
    provider = FakeLLMProvider(
        [{"status": "answered", "answer": answer, "citations": cits}] if cits else []
    )
    return provider, LLMService(provider)


def by_id(i):
    return next(x for x in ITEMS if x["id"] == i)


def test_golden_dataset_shape():
    assert len(ITEMS) == 5
    assert len({x["id"] for x in ITEMS}) == 5
    for x in ITEMS:
        assert REQUIRED <= set(x)
        assert [c["chunk_id"] for c in x["gold_citations"]] == x["gold_chunk_ids"]
        assert (x["expected_status"] == "answered") == bool(x["gold_chunk_ids"])
        assert [c["citation_id"] for c in x["gold_citations"]] == [
            f"C{i}" for i in range(1, len(x["gold_citations"]) + 1)
        ]


@pytest.mark.parametrize("item", ITEMS, ids=[x["id"] for x in ITEMS])
def test_answer_and_citations_match_ground_truth(item):
    provider, svc = llm_for(item)
    resp = answer_from_rerank(rerank_output(item), svc)
    model = RAGResponse.model_validate(resp)
    assert model.status == item["expected_status"]
    assert cited_chunk_ids(resp) == item["gold_chunk_ids"]
    assert resp["citations"] == item["gold_citations"]
    if item["expected_status"] == "answered":
        assert item["ground_truth"] in resp["answer"]
        assert DISTRACTOR["chunk_id"] not in cited_chunk_ids(resp)
    else:
        assert resp["answer"] == NO_CONTEXT_ANSWER
        assert provider.calls == []


def test_citation_metadata_tampering_rejected():
    item = by_id("gold_003")
    cits = [{**item["gold_citations"][0], "document_title": "Luật Khác"}]
    out = {"status": "answered", "answer": "Nội dung [C1].", "citations": cits}
    with pytest.raises(CitationInvalidError):
        answer_from_rerank(rerank_output(item), LLMService(FakeLLMProvider([out])))


def test_citation_to_chunk_not_in_context_rejected():
    item = by_id("gold_003")
    cits = [{**item["gold_citations"][0], "chunk_id": "luat-59-2020-qh14-v1__dieu-99__k1__0"}]
    out = {"status": "answered", "answer": "Nội dung [C1].", "citations": cits}
    with pytest.raises(CitationInvalidError):
        answer_from_rerank(rerank_output(item), LLMService(FakeLLMProvider([out])))


def test_answer_without_marker_rejected():
    item = by_id("gold_003")
    out = {"status": "answered", "answer": "Không có marker.", "citations": item["gold_citations"]}
    with pytest.raises(LLMBadOutputError):
        answer_from_rerank(rerank_output(item), LLMService(FakeLLMProvider([out])))
