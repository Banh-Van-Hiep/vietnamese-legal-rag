"""Internal FastAPI contract, errors, lifecycle and deadline behavior."""
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from team2_rag.api import create_app
from team2_rag.llm.errors import CitationInvalidError, LLMBadOutputError, LLMTimeoutError
from team2_rag.mock import make_mock_response
from team2_rag.reranker import RerankModelError
from team1_data.retrieval.errors import RetrievalUnavailableError

ROOT = Path(__file__).resolve().parents[1]
BODY = {"question": "Câu hỏi kiểm thử", "history": []}
ERROR_SCHEMA = json.loads((ROOT / "contracts/v0.1/error_response.schema.json").read_text())


class APITests(unittest.TestCase):
    def setUp(self):
        self.pipeline = Mock()
        self.pipeline.query.return_value = make_mock_response("answered")

    def check_error(self, response, status, code):
        self.assertEqual(response.status_code, status, response.text)
        self.assertEqual(response.json()["error"]["code"], code)
        Draft202012Validator(ERROR_SCHEMA).validate(response.json())
        self.assertTrue(response.headers["x-request-id"])

    def test_swagger_declares_json_body_and_example_can_be_submitted(self):
        with TestClient(create_app(self.pipeline)) as client:
            operation = client.get("/openapi.json").json()["paths"]["/internal/v1/query"]["post"]
            body = operation["requestBody"]
            self.assertTrue(body["required"])
            media = body["content"]["application/json"]
            Draft202012Validator(media["schema"]).validate(media["example"])
            self.assertEqual(client.post("/internal/v1/query", json=media["example"]).status_code, 200)

    def test_real_endpoint_uses_pipeline_and_preserves_request_trace(self):
        with TestClient(create_app(self.pipeline)) as client:
            response = client.post("/internal/v1/query", json=BODY, headers={"X-Request-ID": "trace-123"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["x-request-id"], "trace-123")
            self.pipeline.query.assert_called_once_with(BODY["question"], [], request_id="trace-123")
            self.assertEqual(set(response.json()), {"status", "answer", "citations"})
            self.assertEqual(client.get("/internal/v1/ready").status_code, 200)

    def test_startup_failure_keeps_liveness_but_blocks_queries(self):
        factory = Mock(side_effect=RuntimeError("SECRET configuration detail"))
        with TestClient(create_app(runtime_factory=factory)) as client:
            self.assertEqual(client.get("/internal/v1/health").json(), {"status": "up"})
            self.assertEqual(client.get("/internal/v1/ready").status_code, 503)
            response = client.post("/internal/v1/query", json=BODY)
            self.check_error(response, 503, "LLM_UNAVAILABLE")
            self.assertNotIn("SECRET", response.text)
        factory.assert_called_once()

    def test_runtime_loaded_once_and_closed(self):
        runtime = Mock(pipeline=self.pipeline)
        factory = Mock(return_value=runtime)
        with TestClient(create_app(runtime_factory=factory)) as client:
            for _ in range(2):
                self.assertEqual(client.post("/internal/v1/query", json=BODY).status_code, 200)
        factory.assert_called_once()
        runtime.close.assert_called_once()

    def test_input_not_coerced_or_silently_repaired(self):
        invalid = [{}, [], BODY | {"question": 42}, BODY | {"question": "   "},
                   BODY | {"question": "x" * 2001}, BODY | {"history": None},
                   BODY | {"history": "bad"}, BODY | {"scenario": "answered"},
                   BODY | {"history": [{"role": "user", "content": "x"}]}]
        with TestClient(create_app(self.pipeline)) as client:
            for payload in invalid:
                self.check_error(client.post("/internal/v1/query", json=payload), 400, "INVALID_REQUEST")
            for raw in ('{"question":"a","question":"b","history":[]}', '{',
                        '{"question":NaN,"history":[]}'):
                self.check_error(client.post("/internal/v1/query", content=raw,
                                            headers={"Content-Type": "application/json"}), 400, "INVALID_REQUEST")
        self.pipeline.query.assert_not_called()

    def test_media_type_body_size_and_unknown_query_parameters(self):
        with TestClient(create_app(self.pipeline)) as client:
            self.check_error(client.post("/internal/v1/query", content="x"), 415, "UNSUPPORTED_MEDIA_TYPE")
            self.check_error(client.post("/internal/v1/query", content="x" * (256 * 1024 + 1),
                                        headers={"Content-Type": "application/json"}), 413, "PAYLOAD_TOO_LARGE")
            self.check_error(client.post("/internal/v1/query?top_k=50", json=BODY), 400, "INVALID_REQUEST")

    def test_known_error_codes_and_safe_messages(self):
        for exc, status, code in [
            (LLMTimeoutError("SECRET"), 504, "LLM_TIMEOUT"),
            (LLMBadOutputError("SECRET"), 502, "INVALID_LLM_OUTPUT"),
            (CitationInvalidError("SECRET"), 502, "CITATION_INVALID"),
            (RetrievalUnavailableError("SECRET"), 503, "RETRIEVAL_UNAVAILABLE"),
            (RerankModelError("SECRET"), 503, "RETRIEVAL_UNAVAILABLE"),
            (RuntimeError("SECRET"), 500, "INTERNAL_ERROR"),
        ]:
            self.pipeline.query.side_effect = exc
            with self.subTest(code=code), TestClient(create_app(self.pipeline), raise_server_exceptions=False) as client:
                response = client.post("/internal/v1/query", json=BODY)
                self.check_error(response, status, code)
                self.assertNotIn("SECRET", response.text)

    def test_invalid_pipeline_response_is_not_returned_as_http_200(self):
        self.pipeline.query.return_value = {"status": "answered", "answer": "x", "citations": []}
        with TestClient(create_app(self.pipeline)) as client:
            self.check_error(client.post("/internal/v1/query", json=BODY), 502, "INVALID_LLM_OUTPUT")

    def test_malformed_or_unmatched_markers_are_http_502(self):
        for suffix in ("[C0]", "[C01]", "[c1]", "[ C1]", "[C1", "[C3]"):
            result = make_mock_response("answered")
            result["answer"] += " " + suffix
            self.pipeline.query.return_value = result
            with self.subTest(marker=suffix), TestClient(create_app(self.pipeline)) as client:
                self.check_error(client.post("/internal/v1/query", json=BODY), 502, "INVALID_LLM_OUTPUT")

    def test_shared_installer_receives_pipeline_errors_without_local_swallowing(self):
        class Team2Error(Exception):
            pass
        seen = []
        def install_error_handlers(app):
            seen.append(app)
            @app.exception_handler(Team2Error)
            async def shared_handler(request, exc):
                from fastapi.responses import JSONResponse
                return JSONResponse({"error": {"code": "SHARED_HANDLER", "message": "test", "retryable": False}},
                                    status_code=503)
        self.pipeline.query.side_effect = Team2Error("private")
        app = create_app(self.pipeline, error_installer=install_error_handlers)
        self.assertEqual(seen, [app])
        with TestClient(app) as client:
            response = client.post("/internal/v1/query", json=BODY)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["error"]["code"], "SHARED_HANDLER")

    def test_response_is_validated_by_injected_shared_model(self):
        model = Mock()
        model.model_validate.return_value.model_dump.return_value = make_mock_response("answered")
        with TestClient(create_app(self.pipeline, response_model=model)) as client:
            self.assertEqual(client.post("/internal/v1/query", json=BODY).status_code, 200)
        model.model_validate.assert_called_once_with(self.pipeline.query.return_value)

    def test_pydantic_output_validation_error_maps_to_502_in_legacy_adapter(self):
        from pydantic import BaseModel
        class InvalidOutputModel(BaseModel):
            must_exist: str
        with TestClient(create_app(self.pipeline, response_model=InvalidOutputModel)) as client:
            self.check_error(client.post("/internal/v1/query", json=BODY), 502, "INVALID_LLM_OUTPUT")

    def test_timeout_does_not_admit_more_work_until_worker_finishes(self):
        release, finished = threading.Event(), threading.Event()
        def blocked(*args, **kwargs):
            try:
                release.wait(2)
                return make_mock_response("answered")
            finally:
                finished.set()
        self.pipeline.query.side_effect = blocked
        with TestClient(create_app(self.pipeline, timeout_seconds=.02)) as client:
            try:
                self.check_error(client.post("/internal/v1/query", json=BODY), 504, "LLM_TIMEOUT")
                self.check_error(client.post("/internal/v1/query", json=BODY), 503, "LLM_UNAVAILABLE")
                self.assertEqual(self.pipeline.query.call_count, 1)
            finally:
                release.set()
                self.assertTrue(finished.wait(2))


if __name__ == "__main__":
    unittest.main()
