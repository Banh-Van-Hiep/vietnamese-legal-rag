"""Team 1: out-of-scope Dev cases for Team 2's refusal threshold (VLRA-T2-20)."""

import json
import unittest
from collections import Counter
from pathlib import Path

from scripts.eval_reranker import validate_dataset

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "team1_data/golden/out_of_scope_v1.json"
GOLDEN = ROOT / "team1_data/golden/golden_phase1.json"
CHUNKS = ROOT / "data/doanh-nghiep/processed/chunks.jsonl"


class OutOfScopeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(CASES.read_text(encoding="utf-8"))
        cls.corpus = {c["chunk_id"]: c for c in map(json.loads, CHUNKS.read_text(encoding="utf-8").splitlines())}

    def test_at_least_30_unanswerable_dev_cases(self):
        self.assertGreaterEqual(len(self.cases), 30)
        validate_dataset(self.cases, self.corpus)
        for case in self.cases:
            with self.subTest(id=case["id"]):
                self.assertEqual(case["expected_status"], "insufficient_context")
                self.assertEqual((case["gold_chunk_ids"], case["relevant_unit_groups"]), ([], []))
                self.assertEqual((case["citation"], case["ground_truth"]), ("", ""))
                self.assertEqual(case["review_status"], "draft_needs_legal_review")
                self.assertTrue(case["reason"])

    def test_categories_and_no_overlap_with_golden(self):
        counts = Counter(c["category"] for c in self.cases)
        self.assertEqual(set(counts), {"out_of_domain", "missing_information", "trap"})
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        self.assertFalse({c["id"] for c in self.cases} & {c["id"] for c in golden})
        self.assertFalse({c["question"] for c in self.cases} & {c["question"] for c in golden})


if __name__ == "__main__":
    unittest.main()
