"""VLRA-66/67: schema claims, prompt v3, rerank timeout/tắt rerank, Verification và API; fake scorer/provider."""
import copy
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from team2_rag.api import create_app
from team2_rag.llm.errors import CitationInvalidError, LLMBadOutputError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.output_parser import parse_llm_output
from team2_rag.llm.service import LLMService
from team2_rag.pipeline import RAGPipeline
from team2_rag.prompts import (CLAIMS_INSTRUCTION, OUTPUT_INSTRUCTION, OUTPUT_INSTRUCTION_WITH_CLAIMS,
                               PromptBuilder, SYSTEM_INSTRUCTION)
from team2_rag.reranker import RerankModelError
from team2_rag.tests.helpers import CONTEXT, QUESTION, citation, good_output
from team2_rag.verification import ClaimCheck, VerificationResult, verify_response

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / "team2_rag/data/samples/reranker_input.json").read_text(encoding="utf-8"))
META = ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")


def claims_output(rows, row=2, claim=None):
    """LLM trích dẫn nhãn C2 (chunk thứ hai trong context, tức `rows[row]`) và khai một claim trỏ về nó."""
    return {"status": "answered", "answer": "Phản hồi kiểm thử [C2].",
            "citations": [{"citation_id": "C2", **{k: rows[row][k] for k in META}}],
            "claims": [{"claim_id": "K1", "text": claim or rows[row]["content"], "citation_ids": ["C2"]}]}


class ClaimsParserTests(unittest.TestCase):
    def parse(self, claims, **change):
        out = good_output() | {"claims": claims} | change
        return parse_llm_output(json.dumps(out, ensure_ascii=False))

    def test_valid_claims_are_parsed(self):
        out = self.parse([{"claim_id": "K1", "text": "Nhận định.", "citation_ids": ["C1"]}])
        self.assertEqual(out.claims[0].citation_ids, ("C1",))

    def test_output_without_claims_is_still_valid(self):
        self.assertEqual(parse_llm_output(json.dumps(good_output(), ensure_ascii=False)).claims, ())

    def test_invalid_claims_are_rejected(self):
        ok = {"claim_id": "K1", "text": "Nhận định.", "citation_ids": ["C1"]}
        for bad in (
            [ok | {"citation_ids": ["C9"]}],             # nhãn không có trong citations
            [ok | {"citation_ids": []}],                 # claim không có nguồn
            [ok, ok],                                    # claim_id trùng
            [ok | {"claim_id": "1"}],                    # sai dạng id
            [ok | {"extra": 1}],                         # field lạ
            "K1",                                        # không phải danh sách
        ):
            with self.subTest(bad=str(bad)[:40]), self.assertRaises(LLMBadOutputError):
                self.parse(bad)

    def test_insufficient_context_must_have_no_claims(self):
        out = {"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": [], "claims": [
            {"claim_id": "K1", "text": "x", "citation_ids": ["C1"]}]}
        with self.assertRaises(LLMBadOutputError):
            parse_llm_output(json.dumps(out, ensure_ascii=False))


class PromptV3Tests(unittest.TestCase):
    def test_claims_instruction_only_when_requested(self):
        self.assertIn(CLAIMS_INSTRUCTION, OUTPUT_INSTRUCTION_WITH_CLAIMS)  # str.replace không được thành no-op
        self.assertNotIn(CLAIMS_INSTRUCTION, OUTPUT_INSTRUCTION)
        plain = PromptBuilder().build(QUESTION, CONTEXT)
        claims = PromptBuilder(include_claims=True).build(QUESTION, CONTEXT)
        self.assertEqual((plain.prompt_version, claims.prompt_version), ("prompt_v3", "prompt_v3_claims"))
        self.assertIn('"claims"', claims.output_instruction)
        self.assertNotIn('"claims"', plain.output_instruction)

    def test_system_prompt_states_conditions_exceptions_and_refusal(self):
        for phrase in ("ngoại lệ", "KHI NÀO TỪ CHỐI", 'status="insufficient_context"', "Kiến thức pháp luật có sẵn"):
            self.assertIn(phrase, SYSTEM_INSTRUCTION)


