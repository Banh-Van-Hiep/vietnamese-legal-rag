"""VLRA-38 composition regressions; fake scoring/provider, real pipeline code."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.pipeline import BM25SearchAdapter, RAGPipeline
from team2_rag.reranker import RerankInputError, RerankModelError

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / "team2_rag/data/samples/reranker_input.json").read_text())
META = ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")


def reply(row):
    return {"status": "answered", "answer": "Phản hồi kiểm thử [C1].",
            "citations": [{"citation_id": "C1", **{k: row[k] for k in META}}]}


class PipelineTests(unittest.TestCase):
    def make(self, payload=None, response=None):
        self.payload = copy.deepcopy(SAMPLE if payload is None else payload)
        self.retriever = Mock()
        self.retriever.retrieve.return_value = self.payload
        provider = FakeLLMProvider([response or reply(self.payload["results"][1])])
        self.provider = provider
        self.scorer = Mock(return_value=[1, 3, 2])
        return RAGPipeline(self.retriever, LLMService(provider), scorer=self.scorer)

    def test_query_reaches_retrieval_reranker_context_llm_and_preserves_sources(self):
        pipeline = self.make()
        before = copy.deepcopy(self.payload)
        result = pipeline.query(SAMPLE["question"], [], request_id="test-trace")
        self.retriever.retrieve.assert_called_once_with(SAMPLE["question"], top_k=20)
        self.assertEqual(self.payload, before)
        self.assertEqual(result["citations"][0]["chunk_id"], before["results"][1]["chunk_id"])
        prompt = self.provider.calls[0][0].user
        ordered = [prompt.index("chunk_id=" + before["results"][i]["chunk_id"]) for i in [1, 2, 0]]
        self.assertEqual(ordered, sorted(ordered))

    def test_empty_results_never_run_scoring_or_llm(self):
        pipeline = self.make({"question": SAMPLE["question"], "results": []}, response={"unused": True})
        self.assertEqual(pipeline.query(SAMPLE["question"])["status"], "insufficient_context")
        self.scorer.assert_not_called()
        self.assertEqual(self.provider.calls, [])

    def test_scoring_failure_is_not_silently_returned_as_success(self):
        pipeline = self.make()
        self.scorer.side_effect = RuntimeError("model unavailable")
        with self.assertRaises(RerankModelError):
            pipeline.query(SAMPLE["question"])
        self.assertEqual(self.provider.calls, [])

    def test_retrieval_failure_never_becomes_insufficient_context(self):
        from team1_data.retrieval.errors import RetrievalUnavailableError
        pipeline = self.make()
        self.retriever.retrieve.side_effect = RetrievalUnavailableError("index missing")
        with self.assertRaises(RetrievalUnavailableError):
            pipeline.query(SAMPLE["question"])
        self.scorer.assert_not_called()

    def test_mismatched_query_or_invalid_candidate_stops_generation(self):
        for change in ("query", "candidate"):
            pipeline = self.make()
            if change == "query":
                self.payload["question"] = "another query"
            else:
                del self.payload["results"][0]["source_url"]
            with self.assertRaises((ValueError, RerankInputError)):
                pipeline.query(SAMPLE["question"])
            self.assertEqual(self.provider.calls, [])

    def test_history_is_sent_as_history_not_used_as_legal_source(self):
        pipeline = self.make()
        turns = [{"role": "user", "content": "Câu hỏi cũ"},
                 {"role": "assistant", "content": "Trả lời cũ [C9]"}]
        pipeline.query(SAMPLE["question"], turns)
        prompt = self.provider.calls[0][0].user
        legal = prompt.split("<LEGAL_CONTEXT>")[1].split("</LEGAL_CONTEXT>")[0]
        self.assertIn("Câu hỏi cũ", prompt)
        self.assertNotIn("Trả lời cũ", legal)

    def test_ambiguous_reference_asks_for_clarification_without_provider(self):
        pipeline = self.make()
        self.assertEqual(pipeline.query("Trường hợp vừa nêu thì sao?")["status"], "insufficient_context")
        self.retriever.retrieve.assert_not_called()
        self.assertEqual(self.provider.calls, [])

    def test_http_input_limits_are_also_checked_for_direct_calls(self):
        pipeline = self.make()
        bad = [None, "", " " * 4, 12, "a" * 2001]
        for q in bad:
            with self.subTest(q=str(q)[:10]), self.assertRaises(ValueError):
                pipeline.query(q)
        for h in ({}, [{"role": "user", "content": "x"}],
                  [{"role": "assistant", "content": "x"}, {"role": "user", "content": "y"}],
                  [{"role": "user", "content": "x" * 20000}, {"role": "assistant", "content": "x"}]):
            with self.assertRaises(ValueError):
                pipeline.query(SAMPLE["question"], h)


class BM25CompatibilityTests(unittest.TestCase):
    def test_bm25_envelope_is_unwrapped_and_future_list_is_accepted(self):
        rows = SAMPLE["results"]
        for result in (rows, {"question": SAMPLE["question"], "results": rows}):
            branch = Mock()
            branch._search.return_value = result
            self.assertEqual(BM25SearchAdapter(branch)._search(SAMPLE["question"]), rows)

    def test_bad_envelope_does_not_get_fused(self):
        branch = Mock()
        branch._search.return_value = {"question": "wrong", "results": []}
        with self.assertRaises(ValueError):
            BM25SearchAdapter(branch)._search(SAMPLE["question"])


if __name__ == "__main__":
    unittest.main()
