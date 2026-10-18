"""VLRA-29 kiểm thử Reranker -> Context -> LLM -> Answer + chunk_id.

Chạy offline: scorer giả cho `rerank` (không tải mô hình BGE), FakeLLMProvider cho LLM (không cần API key).
Không kiểm chứng: chất lượng xếp hạng của mô hình BGE thật, BM25/Dense thật, LLM thật, tokenizer thật.
"""
import copy
import json
import unittest

from team2_rag.answer import generate_answer, to_error_response
from team2_rag.llm.errors import CitationInvalidError, LLMBadOutputError, LLMTimeoutError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.reranker import RerankInputError, RerankModelError, rerank, rerank_with_details
from team2_rag.answer import NO_CONTEXT_ANSWER
from team2_rag.tests.helpers import REPO_ROOT

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

TEMPLATE = json.loads((REPO_ROOT / "team2_rag" / "data" / "samples" / "reranker_input.json").read_text(encoding="utf-8"))
CONTRACTS = REPO_ROOT / "contracts" / "v0.1"
META = ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")


def retrieval_output(n=4):
    """n candidate hợp lệ theo contract Team 1; rank/score gốc của retrieval giảm dần, chunk_id khác nhau."""
    rows = []
    for i in range(n):
        row = copy.deepcopy(TEMPLATE["results"][i % len(TEMPLATE["results"])])
        row.update(chunk_id=f"chunk_{i}", article_id=f"dieu-{i}", content=f"Nội dung điều {i}.", rank=i + 1, score=10.0 - i)
        rows.append(row)
    return {"question": TEMPLATE["question"], "results": rows}


def scorer_for(scores):
    return lambda pairs: list(scores)


def reply_for(results, *positions):
    """Phản hồi LLM trích dẫn đúng chunk ở vị trí `positions` (0-based) trong danh sách ĐÃ rerank."""
    cits = [{"citation_id": f"C{p + 1}"} | {k: results[p][k] for k in META} for p in positions]
    answer = " ".join(f"Ý {c['citation_id']} [{c['citation_id']}]." for c in cits)
    return {"status": "answered", "answer": answer, "citations": cits}


