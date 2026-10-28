"""Tương thích với dữ liệu Team 1 thật (data/doanh-nghiep/processed/chunks.jsonl) và golden của Team 2.

Đây KHÔNG phải integration test với Reranker/retrieve() (chưa tồn tại). Candidate được dựng trực tiếp từ chunk thật
theo contract retrieval_output v0.1; LLM là FakeLLMProvider sao chép metadata đúng như prompt yêu cầu.
"""
import json, unittest
from team2_rag.answer import answer_from_rerank, cited_chunk_ids
from team2_rag.llm.errors import CitationInvalidError
from team2_rag.llm.fake import FakeLLMProvider
from team2_rag.llm.service import LLMService
from team2_rag.prompts import build_context
from team2_rag.tests.helpers import REPO_ROOT

CHUNKS = REPO_ROOT / "data" / "doanh-nghiep" / "processed" / "chunks.jsonl"
GOLDEN = REPO_ROOT / "team2_rag" / "data" / "golden" / "golden_phase1_30cai.json"
FIELDS = ("chunk_id", "document_id", "article_id", "content", "document_title", "article", "clause", "point", "source_url")

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None


def to_candidate(row, rank):
    return {k: row[k] for k in FIELDS} | {"score": 0.1, "rank": rank, "retrieval_method": "hybrid_rrf"}


def citation_of(row, label):
    return {"citation_id": label} | {k: row[k] for k in FIELDS if k != "content"}


@unittest.skipUnless(CHUNKS.is_file() and GOLDEN.is_file(), "thiếu corpus hoặc golden")
class RealCorpusCompatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with CHUNKS.open(encoding="utf-8") as f:
            cls.rows = [json.loads(line) for line in f if line.strip()]
        cls.by_id = {r["chunk_id"]: r for r in cls.rows}
        cls.golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        cls.schema = json.loads((REPO_ROOT / "contracts" / "v0.1" / "rag_response.schema.json").read_text(encoding="utf-8"))

    def test_every_corpus_chunk_satisfies_context_contract(self):
        for i, r in enumerate(self.rows):
            ctx = build_context([to_candidate(r, i + 1)], max_chars=None)
            self.assertEqual((ctx.chunks[0].chunk_id, ctx.chunks[0].content), (r["chunk_id"], r["content"]), r["chunk_id"])

    def test_golden_chunk_ids_exist_in_corpus(self):
        for item in self.golden:
            for cid in item["gold_chunk_ids"]:
                self.assertIn(cid, self.by_id, item["id"])

    def test_golden_answered_items_return_gold_chunk_ids_and_valid_schema(self):
        distractors = [r for r in self.rows][:2]
        for item in (g for g in self.golden if g["expected_status"] == "answered" and len(g["gold_chunk_ids"]) <= 5):
            gold = [self.by_id[c] for c in item["gold_chunk_ids"]]
            pool = gold + [d for d in distractors if d["chunk_id"] not in item["gold_chunk_ids"]]
            labels = [f"C{i}" for i in range(1, len(gold) + 1)]
            answer = " ".join(f"Nhận định {i} [{lb}]." for i, lb in enumerate(labels, 1))
            llm = {"status": "answered", "answer": answer, "citations": [citation_of(r, lb) for r, lb in zip(gold, labels)]}
            resp = answer_from_rerank({"question": item["question"], "results": [to_candidate(r, i + 1) for i, r in enumerate(pool)]},
                                      LLMService(FakeLLMProvider([llm])), max_chunks=len(pool), max_context_chars=None)
            self.assertEqual(cited_chunk_ids(resp), item["gold_chunk_ids"], item["id"])
            self.assertEqual(set(resp), {"status", "answer", "citations"})
            if jsonschema: jsonschema.validate(resp, self.schema)

    def test_golden_items_with_more_than_5_gold_chunks_are_capped_at_context_limit(self):
        # Ghi nhận thực tế: golden có mẫu 6-11 chunk nguồn nhưng context tối đa 5 chunk (context-builder.md);
        # pipeline chỉ đưa 5 chunk đầu vào prompt nên không thể trích dẫn quá 5. Cần Team 1/2 thống nhất.
        big = [g for g in self.golden if len(g["gold_chunk_ids"]) > 5]
        self.assertTrue(big, "golden hiện không còn mẫu > 5 chunk; có thể bỏ test này")
        item = big[0]
        gold = [self.by_id[c] for c in item["gold_chunk_ids"]]
        ctx = build_context([to_candidate(r, i + 1) for i, r in enumerate(gold)], max_chars=None)
        self.assertEqual(len(ctx.chunks), 5)
        self.assertEqual(set(ctx.skipped_chunk_ids), set(item["gold_chunk_ids"][5:]))

    def test_citing_a_corpus_chunk_that_was_not_in_input_is_rejected(self):
        item = next(g for g in self.golden if g["expected_status"] == "answered")
        gold = self.by_id[item["gold_chunk_ids"][0]]
        outsider = next(r for r in self.rows if r["chunk_id"] != gold["chunk_id"])  # chunk thật nhưng KHÔNG có trong input
        llm = {"status": "answered", "answer": "A [C1].", "citations": [citation_of(outsider, "C1")]}
        with self.assertRaises(CitationInvalidError):
            answer_from_rerank({"question": item["question"], "results": [to_candidate(gold, 1)]}, LLMService(FakeLLMProvider([llm])), max_context_chars=None)

if __name__ == "__main__": unittest.main()
