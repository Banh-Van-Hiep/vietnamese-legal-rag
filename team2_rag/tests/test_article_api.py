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


if __name__ == "__main__":
    unittest.main()
