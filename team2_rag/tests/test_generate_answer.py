"""Luồng chính VLRA-29: generate_answer / to_error_response (trong answer.py) và query() mock (service.py, không đổi). Không cần API key hay mạng."""
import json, unittest
from unittest.mock import patch
from team2_rag import query
from team2_rag.answer import generate_answer, to_error_response
from team2_rag.config.settings import ConfigError, load_settings
from team2_rag.llm.errors import (CitationInvalidError, LLMAuthError, LLMBadOutputError, LLMConfigError, LLMContentBlockedError,
                                  LLMProviderError, LLMRateLimitError, LLMTimeoutError)
from team2_rag.llm.factory import create_llm_service
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.http import HttpResponse
from team2_rag.llm.service import LLMService
from team2_rag.mock import make_mock_response
from team2_rag.prompts import ContextBuildError
from team2_rag.tests.helpers import REPO_ROOT, RecordingTransport, env_for, openai_ok, settings_for

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

SAMPLE = json.loads((REPO_ROOT / "team2_rag" / "data" / "samples" / "rerank_output_sample.json").read_text(encoding="utf-8"))
CONTRACTS = REPO_ROOT / "contracts" / "v0.1"
META = ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")


def schema(name):
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))

def reply(*indexes, answer=None):
    labels = [f"C{i + 1}" for i in indexes]  # nhãn trong context = vị trí chunk trong results (C1 = results[0]...)
    cits = [{"citation_id": lb} | {k: SAMPLE["results"][i][k] for k in META} for lb, i in zip(labels, indexes)]
    return {"status": "answered", "answer": answer or " ".join(f"Ý {lb} [{lb}]." for lb in labels), "citations": cits}


class SampleDataTests(unittest.TestCase):
    def test_sample_matches_team1_retrieval_schema(self):
        if jsonschema is None: self.skipTest("jsonschema chưa cài")
        jsonschema.validate(SAMPLE, schema("retrieval_output.schema.json"))


class GenerateAnswerTests(unittest.TestCase):
    def test_context_to_llm_to_answer_with_fake_client(self):
        p = FakeLLMProvider([reply(0)])
        r = generate_answer(SAMPLE, llm_service=LLMService(p))
        self.assertEqual((r["status"], [c["chunk_id"] for c in r["citations"]]), ("answered", [SAMPLE["results"][0]["chunk_id"]]))
        user = p.calls[0][0].user
        for res in SAMPLE["results"]:
            self.assertIn(f"chunk_id={res['chunk_id']}", user); self.assertIn(res["content"], user)
        if jsonschema: jsonschema.validate(r, schema("rag_response.schema.json"))

    def test_real_provider_request_path_via_recording_transport(self):
        t = RecordingTransport(openai_ok(json.dumps(reply(1), ensure_ascii=False)))
        svc = create_llm_service(settings_for("openai"), transport=t)
        r = generate_answer(SAMPLE, llm_service=svc)
        self.assertEqual(r["citations"][0]["chunk_id"], SAMPLE["results"][1]["chunk_id"])
        body = t.calls[0]["body"]
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertIn(SAMPLE["results"][0]["chunk_id"], body["messages"][1]["content"])
        self.assertNotIn("test-openai-key", str(body))

    def test_empty_results_do_not_call_llm(self):
        p = FakeLLMProvider([])
        r = generate_answer({"question": SAMPLE["question"], "results": []}, llm_service=LLMService(p))
        self.assertEqual((r["status"], r["citations"], p.calls), ("insufficient_context", [], []))

    def test_empty_or_blank_llm_output_is_invalid_llm_output(self):
        for text in ("", "   \n", "null", "{}"):
            p = FakeLLMProvider([text])
            with self.assertRaises(LLMBadOutputError, msg=repr(text)): generate_answer(SAMPLE, llm_service=LLMService(p))
        for empty in (openai_ok(text=""), HttpResponse(200, {"choices": [{"message": {"role": "assistant", "content": None}, "finish_reason": "stop"}]})):
            svc = create_llm_service(settings_for("openai"), transport=RecordingTransport(empty))
            with self.assertRaises(LLMBadOutputError): generate_answer(SAMPLE, llm_service=svc)

    def test_chunk_id_not_in_context_is_rejected_not_returned(self):
        bad = reply(0); bad["citations"][0]["chunk_id"] = "luat-59-2020-qh14-v1__dieu-99__k9__9"
        with self.assertRaises(CitationInvalidError): generate_answer(SAMPLE, llm_service=LLMService(FakeLLMProvider([bad])))

    def test_invalid_candidate_raises_context_error_before_llm(self):
        p = FakeLLMProvider([])
        data = json.loads(json.dumps(SAMPLE)); data["results"][0]["source_url"] = "luat-59.pdf"
        with self.assertRaises(ContextBuildError): generate_answer(data, llm_service=LLMService(p))
        self.assertEqual(p.calls, [])

    def test_settings_without_api_key_fails_fast_no_network(self):
        with self.assertRaises(ConfigError): generate_answer(SAMPLE, settings=load_settings(env={"LLM_MODEL": "m"}))

    def test_settings_limits_and_token_budget_are_wired(self):
        p = FakeLLMProvider([reply(0)])
        with patch("team2_rag.answer.create_llm_service", return_value=LLMService(p)):
            generate_answer(SAMPLE, settings=settings_for("openai", LLM_MAX_CONTEXT_CHUNKS="1"))
            user = p.calls[0][0].user
            self.assertIn(SAMPLE["results"][0]["chunk_id"], user); self.assertNotIn(SAMPLE["results"][1]["chunk_id"], user)
            # có context window nhưng provider chưa có counter -> lỗi cấu hình rõ ràng, không rơi về đếm ký tự
            with self.assertRaises(ConfigError):
                generate_answer(SAMPLE, settings=settings_for("gemini", LLM_CONTEXT_WINDOW_TOKENS="100000"))


