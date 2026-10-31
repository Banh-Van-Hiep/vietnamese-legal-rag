"""VLRA-36: Golden Dataset Phase 1 của Team 1 — đủ số câu, có căn cứ, gold_chunk_ids có trong corpus."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from eval_retrieval import validate_cases  # noqa: E402

GOLDEN = ROOT / "team1_data/golden/golden_phase1.json"
CHUNKS = ROOT / "data/doanh-nghiep/processed/chunks.jsonl"
REQUIRED = ("id", "question", "expected_status", "ground_truth", "gold_chunk_ids", "citation",
            "category", "author", "source", "review_status")


class GoldenPhase1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
        cls.corpus = {c["chunk_id"]: c for c in map(json.loads, CHUNKS.read_text(encoding="utf-8").splitlines())}

    def test_size_is_within_phase1_target(self):
        self.assertTrue(100 <= len(self.cases) <= 150, len(self.cases))

    def test_cases_pass_eval_validation(self):
        validate_cases(self.cases, set(self.corpus))

    def test_every_case_has_required_fields(self):
        for case in self.cases:
            with self.subTest(id=case.get("id")):
                self.assertEqual([k for k in REQUIRED if not case.get(k)], [])

    def test_draft_answers_are_verbatim_from_gold_chunk(self):
        drafts = [c for c in self.cases if c["review_status"].startswith("draft")]
        self.assertTrue(drafts)
        for case in drafts:
            with self.subTest(id=case["id"]):
                (cid,) = case["gold_chunk_ids"]
                chunk = self.corpus[cid]
                self.assertEqual(case["ground_truth"], chunk["content"])
                self.assertIn(chunk["article"], case["citation"])
                self.assertIn(chunk["document_number"], case["citation"])
                self.assertIn(chunk["legal_status"], ("con_hieu_luc", "het_hieu_luc_mot_phan"))

    def test_imported_cases_unchanged_from_team2_source(self):
        team2 = {c["id"]: c for c in json.loads(
            (ROOT / "team2_rag/data/golden/golden_phase1_30cai.json").read_text(encoding="utf-8"))}
        for case in self.cases:
            if case["review_status"] == "team2_reviewed":
                with self.subTest(id=case["id"]):
                    original = team2[case["id"]]
                    self.assertEqual({k: case[k] for k in original}, original)


if __name__ == "__main__":
    unittest.main()
