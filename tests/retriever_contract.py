"""Reusable retrieval v0.1 checks; concrete unittest classes supply an instance.

Hybrid can inherit this mixin without changing its production base class.
"""

import json
import math
from pathlib import Path



class RetrieverContractTests:
    method = None
    sample_question = "doanh nghiệp"

    def test_contract_schema_and_semantics(self):
        try:
            from jsonschema import Draft202012Validator, FormatChecker
        except ImportError:
            self.skipTest("requires jsonschema")
        schema = Path(__file__).resolve().parents[1] / "contracts/v0.1/retrieval_output.schema.json"
        validator = Draft202012Validator(json.loads(schema.read_text(encoding="utf-8")),
                                        format_checker=FormatChecker())
        for k in (1, 20, 50):
            with self.subTest(k=k):
                output = self.retriever.retrieve(self.sample_question, top_k=k)
                validator.validate(output)
                rows = output["results"]
                self.assertLessEqual(len(rows), k)
                self.assertEqual([r["rank"] for r in rows], list(range(1, len(rows) + 1)))
                self.assertEqual(len({r["chunk_id"] for r in rows}), len(rows))
                scores = [r["score"] for r in rows]
                self.assertTrue(all(math.isfinite(s) for s in scores))
                self.assertEqual(scores, sorted(scores, reverse=True))
                self.assertTrue(all(r["retrieval_method"] == self.method for r in rows))

    def test_contract_trim_and_boundaries(self):
        self.assertEqual(self.retriever.retrieve("  " + self.sample_question + "  ")["question"],
                         self.sample_question)
        self.assertEqual(self.retriever.retrieve("a" * 4000, top_k=50)["question"], "a" * 4000)

    def test_contract_rejects_eight_invalid_inputs(self):
        for question, k in [("", 5), ("   ", 5), (None, 5), ("a" * 4001, 5),
                            (self.sample_question, 0), (self.sample_question, 51),
                            (self.sample_question, True), (self.sample_question, 2.0)]:
            with self.subTest(question=repr(question)[:30], k=k), self.assertRaises(ValueError):
                self.retriever.retrieve(question, top_k=k)
