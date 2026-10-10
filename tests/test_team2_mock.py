"""Validate actual mock output against the shared schema, including URI formats."""

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from team2_rag import query


class MockContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "contracts/v0.1/rag_response.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        cls.validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def test_both_scenarios_match_shared_contract(self):
        for scenario in ("answered", "insufficient_context"):
            with self.subTest(scenario=scenario):
                output = query("Câu hỏi mẫu", [], scenario=scenario)
                self.validator.validate(output)
                self.assertEqual(set(output), {"status", "answer", "citations"})

    def test_citation_markers_match_ids(self):
        output = query("Câu hỏi mẫu")
        for citation in output["citations"]:
            self.assertIn(f'[{citation["citation_id"]}]', output["answer"])

    def test_history_accepted_without_affecting_mock(self):
        history = [{"role": "user", "content": "Câu hỏi trước"}, {"role": "assistant", "content": "Câu trả lời trước"}]
        before = copy.deepcopy(history)
        self.assertEqual(query("Câu hỏi mới", history), query("Câu hỏi mới", []))
        self.assertEqual(history, before)

    def test_calls_do_not_share_mutable_citations(self):
        first = query("Câu hỏi mẫu")
        first["citations"][0]["chunk_id"] = "modified"
        second = query("Câu hỏi mẫu")
        self.assertEqual(second["citations"][0]["chunk_id"], "mock_v1_art1_clause1")
        self.validator.validate(second)

    def test_invalid_question_and_scenario_rejected(self):
        for question in ("", "  ", "x" * 2001, None):
            with self.subTest(question_type=type(question).__name__):
                with self.assertRaises(ValueError):
                    query(question)
        with self.assertRaises(ValueError):
            query("Câu hỏi mẫu", scenario="unknown")

    def test_schema_rejects_wrong_boundaries_and_invalid_citations(self):
        output = query("Câu hỏi mẫu")
        mutations = []
        public_output = copy.deepcopy(output)
        public_output["conversation_id"] = "backend-owned"
        mutations.append(public_output)
        missing_metadata = copy.deepcopy(output)
        del missing_metadata["citations"][0]["article_id"]
        mutations.append(missing_metadata)
        insecure_url = copy.deepcopy(output)
        insecure_url["citations"][0]["source_url"] = "http://example.com/mock-law"
        mutations.append(insecure_url)
        bad_status = copy.deepcopy(output)
        bad_status["status"] = "success"
        mutations.append(bad_status)
        empty_citations = copy.deepcopy(output)
        empty_citations["citations"] = []
        mutations.append(empty_citations)
        insufficient_with_marker = query("Câu hỏi mẫu", scenario="insufficient_context")
        insufficient_with_marker["answer"] += " [C1]"
        mutations.append(insufficient_with_marker)
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(ValidationError):
                    self.validator.validate(mutation)


if __name__ == "__main__":
    unittest.main()
