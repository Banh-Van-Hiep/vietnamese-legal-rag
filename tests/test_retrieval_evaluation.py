"""VLRA-48: pipeline đánh giá Retrieval (team1_data.evaluation) trên corpus/Dev Set thu nhỏ."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

DEPS = ("bm25s", "underthesea", "numpy", "qdrant_client", "jsonschema", "sklearn")
HAS_DEPS = all(importlib.util.find_spec(m) for m in DEPS)
ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data/doanh-nghiep/processed/chunks.jsonl"

if HAS_DEPS:
    from team1_data.evaluation import check_inputs, equivalence, rechunk, run, score, unit_of


def _chunk(cid, content, article="dieu-1", clause="Khoản 1", index=0):
    return {"chunk_id": cid, "article_id": article, "clause": clause, "content": content, "chunk_index": index}


@unittest.skipUnless(HAS_DEPS, "requires " + ", ".join(DEPS))
class MetricTest(unittest.TestCase):
    def test_score_recall_and_mrr(self):
        ids = ["x", "a"] + ["y"] * 8 + ["b"]
        self.assertEqual(score(ids, ["a", "b"]),
                         {"recall_at_5": .5, "recall_at_10": .5, "recall_at_20": 1.0, "mrr_at_20": .5})
        self.assertEqual(score(["x"] * 20 + ["a"], ["a"])["mrr_at_20"], 0.0)
        self.assertIsNone(score(["a"], [])["recall_at_5"])

    def test_unit_and_equivalence_merge_identical_clauses_only(self):
        self.assertEqual(unit_of("doc__dieu-1__k2__3"), "doc__dieu-1__k2")
        eq = equivalence([_chunk("a__dieu-1__k1__0", "Nội dung  A"), _chunk("b__dieu-1__k1__0", "nội dung a"),
                          _chunk("c__dieu-1__k1__0", "Nội dung khác"),
                          _chunk("d__dieu-2__k1__0", "Nội dung A", article="dieu-2")])
        self.assertEqual(eq["a__dieu-1__k1"], eq["b__dieu-1__k1"])
        self.assertNotEqual(eq["a__dieu-1__k1"], eq["c__dieu-1__k1"])
        self.assertNotEqual(eq["a__dieu-1__k1"], eq["d__dieu-2__k1"])

    def test_rechunk_sliding_window(self):
        words = [f"w{i}" for i in range(10)]
        base = [dict(_chunk("d__dieu-1__k1__0", " ".join(words)), chunk_count=1, token_count=10),
                dict(_chunk("d__dieu-1__k2__0", "ngắn"), chunk_count=1, token_count=1)]
        out = rechunk(base, 4, 1)
        parts = [c for c in out if c["chunk_id"].startswith("d__dieu-1__k1")]
        self.assertEqual([c["content"] for c in parts], ["w0 w1 w2 w3", "w3 w4 w5 w6", "w6 w7 w8 w9"])
        self.assertEqual([c["chunk_id"] for c in parts], [f"d__dieu-1__k1__{i}" for i in range(3)])
        self.assertTrue(all(c["chunk_count"] == 3 for c in parts))
        self.assertEqual(out[-1], base[1])
        self.assertEqual(rechunk(base, None, 0), base)
        with self.assertRaises(ValueError):
            rechunk(base, 4, 4)


@unittest.skipUnless(HAS_DEPS, "requires " + ", ".join(DEPS))
class PipelineRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp))
        lines = [json.loads(line) for line in CHUNKS.read_text(encoding="utf-8").splitlines()[:80]]
        self.chunks = self.tmp / "chunks.jsonl"
        self.chunks.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in lines), encoding="utf-8")
        cases = [{"id": f"q{i}", "question": c["article_title"] + " " + c["content"][:60],
                  "expected_status": "answered", "gold_chunk_ids": [c["chunk_id"]]}
                 for i, c in enumerate(lines[::20])]
        self.dev = self.tmp / "dev.json"
        self.dev.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")

    def test_run_writes_config_results_and_log_for_same_dev_set(self):
        configs = [{"name": "bm25", "method": "bm25"},
                   {"name": "dense_hash", "method": "dense", "embedder": {"type": "hash", "dim": 128}},
                   {"name": "hybrid", "method": "hybrid_rrf", "rrf_k": 60, "embedder": {"type": "hash", "dim": 128}},
                   {"name": "bm25_c32", "method": "bm25", "chunking": {"size": 32, "overlap": 8}}]
        run_dir = run(configs, self.tmp / "runs", dev_set=self.dev, chunks_path=self.chunks, run_id="t")
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["configs"], [c["name"] for c in configs])
        self.assertEqual(meta["inputs"]["dev_set"]["cases"], 4)
        self.assertIn("config bm25 done", (run_dir / "run.log").read_text(encoding="utf-8"))
        for cfg in configs:
            result = json.loads((run_dir / f"{cfg['name']}.json").read_text(encoding="utf-8"))
            self.assertEqual(result["config"], cfg)
            self.assertEqual(len(result["cases"]), 4)
            self.assertEqual(set(result["metrics"]), {"recall_at_5", "recall_at_10", "recall_at_20", "mrr_at_20",
                                                      "hit_at_5", "article_recall_at_5"})
            self.assertEqual(result["metrics_by_group"]["all"]["cases"], 4)
            self.assertTrue(all(0 <= v <= 1 for v in result["metrics"].values()))
        self.assertEqual(json.loads((run_dir / "bm25.json").read_text())["metrics"]["recall_at_5"], 1.0)
        self.assertGreater(json.loads((run_dir / "bm25_c32.json").read_text())["counts"]["corpus_chunks"], 80)
        summary = (run_dir / "summary.md").read_text(encoding="utf-8")
        self.assertIn("| hybrid |", summary)
        self.assertIn("| hybrid | all | 4 |", summary)

    def test_hit_and_article_recall_are_looser_than_clause_recall(self):
        cases = json.loads(self.dev.read_text(encoding="utf-8"))
        lines = [json.loads(line) for line in self.chunks.read_text(encoding="utf-8").splitlines()]
        same_article = [c["chunk_id"] for c in lines if c["article_id"] == "dieu-4"][:8]
        cases[0].update(question="Giải thích từ ngữ " + cases[0]["question"], gold_chunk_ids=same_article,
                        review_status="nhom_a")
        self.dev.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
        run_dir = run([{"name": "bm25", "method": "bm25"}], self.tmp / "runs", dev_set=self.dev,
                      chunks_path=self.chunks, run_id="g")
        result = json.loads((run_dir / "bm25.json").read_text(encoding="utf-8"))
        row = next(r for r in result["cases"] if r["id"] == cases[0]["id"])
        self.assertLessEqual(row["recall_at_5"], 5 / 8)
        self.assertGreaterEqual(row["article_recall_at_5"], row["recall_at_5"])
        self.assertGreaterEqual(row["hit_at_5"], row["recall_at_5"])
        self.assertEqual(set(result["metrics_by_group"]), {"nhom_a", "all"})

    def test_check_inputs_rejects_unknown_gold(self):
        cases = json.loads(self.dev.read_text(encoding="utf-8"))
        cases[0]["gold_chunk_ids"] = ["khong-ton-tai__dieu-1__k0__0"]
        self.dev.write_text(json.dumps(cases), encoding="utf-8")
        with self.assertRaises(ValueError):
            check_inputs(self.dev, self.chunks)
        with self.assertRaises(ValueError):
            run([{"name": "bm25", "method": "bm25"}], self.tmp / "runs", dev_set=self.dev, chunks_path=self.chunks)


if __name__ == "__main__":
    unittest.main()
