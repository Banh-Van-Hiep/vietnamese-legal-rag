"""VLRA-71/72: Article Store của Team 1 mở được mọi Điều được trích dẫn, giữ nguyên văn và chú thích."""

import json
import re
import time
import unittest
from pathlib import Path

from team2_rag.articles import ARTICLES_PATH, _load_article_cache, get_article

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "data/doanh-nghiep/processed/articles.jsonl"
CHUNKS = ROOT / "data/doanh-nghiep/processed/chunks.jsonl"
MARK = re.compile(r"\s*\[(\d{1,2})\]")
FIELDS = {"document_id", "document_title", "article_id", "article", "content", "source_url"}


class ArticleStoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.articles = [json.loads(line) for line in ARTICLES.read_text(encoding="utf-8").splitlines()]
        cls.chunks = [json.loads(line) for line in CHUNKS.read_text(encoding="utf-8").splitlines()]

    def test_viewer_reads_team1_article_store(self):
        self.assertEqual(ARTICLES_PATH.resolve(), ARTICLES.resolve())
        keys = [(a["document_id"], a["article_id"]) for a in self.articles]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(set(a) == FIELDS for a in self.articles))

    def test_every_cited_chunk_opens_full_article(self):
        """Mỗi chunk (citation) mở đúng Điều; mọi dòng của chunk có trong nguyên văn Điều."""
        for chunk in self.chunks:
            with self.subTest(chunk=chunk["chunk_id"]):
                art = get_article(chunk["document_id"], chunk["article_id"])
                self.assertEqual((art["article"], art["source_url"]), (chunk["article"], chunk["source_url"]))
                self.assertTrue(art["content"].startswith(chunk["article"]))
                plain = MARK.sub("", art["content"])
                for line in filter(str.strip, chunk["content"].split("\n")):
                    self.assertIn(line.strip(), plain)

    def test_amendment_notes_are_kept_with_their_markers(self):
        for art in self.articles:
            body, _, notes = art["content"].partition("\n\n[")
            marks = set(MARK.findall(body))
            with self.subTest(article=(art["document_id"], art["article_id"])):
                if marks:
                    self.assertEqual(set(re.findall(r"^\[(\d+)\] ", "[" + notes, re.M)), marks)

    def test_lookup_latency_p95_within_200ms(self):
        _load_article_cache.cache_clear()
        start = time.perf_counter()
        get_article("luat-59-2020-qh14-v1", "dieu-1")
        cold = time.perf_counter() - start
        samples = []
        for art in self.articles:
            start = time.perf_counter()
            get_article(art["document_id"], art["article_id"])
            samples.append(time.perf_counter() - start)
        samples.sort()
        self.assertLess(samples[int(0.95 * (len(samples) - 1))], 0.2)
        self.assertLess(cold, 5.0)


if __name__ == "__main__":
    unittest.main()
