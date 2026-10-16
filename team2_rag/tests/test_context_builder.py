import json, unittest
from team2_rag.prompts import ContextBuildError, build_context
from team2_rag.tests.helpers import REPO_ROOT

CHUNKS = REPO_ROOT / "data" / "doanh-nghiep" / "processed" / "chunks.jsonl"


def candidate(cid="c1", content="Nội dung điều luật 1.", **kw):
    d = {"chunk_id": cid, "document_id": "bll2019_v1", "article_id": "dieu113", "content": content,
         "document_title": "Bộ luật Lao động 2019", "article": "Điều 113", "clause": "Khoản 1", "point": None,
         "source_url": "https://example.com/law", "score": 0.03, "rank": 1, "retrieval_method": "hybrid_rrf"}
    d.update(kw)
    return d


class ContextBuilderTests(unittest.TestCase):
    def test_valid_chunks_keep_content_and_chunk_id_together(self):
        ctx = build_context([candidate("a", "Nội dung A"), candidate("b", "Nội dung B", clause=None)])
        self.assertEqual([c.label for c in ctx.chunks], ["C1", "C2"])
        b1, b2 = ctx.text.split("\n\n")
        self.assertTrue(b1.startswith("[C1] chunk_id=a document_id=bll2019_v1 article_id=dieu113 "))
        self.assertTrue(b1.endswith("source_url=https://example.com/law\nNội dung A"))
        self.assertIn("clause=Khoản 1 point=null", b1)
        self.assertTrue(b2.startswith("[C2] chunk_id=b ") and b2.endswith("\nNội dung B"))
        self.assertIn("clause=null", b2)

    def test_empty_results(self):
        ctx = build_context([])
        self.assertTrue(ctx.is_empty); self.assertEqual(ctx.text, "")

    def test_content_and_metadata_are_verbatim(self):
        text = "  Dòng 1\n   Dòng 2   có khoảng trắng  "
        c = build_context([candidate(content=text)]).chunks[0]
        self.assertEqual(c.content, text)
        self.assertIn(text, build_context([candidate(content=text)]).text)

    def test_extra_reranker_keys_are_ignored(self):
        self.assertEqual(len(build_context([candidate(rerank_score=0.9)]).chunks), 1)

    def test_contract_violations_raise_and_are_not_repaired(self):
        bad_cases = [
            candidate(chunk_id=None), candidate(content=""), candidate(content=None), candidate(article=""),
            candidate(document_id="có dấu cách"), candidate(article_id="Điều 113"),
            candidate(source_url="example-source"), candidate(source_url="http://example.com/x"),
            candidate(document_title="a\nb"), candidate(clause=""), candidate(score=float("nan")),
            candidate(rank=0), candidate(retrieval_method="rerank"), "not-a-dict",
        ]
        for bad in bad_cases:
            with self.assertRaises(ContextBuildError, msg=repr(bad)[:80]): build_context([bad])
        for missing in ("document_id", "article_id", "document_title", "clause", "point", "source_url", "score", "rank", "retrieval_method"):
            d = candidate(); del d[missing]
            with self.assertRaises(ContextBuildError, msg=missing): build_context([d])
        with self.assertRaises(ContextBuildError): build_context("abc")

    def test_legacy_draft_schema_is_not_accepted(self):
        legacy = {"chunk_id": "c", "content": "x", "document": "Doc", "article": "Điều 1", "clause": None,
                  "source": "example-source", "retrieval_score": 0.7, "rerank_score": 0.9}
        with self.assertRaises(ContextBuildError): build_context([legacy])

    def test_duplicates_skipped_and_max_chunks(self):
        ctx = build_context([candidate("a"), candidate("a"), candidate("b"), candidate("c")], max_chunks=2)
        self.assertEqual([(c.label, c.chunk_id) for c in ctx.chunks], [("C1", "a"), ("C2", "b")])
        self.assertEqual(ctx.skipped_chunk_ids, ("c",))

    def test_budget_skips_oversized_chunk_and_continues(self):
        small = len(build_context([candidate("a")]).text)
        cands = [candidate("a"), candidate("big", "x" * 500), candidate("c")]
        ctx = build_context(cands, max_chars=small * 2 + 10)
        self.assertEqual([c.chunk_id for c in ctx.chunks], ["a", "c"])
        self.assertEqual([c.label for c in ctx.chunks], ["C1", "C2"])
        self.assertEqual(ctx.skipped_chunk_ids, ("big",))
        self.assertTrue(build_context([candidate("a")], max_chars=10).is_empty)
        self.assertEqual(len(build_context([candidate("a"), candidate("b")], max_chars=None).chunks), 2)

    def test_real_team1_corpus_rows_are_accepted(self):
        if not CHUNKS.is_file(): self.skipTest("chunks.jsonl không có")
        rows = []
        with CHUNKS.open(encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 200: break
                r = json.loads(line)
                rows.append({k: r[k] for k in ("chunk_id", "document_id", "article_id", "content", "document_title", "article", "clause", "point", "source_url")} | {"score": 0.1, "rank": i + 1, "retrieval_method": "bm25"})
        ctx = build_context(rows, max_chars=None, max_chunks=len(rows))
        self.assertEqual(len(ctx.chunks), len(rows))
        for c, r in zip(ctx.chunks, rows):
            self.assertEqual((c.chunk_id, c.content, c.source_url, c.clause), (r["chunk_id"], r["content"], r["source_url"], r["clause"]))

if __name__ == "__main__": unittest.main()
