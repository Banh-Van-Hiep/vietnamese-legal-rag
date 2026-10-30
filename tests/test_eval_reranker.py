"""Offline checks for paired metrics and failure handling; no model downloads."""
import copy
import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from pathlib import Path

from scripts.eval_reranker import evaluate, main, metrics, validate_dataset


def candidate(cid, rank):
    return dict(chunk_id=cid, document_id="doc-v1", article_id="art1", content=cid,
                document_title="Law", article="Điều 1", clause=None, point=None,
                source_url="https://example.com/law", rank=rank, score=1 / rank,
                retrieval_method="hybrid_rrf")


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.pool = dict(question="question", results=[candidate(c, i) for i, c in enumerate("abcdef", 1)])
        self.corpus = {r["chunk_id"]: r for r in self.pool["results"]}
        self.case = dict(id="q1", question="question", expected_status="answered", gold_chunk_ids=["f"])
        self.calls = 0
        outer = self

        class Retriever:
            def retrieve(self, question, top_k):
                outer.calls += 1
                assert top_k == 20
                return outer.pool
        self.retriever = Retriever()

    def run_case(self, scores=None):
        return evaluate(self.retriever, lambda pairs: scores or list(range(6)), [self.case], self.corpus)

    def test_equivalent_subchunks_count_once(self):
        groups = [["a", "b"], ["c"]]
        result = metrics(["a", "b"], groups)
        self.assertEqual(result["recall_at_5"], .5)
        self.assertEqual(result["mrr_at_20"], 1)
        self.assertEqual(metrics(["x"] * 19 + ["a"], groups)["mrr_at_20"], .05)
        self.assertEqual(metrics(["x"] * 20 + ["a"], groups)["mrr_at_20"], 0)
        self.assertTrue(all(v is None for v in metrics(["a"], []).values()))

    def test_same_pool_one_retrieval_and_no_mutation(self):
        original = copy.deepcopy(self.pool)
        result = self.run_case()
        row = result["cases"][0]
        self.assertEqual(self.calls, 1)
        self.assertEqual(self.pool, original)
        self.assertEqual(row["reranked_ids"], list("fedcba"))
        self.assertEqual(row["impact"], "promoted")
        self.assertEqual(row["before"]["recall_at_20"], row["after"]["recall_at_20"])
        self.assertEqual(result["summary"]["delta"]["recall_at_5"], 1)

    def test_demotion_and_mixed_units(self):
        self.case["gold_chunk_ids"] = ["a"]
        self.assertEqual(self.run_case()["cases"][0]["impact"], "demoted")
        self.case["gold_chunk_ids"] = ["a", "f"]
        row = self.run_case()["cases"][0]
        self.assertEqual(row["impact"], "mixed")
        self.assertEqual(row["gained_groups"], [1])
        self.assertEqual(row["lost_groups"], [0])

    def test_ties_keep_retrieval_order(self):
        row = self.run_case([1] * 6)["cases"][0]
        self.assertEqual(row["reranked_ids"], list("abcdef"))
        self.assertEqual(row["impact"], "unchanged")

    def test_missing_candidate_stays_visible(self):
        self.case["gold_chunk_ids"] = ["g"]
        row = self.run_case()["cases"][0]
        self.assertEqual(row["missing_from_pool"], [0])
        self.assertEqual(row["after"]["recall_at_20"], 0)

    def test_failed_rerank_is_not_a_fallback_success(self):
        def broken(pairs):
            raise TimeoutError("test")
        result = evaluate(self.retriever, broken, [self.case], self.corpus)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["summary"]["rerank_errors"], 1)
        self.assertEqual(result["summary"]["failure_rate"], 1)
        self.assertIsNone(result["summary"]["after"]["recall_at_5"])
        self.assertIn("before", result["cases"][0])
        self.assertIn("rerank_failed_ms", result["cases"][0])

    def test_provenance_mismatch_is_retrieval_error(self):
        self.corpus = copy.deepcopy(self.corpus)
        self.corpus["a"]["content"] = "changed"
        result = self.run_case()
        self.assertEqual(result["summary"]["retrieval_errors"], 1)
        self.assertEqual(result["summary"]["paired_answerable"], 0)

    def test_unanswerable_excluded_and_paired_denominator(self):
        cases = [self.case, dict(id="q2", question="question", gold_chunk_ids=[])]
        result = evaluate(self.retriever, lambda pairs: list(range(6)), cases, self.corpus)
        self.assertEqual(result["summary"]["paired_answerable"], 1)
        self.assertEqual(result["summary"]["unanswerable"], 1)
        self.assertEqual(result["summary"]["after"]["recall_at_5"], 1)

    def test_dev_requires_split_and_reviewed_groups(self):
        with self.assertRaises(ValueError):
            validate_dataset([self.case], self.corpus)
        validate_dataset([self.case], self.corpus, exploratory=True)
        self.case.update(split="dev", relevant_unit_groups=[["f"]])
        validate_dataset([self.case], self.corpus)
        self.case["split"] = "test"
        with self.assertRaises(ValueError):
            validate_dataset([self.case], self.corpus, exploratory=True)

    def test_overlapping_or_incomplete_groups_are_rejected(self):
        for groups in ([["f"], ["f"]], [["missing"]], [["a"]], [[]], "f"):
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                validate_dataset([dict(self.case, relevant_unit_groups=groups)], self.corpus, exploratory=True)

    def test_cli_with_fake_runtime_writes_results_and_closes_client(self):
        # Exercise the full CLI without loading models or opening Qdrant.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            golden, chunks, output = [root / name for name in ("dev.json", "chunks.jsonl", "result.json")]
            golden.write_text(json.dumps([dict(self.case, split="dev", relevant_unit_groups=[["f"]])]))
            chunks.write_text("\n".join(json.dumps(r) for r in self.corpus.values()))
            (root / "index_manifest.json").write_text(json.dumps(dict(index_version="test", chunk_ids=list(self.corpus))))
            client = Mock()
            scorer = Mock(side_effect=lambda pairs: list(range(len(pairs))))
            scorer._model = SimpleNamespace(config=SimpleNamespace(_commit_hash="test-revision"))
            scorer._torch = SimpleNamespace(cuda=SimpleNamespace(get_device_name=lambda: "fake-gpu"),
                                             version=SimpleNamespace(cuda="test-cuda"))
            with patch("scripts.eval_reranker.build_retriever", return_value=(self.retriever, client)), \
                    patch("scripts.eval_reranker.BGEScorer", return_value=scorer) as factory:
                code = main(["--golden", str(golden), "--chunks", str(chunks), "--bm25-index", temp,
                             "--dense-index", temp, "--output", str(output), "--device", "cuda",
                             "--embedding-device", "cuda", "--reranker-revision", "test-revision"])
            self.assertEqual(code, 0)
            factory.assert_called_once_with(device="cuda", revision="test-revision")
            client.close.assert_called_once()
            self.assertEqual(self.calls, 2)  # One warm-up, one measured pool.
            report = json.loads(output.read_text())
            self.assertEqual(report["status"], "COMPLETE")
            self.assertEqual(report["reranker_revision"], "test-revision")
            self.assertEqual(report["config"]["embedding_device"], "cuda")
            self.assertEqual(report["accelerator"], dict(name="fake-gpu", cuda_version="test-cuda"))
            self.assertEqual(report["summary"]["promoted"]["count"], 1)
            self.assertIn("recall_at_5", output.with_suffix(".md").read_text())

    def test_blocked_cli_writes_both_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "result.json"
            code = main(["--golden", str(Path(temp) / "missing.json"), "--bm25-index", temp,
                         "--dense-index", temp, "--output", str(output)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.read_text())["status"], "BLOCKED")
            self.assertEqual(json.loads(output.read_text())["config"]["device"], "cpu")
            self.assertIn("Chưa chạy được", output.with_suffix(".md").read_text())


if __name__ == "__main__":
    unittest.main()
