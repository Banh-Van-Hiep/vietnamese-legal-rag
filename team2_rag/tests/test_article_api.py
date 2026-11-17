"""Tests for get_article and Article Store lookup (contracts/v0.1/internal_article.schema.json)."""
import json
import unittest
from pathlib import Path

from team2_rag.articles import ArticleLookupError, get_article, MOCK_ARTICLE

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts" / "v0.1" / "internal_article.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8")) if SCHEMA_PATH.is_file() else None


class ArticleLookupTests(unittest.TestCase):
    def test_mock_article_lookup(self):
        art = get_article("mock_v1", "art1")
        self.assertEqual(art["document_id"], "mock_v1")
        self.assertEqual(art["article_id"], "art1")
        self.assertEqual(
            set(art.keys()),
            {"document_id", "document_title", "article_id", "article", "content", "source_url"},
        )
        if SCHEMA is not None:
            import jsonschema
            jsonschema.validate(art, SCHEMA)

    def test_real_corpus_article_lookup(self):
        art = get_article("luat-59-2020-qh14-v1", "dieu-1")
        self.assertEqual(art["document_id"], "luat-59-2020-qh14-v1")
        self.assertEqual(art["article_id"], "dieu-1")
        self.assertIn("Luật này quy định", art["content"])
        if SCHEMA is not None:
            import jsonschema
            jsonschema.validate(art, SCHEMA)

    def test_document_not_found(self):
        with self.assertRaises(ArticleLookupError) as ctx:
            get_article("doc-khong-ton-tai", "dieu-1")
        self.assertEqual(ctx.exception.code, "DOCUMENT_NOT_FOUND")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_article_not_found(self):
        with self.assertRaises(ArticleLookupError) as ctx:
            get_article("luat-59-2020-qh14-v1", "dieu-9999")
        self.assertEqual(ctx.exception.code, "ARTICLE_NOT_FOUND")
        self.assertEqual(ctx.exception.status_code, 404)

    def test_invalid_id_format(self):
        for bad_id in ("doc with spaces", "doc/slashes", "doc$symbol", "", "x" * 201):
            with self.subTest(bad_id=bad_id), self.assertRaises(ArticleLookupError) as ctx:
                get_article(bad_id, "dieu-1")
            self.assertEqual(ctx.exception.code, "INVALID_REQUEST")
            self.assertEqual(ctx.exception.status_code, 400)

        for bad_art in ("dieu with spaces", "dieu/1", "x" * 101):
            with self.subTest(bad_art=bad_art), self.assertRaises(ArticleLookupError) as ctx:
                get_article("luat-59-2020-qh14-v1", bad_art)
            self.assertEqual(ctx.exception.code, "INVALID_REQUEST")
            self.assertEqual(ctx.exception.status_code, 400)


    def test_store_error_scenarios(self):
        import tempfile
        from unittest.mock import patch
        from starlette.testclient import TestClient
        from team2_rag.api.app import create_app
        from team2_rag.articles import _load_article_cache

        app = create_app(pipeline=object())
        client = TestClient(app)

        # 1. Missing articles.jsonl -> 503 RETRIEVAL_UNAVAILABLE
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = Path(tmp) / "articles.jsonl"
            with patch("team2_rag.articles.ARTICLES_PATH", missing_path):
                _load_article_cache.cache_clear()
                res = client.get("/internal/v1/documents/doc1/articles/art1")
                self.assertEqual(res.status_code, 503)
                data = res.json()["error"]
                self.assertEqual(data["code"], "RETRIEVAL_UNAVAILABLE")
                self.assertTrue(data["retryable"])

        # 2. Corrupt line in articles.jsonl -> 503 RETRIEVAL_UNAVAILABLE
        with tempfile.TemporaryDirectory() as tmp:
            corrupt_path = Path(tmp) / "articles.jsonl"
            corrupt_path.write_text('{"document_id": "d1"}\n{bad json\n', encoding="utf-8")
            with patch("team2_rag.articles.ARTICLES_PATH", corrupt_path):
                _load_article_cache.cache_clear()
                res = client.get("/internal/v1/documents/doc1/articles/art1")
                self.assertEqual(res.status_code, 503)
                data = res.json()["error"]
                self.assertEqual(data["code"], "RETRIEVAL_UNAVAILABLE")
                self.assertTrue(data["retryable"])

        # 3. Empty articles.jsonl -> 503 RETRIEVAL_UNAVAILABLE
        with tempfile.TemporaryDirectory() as tmp:
            empty_path = Path(tmp) / "articles.jsonl"
            empty_path.write_text("", encoding="utf-8")
            with patch("team2_rag.articles.ARTICLES_PATH", empty_path):
                _load_article_cache.cache_clear()
                res = client.get("/internal/v1/documents/doc1/articles/art1")
                self.assertEqual(res.status_code, 503)
                data = res.json()["error"]
                self.assertEqual(data["code"], "RETRIEVAL_UNAVAILABLE")
                self.assertTrue(data["retryable"])

        # Reset cache back to normal
        _load_article_cache.cache_clear()


if __name__ == "__main__":
    unittest.main()