class PipelineV2Tests(unittest.TestCase):
    def make(self, response=None, *, claims=True, cited_row=2, **kw):  # cited_row=2: C2 sau rerank [1, 2, 0]
        self.payload = copy.deepcopy(SAMPLE)
        self.retriever = Mock()
        self.retriever.retrieve.return_value = self.payload
        self.provider = FakeLLMProvider([response or claims_output(self.payload["results"], cited_row)] * 3)
        self.scorer = kw.pop("scorer", Mock(return_value=[1, 3, 2]))  # thứ tự sau rerank: dòng 1, 2, 0
        kw.setdefault("strict_rerank", False)
        return RAGPipeline(self.retriever, LLMService(self.provider, include_claims=claims), scorer=self.scorer, **kw)

    def source_order(self):
        prompt = self.provider.calls[-1][0].user
        ids = [r["chunk_id"] for r in self.payload["results"]]
        return sorted(range(3), key=lambda i: prompt.index("chunk_id=" + ids[i]))

    def test_verifier_gets_remapped_claims_and_response_has_no_claims(self):
        seen = []
        verifier = lambda out, ctx: seen.append((out, ctx)) or VerificationResult(passed=True)
        response = self.make(verifier=verifier).query(SAMPLE["question"])
        self.assertEqual(set(response), {"status", "answer", "citations"})
        self.assertEqual(response["citations"][0]["citation_id"], "C1")  # C2 của LLM được đánh lại thành C1
        output, context = seen[0]
        self.assertEqual(output.claims[0].citation_ids, ["C1"])
        self.assertEqual(output.citations, response["citations"])
        # Context đưa cho verifier dùng cùng nhãn với response: C1 phải tra ra đúng chunk được trích dẫn.
        self.assertEqual(context.by_label()["C1"].chunk_id, response["citations"][0]["chunk_id"])
        self.assertIn("claims", self.provider.calls[0][0].user)  # prompt đã yêu cầu claims

    def test_failed_verification_raises_citation_invalid_and_is_not_patched(self):
        failing = lambda out, ctx: VerificationResult(passed=False, claim_results=[ClaimCheck(
            claim_id="K1", text="x", supported=False, verdict="UNSUPPORTED", reason="không có nguồn")])
        with self.assertRaises(CitationInvalidError):
            self.make(verifier=failing).query(SAMPLE["question"])

    def test_real_verifier_accepts_grounded_claim_and_rejects_ungrounded_one(self):
        # Verifier thật của Người 2 tra nhãn trong context: nếu nhãn lệch sau khi đánh lại, ca đúng cũng bị loại.
        self.assertEqual(self.make(verifier=verify_response).query(SAMPLE["question"])["status"], "answered")
        rows = copy.deepcopy(SAMPLE["results"])
        bad = claims_output(rows, claim="Kết luận hoàn toàn khác không có trong điều luật này")
        with self.assertRaises(CitationInvalidError):
            self.make(bad, verifier=verify_response).query(SAMPLE["question"])

    def test_verifier_is_skipped_for_refusals(self):
        refuse = {"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}
        verifier = Mock()
        with self.assertLogs("team2_rag.pipeline", "INFO") as logs:
            result = self.make(refuse, verifier=verifier).query(SAMPLE["question"])
        self.assertEqual(result["status"], "insufficient_context")
        verifier.assert_not_called()
        self.assertTrue(any("reason=llm_insufficient" in line for line in logs.output))

    def test_rerank_disabled_keeps_retrieval_order_and_never_scores(self):
        self.make(rerank_enabled=False, cited_row=1).query(SAMPLE["question"])
        self.scorer.assert_not_called()
        self.assertEqual(self.source_order(), [0, 1, 2])

    def test_slow_rerank_falls_back_to_retrieval_order_then_skips_while_busy(self):
        gate = threading.Event()
        self.addCleanup(gate.set)
        slow = Mock(side_effect=lambda pairs: gate.wait(5) and [1, 3, 2])
        pipeline = self.make(scorer=slow, rerank_timeout=0.05, cited_row=1)
        with self.assertLogs("team2_rag.pipeline", "WARNING") as logs:
            pipeline.query(SAMPLE["question"])
            pipeline.query(SAMPLE["question"])  # model vẫn bận: không xếp hàng thêm
        self.assertEqual(self.source_order(), [0, 1, 2])
        self.assertEqual(slow.call_count, 1)
        self.assertTrue(any("RerankTimeout" in l for l in logs.output) and any("RerankBusy" in l for l in logs.output))

    def test_strict_mode_does_not_hide_a_rerank_timeout(self):
        gate = threading.Event()
        self.addCleanup(gate.set)
        pipeline = self.make(scorer=lambda pairs: gate.wait(5) and [1, 3, 2], rerank_timeout=0.05, strict_rerank=True)
        with self.assertRaises(RerankModelError):
            pipeline.query(SAMPLE["question"])
        self.assertEqual(self.provider.calls, [])

    def test_invalid_timeout_is_rejected(self):
        for bad in (0, -1, 46, True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.make(rerank_timeout=bad)

    def test_references_to_earlier_turns_are_refused_without_retrieval(self):
        pipeline = self.make()
        for question in ("Như trên thì sao?", "Điều ở trên có áp dụng cho công ty không?", "Lúc nãy bạn nói gì?"):
            with self.subTest(question=question):
                self.assertEqual(pipeline.query(question)["status"], "insufficient_context")
        self.retriever.retrieve.assert_not_called()


class VerificationOverHTTPTests(unittest.TestCase):
    def test_failed_verification_is_http_502_citation_invalid_and_success_keeps_contract(self):
        payload = copy.deepcopy(SAMPLE)
        retriever = Mock()
        retriever.retrieve.return_value = payload
        provider = FakeLLMProvider([claims_output(payload["results"])] * 2)
        verdicts = iter([VerificationResult(passed=False), VerificationResult(passed=True)])
        pipeline = RAGPipeline(retriever, LLMService(provider, include_claims=True), scorer=Mock(return_value=[1, 3, 2]),
                               strict_rerank=False, verifier=lambda out, ctx: next(verdicts))
        body = {"question": SAMPLE["question"], "history": []}
        with TestClient(create_app(pipeline), raise_server_exceptions=False) as client:
            bad = client.post("/internal/v1/query", json=body)
            self.assertEqual((bad.status_code, bad.json()["error"]["code"]), (502, "CITATION_INVALID"))
            good = client.post("/internal/v1/query", json=body)  # create_app tự kiểm tra rag_response.schema.json
            self.assertEqual(good.status_code, 200, good.text)
            self.assertEqual(set(good.json()), {"status", "answer", "citations"})


if __name__ == "__main__":
    unittest.main()
