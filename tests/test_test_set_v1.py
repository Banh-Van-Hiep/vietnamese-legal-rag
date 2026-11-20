"""Test Set v1 (Team 1): frozen, independent of the Dev Set, answers verbatim from gold chunks."""

import hashlib
import json
import re
import sys
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from eval_retrieval import validate_cases  # noqa: E402

GOLDEN = ROOT / "team1_data/golden"
TEST_SET = GOLDEN / "test_set_v1.json"
MANIFEST = GOLDEN / "test_set_v1.manifest.json"
CHUNKS = ROOT / "data/doanh-nghiep/processed/chunks.jsonl"
LAW = ("luat-59-2020-qh14-v1", "vbhn-67-vbhn-vpqh-v1")


def article_key(chunk):
    number = re.sub(r"\D", "", chunk["article"])
    return ("law", number) if chunk["document_id"] in LAW else (chunk["document_id"], number)


class TestSetV1Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(TEST_SET.read_text(encoding="utf-8"))
        cls.corpus = {c["chunk_id"]: c for c in map(json.loads, CHUNKS.read_text(encoding="utf-8").splitlines())}
        cls.dev = (json.loads((GOLDEN / "golden_phase1.json").read_text(encoding="utf-8"))
                   + json.loads((GOLDEN / "out_of_scope_v1.json").read_text(encoding="utf-8")))

    def test_cases_pass_eval_validation(self):
        validate_cases(self.cases, set(self.corpus))

    def test_has_answerable_multi_clause_and_refusal_cases(self):
        kinds = {c["complexity"] for c in self.cases}
        self.assertEqual(kinds, {"single_clause", "multi_clause", "refusal"})
        for case in self.cases:
            with self.subTest(id=case["id"]):
                self.assertEqual(case["split"], "test")
                self.assertEqual(case["complexity"] == "refusal", case["expected_status"] == "insufficient_context")

    def test_independent_of_dev_set(self):
        dev_questions = {c["question"].strip() for c in self.dev}
        dev_articles = {article_key(self.corpus[i]) for c in self.dev for i in c["gold_chunk_ids"]}
        for case in self.cases:
            with self.subTest(id=case["id"]):
                self.assertNotIn(case["question"].strip(), dev_questions)
                ids = [i for g in case["relevant_unit_groups"] for i in g]
                self.assertFalse({article_key(self.corpus[i]) for i in ids} & dev_articles)

    def test_answers_are_verbatim_from_gold_chunks(self):
        for case in (c for c in self.cases if c["expected_status"] == "answered"):
            with self.subTest(id=case["id"]):
                chunks = [self.corpus[i] for i in case["gold_chunk_ids"]]
                self.assertEqual(case["ground_truth"], "\n\n".join(c["content"] for c in chunks))
                self.assertIn(chunks[0]["article"], case["citation"])
                self.assertIn(chunks[0]["document_number"], case["citation"])
                for chunk in chunks:
                    self.assertIn(chunk["legal_status"], ("con_hieu_luc", "het_hieu_luc_mot_phan"))

    def test_groups_cover_gold_and_only_add_identical_twins(self):
        def norm(text):
            return re.sub(r"\s+|\[\d+\]", "", text)

        for case in self.cases:
            with self.subTest(id=case["id"]):
                groups = case["relevant_unit_groups"]
                self.assertEqual([g[0] for g in groups], case["gold_chunk_ids"])
                for gold, *twins in groups:
                    for twin in twins:
                        self.assertEqual(norm(self.corpus[twin]["content"]), norm(self.corpus[gold]["content"]))

    def test_hash_matches_manifest(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        canon = json.dumps(self.cases, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(unicodedata.normalize("NFC", canon).encode("utf-8")).hexdigest()
        self.assertEqual((manifest["split"], manifest["case_count"], manifest["sha256"]),
                         ("test", len(self.cases), digest))


if __name__ == "__main__":
    unittest.main()