class ErrorResponseTests(unittest.TestCase):
    CASES = [(LLMTimeoutError("t"), "LLM_TIMEOUT", True), (LLMRateLimitError("r"), "LLM_UNAVAILABLE", True),
             (LLMProviderError("p"), "LLM_UNAVAILABLE", True), (LLMAuthError("a"), "LLM_UNAVAILABLE", True),
             (LLMConfigError("c"), "LLM_UNAVAILABLE", True), (LLMContentBlockedError("b"), "LLM_UNAVAILABLE", True),
             (LLMBadOutputError("x", raw_text="SECRET-RAW"), "INVALID_LLM_OUTPUT", False), (CitationInvalidError("y"), "CITATION_INVALID", False)]

    def test_codes_retryable_and_schema(self):
        for exc, code, retryable in self.CASES:
            body = to_error_response(exc)
            self.assertEqual((body["error"]["code"], body["error"]["retryable"]), (code, retryable))
            if jsonschema: jsonschema.validate(body, schema("error_response.schema.json"))

    def test_message_is_safe(self):
        exc = LLMAuthError("openai: HTTP 401 key=sk-SECRET prompt=Câu hỏi riêng", provider="openai", status=401)
        text = json.dumps(to_error_response(exc), ensure_ascii=False)
        for secret in ("sk-SECRET", "Câu hỏi riêng", "401"): self.assertNotIn(secret, text)
        self.assertNotIn("SECRET-RAW", json.dumps(to_error_response(LLMBadOutputError("x", raw_text="SECRET-RAW"))))

    def test_non_llm_errors_are_left_to_api_layer(self):
        for exc in (ValueError("v"), ContextBuildError("c"), RuntimeError("r")): self.assertIsNone(to_error_response(exc))


class MockQueryRegressionTests(unittest.TestCase):
    def test_query_is_still_the_mock_for_team3(self):
        self.assertEqual(query("Câu hỏi bất kỳ"), make_mock_response("answered"))
        self.assertEqual(query("x", scenario="insufficient_context"), make_mock_response("insufficient_context"))
        with self.assertRaises(ValueError): query("   ")

if __name__ == "__main__": unittest.main()
