"""VLRA-T2-31: câu trả lời có Markdown (danh sách, bảng) qua được kiểm tra contract; kịch bản mock cho Team 3."""
import copy
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from team2_rag.api.mock_app import MOCK_MARKDOWN_RESPONSE, create_mock_app
from team2_rag.models import RAGResponse
from team2_rag.pipeline import validate_generated_response

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts/v0.1"


def _schema(name):
    return Draft202012Validator(json.loads((CONTRACTS / name).read_text(encoding="utf-8")))


class MarkdownAnswerValidationTests(unittest.TestCase):
    def check(self, response):
        out = validate_generated_response(copy.deepcopy(response), response_model=RAGResponse)
        self.assertEqual(out["answer"], response["answer"])  # không làm mất xuống dòng, bảng hay danh sách
        _schema("rag_response.schema.json").validate(out)

    def test_mock_markdown_fixture_is_valid(self):
        self.check(MOCK_MARKDOWN_RESPONSE)

    def test_nested_lists_table_bold_and_repeated_markers(self):
        response = copy.deepcopy(MOCK_MARKDOWN_RESPONSE)
        response["answer"] = (
            "### Điều kiện\n"
            "1. Điều kiện chung [C1]:\n"
            "   - a) có hồ sơ hợp lệ;\n"
            "   - b) **đã nộp lệ phí** [C1].\n"
            "2. Trường hợp riêng [C2].\n\n"
            "| STT | Nội dung | Căn cứ |\n"
            "|:---:|:---|---:|\n"
            "| 1 | Hồ sơ \\| lệ phí | [C1], [C2] |\n\n"
            "> Lưu ý: dữ liệu giả lập [C2]."
        )
        self.check(response)

    def test_marker_order_still_enforced_inside_table(self):
        response = copy.deepcopy(MOCK_MARKDOWN_RESPONSE)
        response["answer"] = "| Ý | Căn cứ |\n| --- | --- |\n| hai | [C2] |\n| một | [C1] |"
        with self.assertRaises(ValueError):  # [C2] xuất hiện trước [C1]; pydantic ValidationError là ValueError
            validate_generated_response(response, response_model=RAGResponse)


class MockScenarioTests(unittest.TestCase):
    def post(self, scenario):
        with mock.patch.dict(os.environ, {"RAG_MOCK_SCENARIO": scenario}):
            with TestClient(create_mock_app()) as client:
                return client.post("/internal/v1/query", json={"question": "Câu hỏi thử?", "history": []},
                                   headers={"X-Request-ID": "req-1"})

    def test_answered_markdown(self):
        res = self.post("answered_markdown")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["X-Request-ID"], "req-1")
        body = res.json()
        _schema("rag_response.schema.json").validate(body)
        self.assertEqual([c["citation_id"] for c in body["citations"]], ["C1", "C2"])
        self.assertIn("| --- |", body["answer"])

    def test_error_scenarios_match_real_app_wire_codes(self):
        expected = {
            "error_timeout": (504, "LLM_TIMEOUT", True),
            "error_busy": (503, "LLM_UNAVAILABLE", True),
            "error_invalid_output": (502, "INVALID_LLM_OUTPUT", False),
        }
        for scenario, (status, code, retryable) in expected.items():
            with self.subTest(scenario):
                res = self.post(scenario)
                self.assertEqual(res.status_code, status)
                self.assertEqual(res.headers["X-Request-ID"], "req-1")
                error = res.json()["error"]
                self.assertEqual((error["code"], error["retryable"]), (code, retryable))
                _schema("error_response.schema.json").validate(res.json())


if __name__ == "__main__":
    unittest.main()