class RerankOrderTests(unittest.TestCase):
    def test_results_sorted_by_model_score_and_original_rank_kept(self):
        out = rerank(retrieval_output(), scorer=scorer_for([1, 9, 5, 3]))
        self.assertEqual([r["chunk_id"] for r in out["results"]], ["chunk_1", "chunk_2", "chunk_3", "chunk_0"])
        # `rank` vẫn là rank retrieval gốc, KHÔNG được đánh lại theo thứ tự rerank.
        self.assertEqual([r["rank"] for r in out["results"]], [2, 3, 4, 1])

    def test_rerank_output_still_matches_retrieval_contract(self):
        if jsonschema is None:
            self.skipTest("jsonschema chưa cài")
        out = rerank(retrieval_output(), scorer=scorer_for([1, 9, 5, 3]))
        schema = json.loads((CONTRACTS / "retrieval_output.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(out, schema)

    def test_context_labels_follow_rerank_order_not_original_rank(self):
        reranked = rerank(retrieval_output(), scorer=scorer_for([1, 9, 5, 3]))
        p = FakeLLMProvider([reply_for(reranked["results"], 0)])
        generate_answer(reranked, llm_service=LLMService(p))
        user = p.calls[0][0].user
        pos = [user.index(f"chunk_id={cid}") for cid in ("chunk_1", "chunk_2", "chunk_3", "chunk_0")]
        self.assertEqual(pos, sorted(pos))  # đúng thứ tự rerank trong prompt
        self.assertLess(user.index("[C1] chunk_id=chunk_1"), user.index("[C2] chunk_id=chunk_2"))
        self.assertIn("[C4] chunk_id=chunk_0", user)  # chunk rank 1 ban đầu nay đứng cuối


class RerankToAnswerTests(unittest.TestCase):
    def setUp(self):
        self.reranked = rerank(retrieval_output(), scorer=scorer_for([1, 9, 5, 3]))
        self.rows = self.reranked["results"]  # chunk_1, chunk_2, chunk_3, chunk_0

    def run_answer(self, *replies, **kw):
        p = FakeLLMProvider(list(replies))
        return generate_answer(self.reranked, llm_service=LLMService(p), **kw), p

    def test_answer_and_chunk_ids_from_reranked_top(self):
        r, _ = self.run_answer(reply_for(self.rows, 0, 1))
        self.assertEqual(r["status"], "answered")
        self.assertEqual([c["chunk_id"] for c in r["citations"]], ["chunk_1", "chunk_2"])
        self.assertEqual([c["citation_id"] for c in r["citations"]], ["C1", "C2"])
        self.assertEqual(set(r), {"status", "answer", "citations"})
        if jsonschema:
            schema = json.loads((CONTRACTS / "rag_response.schema.json").read_text(encoding="utf-8"))
            jsonschema.validate(r, schema)

    def test_citation_keeps_reranked_chunk_even_if_it_was_not_rank_1(self):
        r, _ = self.run_answer(reply_for(self.rows, 3))  # chunk_0 (rank 1 gốc) đứng cuối sau rerank
        self.assertEqual(r["citations"][0]["chunk_id"], "chunk_0")
        self.assertEqual(r["citations"][0]["citation_id"], "C1")  # đánh số lại theo thứ tự xuất hiện trong câu trả lời

    def test_llm_using_pre_rerank_order_is_rejected(self):
        """LLM/caller dùng metadata theo thứ tự retrieval cũ cho nhãn C1 -> phải CITATION_INVALID, không sửa ngầm."""
        original = retrieval_output()["results"]
        with self.assertRaises(CitationInvalidError) as ctx:
            self.run_answer(reply_for(original, 0))  # C1 + metadata chunk_0, nhưng C1 trong context là chunk_1
        self.assertEqual(to_error_response(ctx.exception)["error"]["code"], "CITATION_INVALID")

    def test_chunk_beyond_max_chunks_cannot_be_cited(self):
        big = rerank(retrieval_output(8), scorer=scorer_for([1, 2, 3, 4, 5, 6, 7, 8]))  # đảo ngược: chunk_7 đầu
        rows = big["results"]
        p = FakeLLMProvider([reply_for(rows, 5)])  # vị trí thứ 6 (C6) không được đưa vào LLM
        with self.assertRaises(CitationInvalidError):
            generate_answer(big, llm_service=LLMService(p))
        user = p.calls[0][0].user
        self.assertIn(f"chunk_id={rows[4]['chunk_id']}", user)
        self.assertNotIn(f"chunk_id={rows[5]['chunk_id']}", user)

    def test_empty_retrieval_gives_insufficient_context_without_calling_llm(self):
        empty = rerank({"question": TEMPLATE["question"], "results": []}, scorer=scorer_for([]))
        self.assertEqual(empty["results"], [])
        p = FakeLLMProvider([])
        r = generate_answer(empty, llm_service=LLMService(p))
        self.assertEqual(r, {"status": "insufficient_context", "answer": NO_CONTEXT_ANSWER, "citations": []})
        self.assertEqual(p.calls, [])

    def test_llm_errors_after_rerank_map_to_error_response(self):
        with self.assertRaises(LLMTimeoutError) as ctx:
            self.run_answer(LLMTimeoutError("timeout"))
        self.assertEqual(to_error_response(ctx.exception), {"error": {"code": "LLM_TIMEOUT", "message": to_error_response(ctx.exception)["error"]["message"], "retryable": True}})
        with self.assertRaises(LLMBadOutputError) as ctx:
            self.run_answer("không phải JSON")
        err = to_error_response(ctx.exception)["error"]
        self.assertEqual((err["code"], err["retryable"]), ("INVALID_LLM_OUTPUT", False))


class RerankFailureTests(unittest.TestCase):
    def test_model_failure_falls_back_to_original_order_and_answer_still_works(self):
        def broken(pairs):
            raise RuntimeError("model down")
        details = rerank_with_details(retrieval_output(), scorer=broken)
        self.assertEqual(details.fallback_reason, "RuntimeError")
        self.assertEqual([r["chunk_id"] for r in details.output["results"]], ["chunk_0", "chunk_1", "chunk_2", "chunk_3"])
        p = FakeLLMProvider([reply_for(details.output["results"], 0)])
        r = generate_answer(details.output, llm_service=LLMService(p))
        self.assertEqual(r["citations"][0]["chunk_id"], "chunk_0")

    def test_strict_mode_raises_instead_of_silent_fallback(self):
        with self.assertRaises(RerankModelError):
            rerank(retrieval_output(), scorer=lambda pairs: [1.0], strict=True)  # sai số lượng điểm

    def test_invalid_retrieval_output_is_not_hidden_by_fallback(self):
        bad = retrieval_output()
        del bad["results"][0]["source_url"]
        with self.assertRaises(RerankInputError):
            rerank(bad, scorer=scorer_for([1, 2, 3, 4]))

    def test_non_https_source_url_rejected_before_llm(self):
        bad = retrieval_output()
        bad["results"][0]["source_url"] = "http://example.com/x"
        with self.assertRaises(RerankInputError):
            rerank(bad, scorer=scorer_for([1, 2, 3, 4]))


if __name__ == "__main__":
    unittest.main()
