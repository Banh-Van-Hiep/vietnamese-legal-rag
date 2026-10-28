"""Ollama provider: config, request shape, response/failure handling, smoke script. Offline: every network call is mocked."""
import http.client
import io
import json
import socket
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from team2_rag import smoke_ollama
from team2_rag.answer import generate_answer, to_error_response
from team2_rag.config.settings import DEFAULT_OLLAMA_BASE_URL, PROVIDERS, ConfigError, load_settings, read_dotenv
from team2_rag.llm.errors import (CitationInvalidError, LLMAuthError, LLMBadOutputError, LLMConfigError,
                                  LLMContentBlockedError, LLMProviderError, LLMTimeoutError)
from team2_rag.llm.factory import create_llm_service, create_provider
from team2_rag.llm.http import HttpResponse, UrllibTransport
from team2_rag.llm.ollama_client import OllamaProvider
from team2_rag.tests.helpers import CONTEXT, GOOD_TEXT, QUESTION, REPO_ROOT, RecordingTransport, openai_ok, settings_for

PKG = REPO_ROOT / "team2_rag"
SAMPLE = json.loads((PKG / "data" / "samples" / "rerank_output_sample.json").read_text(encoding="utf-8"))
META = ("chunk_id", "document_id", "article_id", "document_title", "article", "clause", "point", "source_url")
OLLAMA = {"LLM_MODEL": "qwen2.5:3b", "LLM_CONTEXT_WINDOW_TOKENS": "8192"}


def ollama_settings(**extra):
    return settings_for("ollama", **{**OLLAMA, **extra})


class RaisingTransport:
    def __init__(self, exc):
        self.exc, self.calls = exc, 0

    def post_json(self, url, headers, body, timeout):
        self.calls += 1
        raise self.exc


def ask(transport):
    return create_llm_service(ollama_settings(), transport=transport).ask(QUESTION, CONTEXT)


class OllamaConfigTests(unittest.TestCase):
    def test_provider_is_registered_and_old_ones_kept(self):
        self.assertEqual(PROVIDERS, ("openai", "gemini", "qwen", "ollama"))

    def test_no_api_key_required(self):
        s = load_settings(env={"LLM_PROVIDER": "ollama", **OLLAMA})
        s.validate()
        self.assertEqual((s.api_key(), s.ollama_base_url), ("", DEFAULT_OLLAMA_BASE_URL))
        self.assertEqual(DEFAULT_OLLAMA_BASE_URL, "http://localhost:11434/v1")

    def test_other_providers_still_require_keys(self):
        for provider in ("openai", "gemini", "qwen"):
            with self.subTest(provider), self.assertRaises(ConfigError):
                load_settings(env={"LLM_PROVIDER": provider, "LLM_MODEL": "m"}).validate()

    def test_model_and_context_window_are_required(self):
        with self.assertRaises(ConfigError):
            load_settings(env={"LLM_PROVIDER": "ollama", "LLM_CONTEXT_WINDOW_TOKENS": "8192"}).validate()
        with self.assertRaises(ConfigError) as ctx:
            load_settings(env={"LLM_PROVIDER": "ollama", "LLM_MODEL": "qwen2.5:3b"}).validate()
        self.assertIn("LLM_CONTEXT_WINDOW_TOKENS", str(ctx.exception))

    def test_window_must_still_exceed_output_plus_margin(self):
        env = {"LLM_PROVIDER": "ollama", "LLM_MODEL": "m", "LLM_CONTEXT_WINDOW_TOKENS": "1756"}
        with self.assertRaises(ConfigError):
            load_settings(env=env).validate()

    def test_env_overrides(self):
        s = load_settings(env={"LLM_PROVIDER": " Ollama ", **OLLAMA, "OLLAMA_BASE_URL": " http://127.0.0.1:9999/v1 ",
                               "LLM_TIMEOUT_SECONDS": "90", "LLM_TEMPERATURE": "0.3"})
        s.validate()
        self.assertEqual((s.provider, s.ollama_base_url, s.timeout_seconds, s.temperature),
                         ("ollama", "http://127.0.0.1:9999/v1", 90.0, 0.3))

    def test_timeout_limits(self):
        base = {"LLM_PROVIDER": "ollama", **OLLAMA}
        load_settings(env=base | {"LLM_TIMEOUT_SECONDS": "600"}).validate()
        for bad in ("0", "601"):
            with self.subTest(bad), self.assertRaises(ConfigError):
                load_settings(env=base | {"LLM_TIMEOUT_SECONDS": bad}).validate()
        # remote providers keep the original 30s ceiling and default
        for provider, key in (("openai", "OPENAI_API_KEY"), ("gemini", "GEMINI_API_KEY"), ("qwen", "QWEN_API_KEY")):
            with self.subTest(provider), self.assertRaises(ConfigError):
                load_settings(env={"LLM_PROVIDER": provider, "LLM_MODEL": "m", key: "k", "LLM_TIMEOUT_SECONDS": "31"}).validate()
        self.assertEqual(load_settings(env={"LLM_PROVIDER": "ollama", **OLLAMA}).timeout_seconds, 30.0)

    def test_base_url_must_be_http(self):
        with self.assertRaises(ConfigError):
            load_settings(env={"LLM_PROVIDER": "ollama", **OLLAMA, "OLLAMA_BASE_URL": "localhost:11434/v1"}).validate()

    def test_retries_still_forced_to_zero(self):
        with self.assertRaises(ConfigError):
            load_settings(env={"LLM_PROVIDER": "ollama", **OLLAMA, "LLM_MAX_RETRIES": "1"}).validate()

    def test_env_example_is_secret_free_and_loadable(self):
        path = PKG / ".env.ollama.example"
        text = path.read_text(encoding="utf-8")
        for marker in ("sk-", "AIza", "API_KEY"):
            self.assertNotIn(marker, text)
        s = load_settings(env=read_dotenv(path))
        s.validate()
        self.assertEqual((s.provider, s.model), ("ollama", "qwen2.5:3b"))


