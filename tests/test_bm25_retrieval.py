import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from retriever_contract import RetrieverContractTests

HAS_DEPS = all(importlib.util.find_spec(m) for m in ("bm25s", "underthesea"))

if HAS_DEPS:
    from team1_data.retrieval import BM25Retriever, RetrievalUnavailableError, tokenize_vi


def chunk(cid, article, header, content, status="con_hieu_luc", clause=None):
    doc = cid.split("__")[0]
    return {
        "chunk_id": cid, "document_id": doc, "article_id": cid.split("__")[1],
        "content": content, "document_title": "Luật Doanh nghiệp", "article": article,
        "clause": clause, "point": None, "source_url": "https://vbpl.vn/example",
        "context_header": header, "legal_status": status,
    }


CHUNKS = [
    chunk("luat-59-2020-qh14-v1__dieu-17__k2__0", "Điều 17",
          "Luật Doanh nghiệp 59/2020/QH14 > Điều 17. Quyền thành lập doanh nghiệp",
          "Tổ chức, cá nhân sau đây không có quyền thành lập và quản lý doanh nghiệp.", clause="Khoản 2"),
    chunk("luat-59-2020-qh14-v1__dieu-69__k0__0", "Điều 69",
          "Luật Doanh nghiệp 59/2020/QH14 > Điều 69. Điều kiện để chia lợi nhuận",
          "Công ty chỉ được chia lợi nhuận cho các thành viên sau khi đã hoàn thành nghĩa vụ thuế."),
    chunk("nd-168-2025-nd-cp-v1__dieu-60__k1__0", "Điều 60",
          "Nghị định 168/2025/NĐ-CP > Điều 60. Đăng ký tạm ngừng kinh doanh",
          "Doanh nghiệp gửi thông báo tạm ngừng kinh doanh chậm nhất 03 ngày làm việc trước ngày tạm ngừng.",
          clause="Khoản 1"),
    chunk("luat-59-2020-qh14-v1__dieu-207__k0__0", "Điều 207",
          "Luật Doanh nghiệp 59/2020/QH14 > Điều 207. Các trường hợp và điều kiện giải thể doanh nghiệp",
          "Doanh nghiệp bị giải thể khi kết thúc thời hạn hoạt động đã ghi trong Điều lệ công ty."),
    chunk("luat-68-2014-qh13-v1__dieu-1__k0__0", "Điều 1",
          "Luật Doanh nghiệp 68/2014/QH13 > Điều 1. Phạm vi điều chỉnh",
          "Văn bản đã hết hiệu lực, có cụm tạm ngừng kinh doanh để kiểm tra bộ lọc.", status="het_hieu_luc"),
]


@unittest.skipUnless(HAS_DEPS, "requires bm25s and underthesea")
class TokenizerTest(unittest.TestCase):
    def test_normalises_tone_placement_only_at_syllable_end(self):
        for raw, expected in [("hoà", "hòa"), ("thuỷ", "thủy"), ("uỷ", "ủy")]:
            self.assertEqual(tokenize_vi(raw), [expected])
        for kept in ["hoàng", "khoảng", "toán", "quý", "quỷ", "huỳnh"]:
            self.assertEqual(tokenize_vi(kept), [kept])

    def test_keeps_legal_references_as_single_tokens(self):
        tokens = tokenize_vi("Điều 69, khoản 1, điểm đ, Chương VII của Luật 59/2020/QH14 và Nghị định 168/2025/NĐ-CP")
        for t in ["điều_69", "khoản_1", "điểm_đ", "chương_vii", "59/2020/qh14", "168/2025/nđ-cp"]:
            self.assertIn(t, tokens)

    def test_does_not_treat_common_words_as_references(self):
        tokens = tokenize_vi("điều kiện và điều lệ")
        self.assertIn("điều_kiện", tokens)
        self.assertIn("điều_lệ", tokens)
        self.assertFalse(any(t in ("điều_k", "điều_l") for t in tokens))

    def test_segments_words_and_drops_punctuation(self):
        self.assertEqual(tokenize_vi("Doanh nghiệp, kinh doanh!"), ["doanh_nghiệp", "kinh_doanh"])


@unittest.skipUnless(HAS_DEPS, "requires bm25s and underthesea")
class BM25RetrieverTest(RetrieverContractTests, unittest.TestCase):
    method = "bm25"

    @classmethod
    def setUpClass(cls):
        cls.retriever = BM25Retriever(CHUNKS)

    def ids(self, output):
        return [r["chunk_id"] for r in output["results"]]

    def test_index_skips_chunks_outside_default_legal_status(self):
        self.assertEqual(len(self.retriever.chunks), 4)
        self.assertNotIn("luat-68-2014-qh13-v1__dieu-1__k0__0", self.retriever.chunk_ids)

    def test_basic_query_ranks_matching_chunk_first(self):
        output = self.retriever.retrieve("Tạm ngừng kinh doanh phải thông báo trước mấy ngày?", top_k=3)
        self.assertEqual(self.ids(output)[0], "nd-168-2025-nd-cp-v1__dieu-60__k1__0")

    def test_article_reference_query(self):
        output = self.retriever.retrieve("Điều 69 Luật Doanh nghiệp quy định gì?", top_k=3)
        self.assertEqual(self.ids(output)[0], "luat-59-2020-qh14-v1__dieu-69__k0__0")

    def test_result_has_chunk_id_content_and_score(self):
        row = self.retriever.retrieve("chia lợi nhuận", top_k=1)["results"][0]
        self.assertEqual(row["chunk_id"], "luat-59-2020-qh14-v1__dieu-69__k0__0")
        self.assertIn("chia lợi nhuận", row["content"])
        self.assertIsInstance(row["score"], float)
        self.assertGreater(row["score"], 0)
        self.assertEqual(row["retrieval_method"], "bm25")
    def test_no_matching_word_returns_empty_results(self):
        self.assertEqual(self.retriever.retrieve("xyz qwerty", top_k=5),
                         {"question": "xyz qwerty", "results": []})
    def test_rejects_empty_or_duplicate_corpus(self):
        with self.assertRaises(ValueError):
            BM25Retriever([CHUNKS[4]])
        with self.assertRaises(ValueError):
            BM25Retriever([CHUNKS[0], CHUNKS[0]])


@unittest.skipUnless(HAS_DEPS, "requires bm25s and underthesea")
class BM25PersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.chunks_path = self.dir / "chunks.jsonl"
        self.chunks_path.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in CHUNKS), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_and_load_give_same_results(self):
        built = BM25Retriever.from_jsonl(self.chunks_path)
        index_dir = built.save(self.dir / "index" / "test-01")
        manifest = json.loads((index_dir / "index_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["index_version"], "test-01")
        self.assertEqual(manifest["chunk_count"], 4)
        loaded = BM25Retriever.load(index_dir, self.chunks_path)
        question = "tạm ngừng kinh doanh"
        self.assertEqual(loaded.retrieve(question, 5), built.retrieve(question, 5))

    def test_load_rejects_chunk_store_that_does_not_match(self):
        index_dir = BM25Retriever(CHUNKS).save(self.dir / "index" / "test-02")
        self.chunks_path.write_text(json.dumps(CHUNKS[0], ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(RetrievalUnavailableError):
            BM25Retriever.load(index_dir, self.chunks_path)

    def test_load_missing_index_raises(self):
        with self.assertRaises(RetrievalUnavailableError):
            BM25Retriever.load(self.dir / "missing", self.chunks_path)


if __name__ == "__main__":
    unittest.main()
