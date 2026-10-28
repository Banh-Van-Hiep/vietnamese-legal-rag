"""Integration boundaries of the real pipeline: Retrieval -> Rerank -> Context -> LLM -> Citation check -> Validation.

All external parts are fakes (retriever echoing a Team 1-shaped payload, scorer, FakeLLMProvider). This proves the
wiring and error boundaries of `RAGPipeline`, NOT real Qdrant/BM25/BGE/LLM behaviour or retrieval quality.
"""
import unittest

from team2_rag.answer import NO_CONTEXT_ANSWER
from team2_rag.llm.errors import CitationInvalidError, LLMBadOutputError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.pipeline import RAGPipeline, validate_generated_response
from team2_rag.reranker import RerankModelError, rerank
from team2_rag.tests.helpers import citation
from team2_rag.tests.test_rerank_to_answer import META, reply_for, retrieval_output, scorer_for


class FakeRetriever:
    def __init__(self, build=None):
        self.calls = []
        self.build = build or (lambda q: {**retrieval_output(4), "question": q})

    def retrieve(self, question, top_k=20):
        self.calls.append((question, top_k))
        return self.build(question)


QUESTION = retrieval_output(1)["question"]
SCORES = [0.1, 0.9, 0.5, 0.2]          # reranked order of chunk_0..3 -> chunk_1, chunk_2, chunk_3, chunk_0


def pipeline(llm_replies, retriever=None, scorer=None, **kw):
    provider = FakeLLMProvider(llm_replies)
    retriever = retriever or FakeRetriever()
    return RAGPipeline(retriever, LLMService(provider), scorer=scorer or scorer_for(SCORES), **kw), provider, retriever


def reranked():
    return rerank(retrieval_output(4), scorer=scorer_for(SCORES))["results"]


class PipelineFlowTests(unittest.TestCase):
    def test_full_flow_cites_highest_reranked_chunk(self):
        p, llm, retriever = pipeline([reply_for(reranked(), 0)])
        out = p.query(QUESTION, [])
        self.assertEqual(out["status"], "answered")
        self.assertEqual([c["chunk_id"] for c in out["citations"]], ["chunk_1"])   # rank 2 originally, reranked first
        self.assertEqual(retriever.calls, [(QUESTION, 20)])
        self.assertEqual(len(llm.calls), 1)
        self.assertIn("Nội dung điều 1.", llm.calls[0][0].user)   # context really reached the LLM prompt

    def test_question_is_trimmed_before_retrieval(self):
        p, _, retriever = pipeline([reply_for(reranked(), 0)])
        p.query(f"  {QUESTION}  ", [])
        self.assertEqual(retriever.calls[0][0], QUESTION)

    def test_retriever_must_echo_the_actual_query(self):
        p, llm, _ = pipeline([], retriever=FakeRetriever(lambda q: retrieval_output(4)))  # echoes template question
        with self.assertRaises(ValueError):
            p.query("Một câu hỏi hoàn toàn khác về thuế?", [])
        self.assertEqual(llm.calls, [])

    def test_no_results_returns_insufficient_without_calling_llm(self):
        p, llm, _ = pipeline([], retriever=FakeRetriever(lambda q: {"question": q, "results": []}))
        out = p.query(QUESTION, [])
        self.assertEqual(out, {"status": "insufficient_context", "answer": NO_CONTEXT_ANSWER, "citations": []})
        self.assertEqual(llm.calls, [])

    def test_context_free_reference_question_does_not_retrieve(self):
        p, llm, retriever = pipeline([])
        out = p.query("Doanh nghiệp đó có phải đóng thuế không?", [])
        self.assertEqual((out["status"], out["citations"]), ("insufficient_context", []))
        self.assertEqual((retriever.calls, llm.calls), ([], []))

    def test_reranker_failure_is_not_masked_by_silent_fallback(self):
        def broken(pairs): raise RuntimeError("model down")
        p, llm, _ = pipeline([], scorer=broken)
        with self.assertRaises(RerankModelError):
            p.query(QUESTION, [])
        self.assertEqual(llm.calls, [])

    def test_reranker_graceful_degradation_when_not_strict(self):
        def broken(pairs): raise RuntimeError("GPU OOM or timeout")
        # When strict_rerank=False, falls back to original retrieval order without failing
        p, llm, retriever = pipeline([reply_for(retrieval_output(4)["results"], 0)], scorer=broken, strict_rerank=False)
        out = p.query(QUESTION, [])
        self.assertEqual(out["status"], "answered")
        self.assertEqual(out["citations"][0]["chunk_id"], "chunk_0")  # original retrieval top rank
        self.assertEqual(len(llm.calls), 1)

    def test_llm_citing_chunk_outside_supplied_context_is_rejected(self):
        bad = reply_for(reranked(), 0)
        bad["citations"][0]["chunk_id"] = "chunk_not_in_context"
        p, _, _ = pipeline([bad])
        with self.assertRaises(CitationInvalidError):
            p.query(QUESTION, [])

    def test_llm_citation_with_tampered_metadata_is_rejected(self):
        bad = reply_for(reranked(), 0)
        bad["citations"][0]["article"] = "Điều 999"
        p, _, _ = pipeline([bad])
        with self.assertRaises(CitationInvalidError):
            p.query(QUESTION, [])

    def test_malformed_llm_output_is_rejected(self):
        for raw in ("không phải JSON", "[]", '{"status": "answered"}'):
            with self.subTest(raw=raw):
                p, _, _ = pipeline([raw])
                with self.assertRaises(LLMBadOutputError):
                    p.query(QUESTION, [])

    def test_constructor_and_input_validation(self):
        for top_k in (0, 51, True, 2.5):
            with self.subTest(top_k=top_k), self.assertRaises(ValueError):
                RAGPipeline(FakeRetriever(), LLMService(FakeLLMProvider([])), top_k=top_k)
        p, _, retriever = pipeline([])
        for q, h in (("   ", []), ("x" * 2001, []), (QUESTION, [{"role": "user", "content": "a"}])):
            with self.subTest(q=q[:10], h=h), self.assertRaises(ValueError):
                p.query(q, h)
        self.assertEqual(retriever.calls, [])