class OllamaRequestTests(unittest.TestCase):
    def test_payload_uses_ollama_compatible_parameters(self):
        t = RecordingTransport(openai_ok())
        svc = create_llm_service(ollama_settings(LLM_MAX_OUTPUT_TOKENS="800", LLM_TEMPERATURE="0.2", LLM_TIMEOUT_SECONDS="77"), transport=t)
        self.assertEqual(svc.provider.name, "ollama")
        svc.ask(QUESTION, CONTEXT)
        call = t.calls[0]
        self.assertEqual(call["url"], "http://localhost:11434/v1/chat/completions")
        self.assertEqual(call["timeout"], 77.0)
        body = call["body"]
        self.assertEqual(body["model"], "qwen2.5:3b")
        self.assertEqual(body["response_format"]["type"], "json_schema")
        from jsonschema import Draft202012Validator
        schema = body["response_format"]["json_schema"]["schema"]
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        good = json.loads(openai_ok().json["choices"][0]["message"]["content"])
        self.assertTrue(validator.is_valid(good))
        self.assertFalse(validator.is_valid({**good, "answer": "Nội dung không có marker."}))
        self.assertFalse(validator.is_valid({**good, "citations": []}))
        self.assertTrue(validator.is_valid({"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []}))
        self.assertFalse(validator.is_valid({**good, "status": "insufficient_context"}))
        self.assertEqual((body["max_tokens"], body["temperature"]), (800, 0.2))
        self.assertNotIn("max_completion_tokens", body)  # OpenAI-only parameter, not in Ollama's supported list
        self.assertNotIn("stream", body)
        self.assertIn("LEGAL_CONTEXT", body["messages"][1]["content"])

    def test_no_real_credentials_are_sent(self):
        t = RecordingTransport(openai_ok())
        ask(t)
        sent = json.dumps([t.calls[0]["headers"], t.calls[0]["body"]])
        for secret in ("test-openai-key", "test-gemini-key", "test-qwen-key"):  # present in env_for(), must not leak
            self.assertNotIn(secret, sent)

    def test_custom_base_url_trailing_slash(self):
        t = RecordingTransport(openai_ok())
        create_llm_service(ollama_settings(OLLAMA_BASE_URL="http://10.0.0.5:11434/v1/"), transport=t).ask(QUESTION, CONTEXT)
        self.assertEqual(t.calls[0]["url"], "http://10.0.0.5:11434/v1/chat/completions")

    def test_existing_providers_keep_their_token_parameter(self):
        for provider, field, other in (("openai", "max_completion_tokens", "max_tokens"), ("qwen", "max_tokens", "max_completion_tokens")):
            with self.subTest(provider):
                t = RecordingTransport(openai_ok())
                create_llm_service(settings_for(provider), transport=t).ask(QUESTION, CONTEXT)
                self.assertIn(field, t.calls[0]["body"])
                self.assertNotIn(other, t.calls[0]["body"])

    def test_factory_builds_ollama_provider(self):
        self.assertIsInstance(create_provider(ollama_settings()), OllamaProvider)


class OllamaResponseTests(unittest.TestCase):
    def test_success_with_usage_and_finish_reason(self):
        result = ask(RecordingTransport(openai_ok()))
        self.assertEqual((result.output.status, result.provider, result.model), ("answered", "ollama", "qwen2.5:3b"))
        self.assertEqual((result.usage.input_tokens, result.usage.output_tokens, result.finish_reason), (120, 40, "stop"))

    def test_missing_or_odd_usage_is_tolerated(self):
        for usage in (None, "x", {"prompt_tokens": "7", "completion_tokens": None}):
            with self.subTest(usage):
                resp = HttpResponse(200, {"choices": [{"message": {"content": GOOD_TEXT}, "finish_reason": "stop"}], "usage": usage})
                r = ask(RecordingTransport(resp))
                self.assertEqual((r.usage.input_tokens, r.usage.output_tokens), (None, None))

    def test_model_not_found_is_a_clear_config_error(self):
        body = {"error": {"message": 'model "qwen2.5:3b" not found, try pulling it first', "type": "api_error"}}
        with self.assertRaises(LLMConfigError) as ctx:
            ask(RecordingTransport(HttpResponse(404, body)))
        self.assertIn("ollama pull qwen2.5:3b", str(ctx.exception))
        self.assertEqual((ctx.exception.status, ctx.exception.provider), (404, "ollama"))
        self.assertEqual(to_error_response(ctx.exception)["error"]["code"], "LLM_UNAVAILABLE")

    def test_http_errors_are_normalized(self):
        for status, exc in ((500, LLMProviderError), (503, LLMProviderError), (401, LLMAuthError), (400, LLMConfigError), (408, LLMTimeoutError)):
            with self.subTest(status), self.assertRaises(exc):
                ask(RecordingTransport(HttpResponse(status, {"error": {"message": "boom"}})))

    def test_malformed_envelopes_raise_bad_output(self):
        bad = [
            HttpResponse(200, None, "<html>not json</html>"),
            HttpResponse(200, {}),
            HttpResponse(200, {"choices": []}),
            HttpResponse(200, {"choices": "oops"}),
            HttpResponse(200, {"choices": ["oops"]}),
            HttpResponse(200, {"choices": [{"message": "oops"}]}),
            HttpResponse(200, {"choices": [{"message": {"content": 42}}]}),
        ]
        for i, resp in enumerate(bad):
            with self.subTest(i), self.assertRaises(LLMBadOutputError) as ctx:
                ask(RecordingTransport(resp))
            self.assertEqual(ctx.exception.error_code, "INVALID_LLM_OUTPUT")

    def test_model_text_that_is_not_the_contract_raises_bad_output(self):
        texts = ["", None, "Chắc chắn rồi! Đây là câu trả lời.", GOOD_TEXT[:60], json.dumps({"answer": "thiếu field"}),
                 "```json\n" + GOOD_TEXT + "\n```"]
        for text in texts:
            with self.subTest(text), self.assertRaises(LLMBadOutputError):
                ask(RecordingTransport(openai_ok(text)))

    def test_truncated_generation_is_bad_output_not_success(self):
        with self.assertRaises(LLMBadOutputError):
            ask(RecordingTransport(openai_ok(GOOD_TEXT[:80], finish="length")))

    def test_refusal_and_content_filter(self):
        refusal = HttpResponse(200, {"choices": [{"message": {"content": "", "refusal": "no"}, "finish_reason": "stop"}]})
        with self.assertRaises(LLMContentBlockedError):
            ask(RecordingTransport(refusal))
        with self.assertRaises(LLMContentBlockedError):
            ask(RecordingTransport(openai_ok("", finish="content_filter")))

    def test_transport_failures_propagate_with_internal_codes(self):
        cases = ((LLMTimeoutError("t"), "LLM_TIMEOUT"), (LLMProviderError("down"), "LLM_UNAVAILABLE"))
        for exc, code in cases:
            with self.subTest(code):
                rt = RaisingTransport(exc)
                with self.assertRaises(type(exc)) as ctx:
                    ask(rt)
                self.assertEqual((rt.calls, to_error_response(ctx.exception)["error"]["code"]), (1, code))  # one call: no retry


class UrllibTransportFailureTests(unittest.TestCase):
    """The real transport against mocked urlopen: what a stopped, crashing or slow Ollama looks like to Python."""

    def post(self, side_effect=None, response=None):
        with patch("urllib.request.urlopen", side_effect=side_effect, return_value=response):
            return UrllibTransport().post_json("http://localhost:11434/v1/chat/completions", {}, {"a": 1}, 5)

    def test_connection_refused_server_not_running(self):
        with self.assertRaises(LLMProviderError):
            self.post(urllib.error.URLError(ConnectionRefusedError(111, "refused")))

    def test_connection_reset_and_remote_disconnect_are_provider_errors(self):
        for exc in (ConnectionResetError(), BrokenPipeError(), http.client.RemoteDisconnected("closed"), http.client.IncompleteRead(b"x")):
            with self.subTest(type(exc).__name__), self.assertRaises(LLMProviderError):
                self.post(exc)

    def test_timeouts(self):
        for exc in (socket.timeout("t"), TimeoutError(), urllib.error.URLError(socket.timeout("t"))):
            with self.subTest(repr(exc)), self.assertRaises(LLMTimeoutError):
                self.post(exc)

    def test_http_error_body_is_returned_not_raised(self):
        err = urllib.error.HTTPError("u", 404, "nf", {}, io.BytesIO(b'{"error": {"message": "model not found"}}'))
        r = self.post(err)
        self.assertEqual((r.status, r.json["error"]["message"]), (404, "model not found"))

    def test_non_json_body_is_kept_as_text(self):
        err = urllib.error.HTTPError("u", 502, "bad", {}, io.BytesIO(b"<html>bad gateway</html>"))
        r = self.post(err)
        self.assertEqual((r.status, r.json, r.text), (502, None, "<html>bad gateway</html>"))


class OllamaEndToEndOfflineTests(unittest.TestCase):
    """generate_answer with the real settings -> token budget -> OllamaProvider, transport mocked."""

    def reply(self, index=0, **override):
        cit = {"citation_id": "C1", **{k: SAMPLE["results"][index][k] for k in META}} | override
        return json.dumps({"status": "answered", "answer": "Luật quy định về thành lập và hoạt động của doanh nghiệp [C1].",
                           "citations": [cit]}, ensure_ascii=False)

    def test_answer_with_validated_citations_and_token_budget(self):
        t = RecordingTransport(openai_ok(self.reply()))
        r = generate_answer(SAMPLE, [], llm_service=create_llm_service(ollama_settings(), transport=t), settings=ollama_settings(),
                            request_id="req-1")
        self.assertEqual((r["status"], [c["chunk_id"] for c in r["citations"]]), ("answered", [SAMPLE["results"][0]["chunk_id"]]))
        self.assertEqual(sorted(r), ["answer", "citations", "status"])  # response contract unchanged
        self.assertIn(SAMPLE["results"][0]["chunk_id"], t.calls[0]["body"]["messages"][1]["content"])

    def test_generate_answer_builds_ollama_service_from_settings(self):
        t = RecordingTransport(openai_ok(self.reply()))
        with patch("team2_rag.llm.openai_client.UrllibTransport", lambda: t):  # default transport used when none is injected
            r = generate_answer(SAMPLE, [], settings=ollama_settings())  # no llm_service: path used by the real runtime
        self.assertEqual(r["status"], "answered")
        self.assertTrue(t.calls[0]["url"].endswith("/v1/chat/completions"))

    def test_citation_with_wrong_metadata_is_rejected(self):
        t = RecordingTransport(openai_ok(self.reply(article="Điều 99")))
        with self.assertRaises(CitationInvalidError) as ctx:
            generate_answer(SAMPLE, [], llm_service=create_llm_service(ollama_settings(), transport=t), settings=ollama_settings())
        self.assertEqual(to_error_response(ctx.exception)["error"]["code"], "CITATION_INVALID")

    def test_citation_to_chunk_that_was_never_sent_is_rejected(self):
        fake = {"chunk_id": "khong-ton-tai__dieu-9"}
        t = RecordingTransport(openai_ok(self.reply(**fake)))
        with self.assertRaises(CitationInvalidError):
            generate_answer(SAMPLE, [], llm_service=create_llm_service(ollama_settings(), transport=t), settings=ollama_settings())

    def test_insufficient_context_without_sources_does_not_call_ollama(self):
        t = RecordingTransport()
        r = generate_answer({"question": SAMPLE["question"], "results": []}, [], llm_service=create_llm_service(ollama_settings(), transport=t))
        self.assertEqual((r["status"], t.calls), ("insufficient_context", []))

    def test_public_error_codes_are_unchanged(self):
        try:
            from team2_rag.errors import ErrorCode, classify
        except ImportError:  # pydantic is a dev dependency (requirements-dev.txt)
            self.skipTest("pydantic chưa cài")
        self.assertEqual(classify(LLMConfigError("m", status=404)), ErrorCode.SERVICE_UNAVAILABLE)
        self.assertEqual(classify(LLMTimeoutError("t")), ErrorCode.UPSTREAM_TIMEOUT)
        self.assertEqual(classify(LLMProviderError("p")), ErrorCode.SERVICE_UNAVAILABLE)
        self.assertEqual(classify(LLMBadOutputError("b")), ErrorCode.UPSTREAM_INVALID_RESPONSE)


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def models_response(*ids):
    return lambda url, timeout: FakeResp(json.dumps({"object": "list", "data": [{"id": i} for i in ids]}).encode())


class SmokeScriptTests(unittest.TestCase):
    ENV = {"LLM_PROVIDER": "ollama", **OLLAMA, "LLM_TIMEOUT_SECONDS": "120"}

    def settings(self):
        return load_settings(env=self.ENV)

    def test_preflight_ok_for_exact_and_latest_tag(self):
        smoke_ollama.preflight(self.settings(), models_response("qwen2.5:3b"))
        smoke_ollama.preflight(load_settings(env=self.ENV | {"LLM_MODEL": "qwen2.5"}), models_response("qwen2.5:latest"))

    def test_preflight_reports_missing_model(self):
        with self.assertRaises(smoke_ollama.SmokeError) as ctx:
            smoke_ollama.preflight(self.settings(), models_response("llama3.2:3b"))
        self.assertIn("ollama pull qwen2.5:3b", str(ctx.exception))

    def test_preflight_reports_unreachable_server_and_bad_url(self):
        def refuse(url, timeout):
            raise urllib.error.URLError(ConnectionRefusedError(111, "refused"))

        def not_found(url, timeout):
            raise urllib.error.HTTPError(url, 404, "nf", {}, io.BytesIO(b"404 page not found"))

        for opener, text in ((refuse, "Cannot reach Ollama"), (not_found, "HTTP 404"),
                             (lambda url, timeout: FakeResp(b"<html>"), "model list")):
            with self.subTest(text), self.assertRaises(smoke_ollama.SmokeError) as ctx:
                smoke_ollama.preflight(self.settings(), opener)
            self.assertIn(text, str(ctx.exception))

    def run_main(self, env=None, urlopen=None, **patches):
        with patch.multiple("team2_rag.smoke_ollama", **patches) if patches else patch.dict({}):
            with patch("sys.stdout", new=io.StringIO()) as out, patch("sys.stderr", new=io.StringIO()) as err:
                code = smoke_ollama.main(env=self.ENV if env is None else env, urlopen=urlopen or models_response("qwen2.5:3b"))
        return code, out.getvalue(), err.getvalue()

    def test_refuses_non_ollama_provider_without_any_call(self):
        def boom(*a, **k):
            raise AssertionError("must not touch the network or a paid provider")

        code, _, err = self.run_main(env={"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4o", "OPENAI_API_KEY": "k"},
                                     urlopen=boom, generate_answer=boom)
        self.assertEqual(code, 2)
        self.assertIn("expected 'ollama'", err)

    def test_success_path_prints_validated_response(self):
        good = {"status": "answered", "answer": "Nội dung [C1].", "citations": [{"citation_id": "C1", **{k: SAMPLE["results"][0][k] for k in META}}]}
        code, out, err = self.run_main(generate_answer=lambda *a, **k: good)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), good)
        self.assertIn("SMOKE OK: provider=ollama model=qwen2.5:3b", err)

    def test_llm_failure_returns_1_with_reason(self):
        def fail(*a, **k):
            raise LLMTimeoutError("t")

        code, out, err = self.run_main(generate_answer=fail)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("LLMTimeoutError (LLM_TIMEOUT)", err)

    def test_config_error_returns_2(self):
        code, _, err = self.run_main(env={"LLM_PROVIDER": "ollama", "LLM_MODEL": "qwen2.5:3b"})
        self.assertEqual(code, 2)
        self.assertIn("LLM_CONTEXT_WINDOW_TOKENS", err)


if __name__ == "__main__":
    unittest.main()