class ValidateGeneratedResponseTests(unittest.TestCase):
    C1, C2 = citation("C1", "chunk-a"), citation("C2", "chunk-b")

    def ok(self, answer, *cits, status="answered"):
        return {"status": status, "answer": answer, "citations": list(cits)}

    def test_valid_responses_pass_unchanged(self):
        good = self.ok("A [C1] B [C2] A [C1].", self.C1, self.C2)
        self.assertEqual(validate_generated_response(good), good)
        none = self.ok("Chưa đủ căn cứ.", status="insufficient_context")
        self.assertEqual(validate_generated_response(none), none)

    def test_invalid_markers_and_citation_sets_are_rejected(self):
        cases = {
            "zero marker": self.ok("A [C0] [C1].", self.C1),
            "leading zero marker": self.ok("A [C01] [C1].", self.C1),
            "unclosed marker": self.ok("A [C1] [C2", self.C1),
            "out of order": self.ok("A [C2] [C1].", self.C1, self.C2),
            "citation without marker": self.ok("A [C1].", self.C1, self.C2),
            "marker without citation": self.ok("A [C1] [C2].", self.C1),
            "no marker at all": self.ok("A.", self.C1),
            "duplicate chunk": self.ok("A [C1] [C2].", self.C1, citation("C2", "chunk-a")),
            "answered without citations": self.ok("A [C1]."),
            "not an object": ["answered"],
        }
        for name, bad in cases.items():
            with self.subTest(name), self.assertRaises(LLMBadOutputError):
                validate_generated_response(bad)

    def test_response_model_runs_before_legacy_guard(self):
        class Rejecting:
            @staticmethod
            def model_validate(data): raise ValueError("model rejected")
        with self.assertRaises(ValueError):
            validate_generated_response(self.ok("A [C1].", self.C1), response_model=Rejecting)


if __name__ == "__main__":
    unittest.main()
