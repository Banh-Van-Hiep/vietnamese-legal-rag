import importlib.util
import json
import re
import tempfile
import unittest
import uuid
import zlib
from pathlib import Path

from retriever_contract import RetrieverContractTests

HAS_DEPS = all(importlib.util.find_spec(m) for m in ("numpy", "qdrant_client"))

if HAS_DEPS:
    import numpy as np
    from qdrant_client import QdrantClient, models

    from team1_data.retrieval import DenseRetriever, RetrievalUnavailableError

# Cùng bộ chunk mẫu với tests/test_bm25_retrieval.py để hai nhánh so sánh được.
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


class FakeEmbedder:
    """Bag-of-syllables băm vào 64 chiều: đủ để kiểm tra luồng index/truy vấn, không tải model."""

    name, revision, dim = "fake/bag-of-syllables", "test-rev", 64

    def __init__(self):
        self.query_calls = 0

    def _vec(self, text):
        v = np.zeros(self.dim, dtype=np.float32)
        for w in re.findall(r"\w+", text.lower()):
            v[zlib.crc32(w.encode("utf-8")) % self.dim] += 1.0
        v[0] += 0.01  # tránh vector 0 với câu không có chữ nào trong corpus
        return v / np.linalg.norm(v)

    def embed_passages(self, texts):
        return np.stack([self._vec(t) for t in texts])

    def embed_query(self, text):
        self.query_calls += 1
        return self._vec(text)


def build(**kwargs):
    return DenseRetriever(CHUNKS, FakeEmbedder(), client=QdrantClient(":memory:"), **kwargs)


@unittest.skipUnless(HAS_DEPS, "requires numpy and qdrant-client")
class DenseIndexingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = build(index_version="test-01")

    def test_index_skips_chunks_outside_default_legal_status(self):
        self.assertEqual(len(self.retriever.chunks), 4)
        self.assertNotIn("luat-68-2014-qh13-v1__dieu-1__k0__0", self.retriever.chunk_ids)
        self.assertEqual(self.retriever.client.count("legal_chunks_test-01", exact=True).count, 4)

    def test_points_use_uuid5_ids_and_full_chunk_payload(self):
        cid = "luat-59-2020-qh14-v1__dieu-69__k0__0"
        pid = str(uuid.uuid5(uuid.NAMESPACE_URL, cid))
        [point] = self.retriever.client.retrieve("legal_chunks_test-01", [pid], with_payload=True, with_vectors=True)
        self.assertEqual(point.payload, next(c for c in CHUNKS if c["chunk_id"] == cid))
        self.assertAlmostEqual(float(np.linalg.norm(point.vector["dense"])), 1.0, places=5)

    def test_collection_uses_named_cosine_vector_and_alias(self):
        info = self.retriever.client.get_collection("legal_chunks_test-01")
        params = info.config.params.vectors["dense"]
        self.assertEqual((params.size, params.distance), (64, models.Distance.COSINE))
        aliases = {a.alias_name: a.collection_name for a in self.retriever.client.get_aliases().aliases}
        self.assertEqual(aliases["legal_chunks"], "legal_chunks_test-01")

    def test_embeddings_are_l2_normalised(self):
        np.testing.assert_allclose(np.linalg.norm(self.retriever.embeddings, axis=1), 1.0, rtol=1e-5)

    def test_rebuilding_existing_collection_is_refused(self):
        with self.assertRaises(ValueError):
            DenseRetriever(CHUNKS, FakeEmbedder(), client=self.retriever.client, index_version="test-01")

    def test_rejects_empty_or_duplicate_corpus(self):
        with self.assertRaises(ValueError):
            DenseRetriever([CHUNKS[4]], FakeEmbedder())
        with self.assertRaises(ValueError):
            DenseRetriever([CHUNKS[0], CHUNKS[0]], FakeEmbedder())

    def test_rejects_embedder_with_wrong_dimension(self):
        embedder = FakeEmbedder()
        embedder.embed_passages = lambda texts: np.ones((len(texts), 32), dtype=np.float32)
        with self.assertRaises(ValueError):
            DenseRetriever(CHUNKS, embedder)


@unittest.skipUnless(HAS_DEPS, "requires numpy and qdrant-client")
class DenseRetrieverTest(RetrieverContractTests, unittest.TestCase):
    method = "dense"

    @classmethod
    def setUpClass(cls):
        cls.retriever = build()

    def ids(self, output):
        return [r["chunk_id"] for r in output["results"]]

    def test_basic_query_ranks_matching_chunk_first(self):
        output = self.retriever.retrieve("Tạm ngừng kinh doanh phải thông báo trước mấy ngày?", top_k=3)
        self.assertEqual(self.ids(output)[0], "nd-168-2025-nd-cp-v1__dieu-60__k1__0")

    def test_result_has_chunk_id_content_and_cosine_score(self):
        row = self.retriever.retrieve("điều kiện chia lợi nhuận", top_k=1)["results"][0]
        self.assertEqual(row["chunk_id"], "luat-59-2020-qh14-v1__dieu-69__k0__0")
        self.assertIn("chia lợi nhuận", row["content"])
        self.assertIsInstance(row["score"], float)
        self.assertTrue(-1.0 <= row["score"] <= 1.0 + 1e-6)
        self.assertEqual(row["retrieval_method"], "dense")

    def test_top_k_limits_results_and_unrelated_query_still_returns_neighbours(self):
        self.assertEqual(len(self.retriever.retrieve("doanh nghiệp", top_k=2)["results"]), 2)
        self.assertEqual(len(self.retriever.retrieve("xyz qwerty", top_k=50)["results"]), 4)

    def test_query_filter_excludes_chunks_outside_legal_status(self):
        client = QdrantClient(":memory:")
        retriever = DenseRetriever(CHUNKS, FakeEmbedder(), client=client)
        stale = CHUNKS[4]
        client.upsert(retriever.collection, points=[models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, stale["chunk_id"])),
            vector={"dense": retriever.embedder.embed_query(stale["content"]).tolist()}, payload=stale)])
        self.assertNotIn(stale["chunk_id"], self.ids(retriever.retrieve(stale["content"], top_k=50)))

    def test_rejects_invalid_input_before_embedding(self):
        retriever = build(index_version="validation")
        for question, top_k in [("", 5), ("   ", 5), (None, 5), ("a" * 4001, 5),
                                ("chia lợi nhuận", 0), ("chia lợi nhuận", 51),
                                ("chia lợi nhuận", True), ("chia lợi nhuận", 2.0)]:
            with self.subTest(question=str(question)[:10], top_k=top_k), self.assertRaises(ValueError):
                retriever.retrieve(question, top_k=top_k)
        self.assertEqual(retriever.embedder.query_calls, 0)

@unittest.skipUnless(HAS_DEPS, "requires numpy and qdrant-client")
class DensePersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.client = QdrantClient(":memory:")
        self.built = DenseRetriever(CHUNKS, FakeEmbedder(), client=self.client, index_version="test-02")
        self.index_dir = self.built.save(self.dir / "test-02")

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_writes_manifest_and_embedding_cache(self):
        manifest = json.loads((self.index_dir / "index_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["index_version"], "test-02")
        self.assertEqual(manifest["collection"], "legal_chunks_test-02")
        self.assertEqual(manifest["chunk_count"], 4)
        self.assertEqual((manifest["embedding_model"], manifest["embedding_revision"], manifest["embedding_dim"]),
                         ("fake/bag-of-syllables", "test-rev", 64))
        self.assertEqual(np.load(self.index_dir / "embeddings.npy").shape, (4, 64))
        self.assertEqual(json.loads((self.index_dir / "chunk_ids.json").read_text(encoding="utf-8")),
                         self.built.chunk_ids)

    def test_connect_gives_same_results(self):
        connected = DenseRetriever.connect(self.index_dir, FakeEmbedder(), client=self.client)
        question = "tạm ngừng kinh doanh"
        self.assertEqual(connected.retrieve(question, 5), self.built.retrieve(question, 5))

    def test_connect_rejects_different_embedding_model(self):
        embedder = FakeEmbedder()
        embedder.revision = "other-rev"
        with self.assertRaises(RetrievalUnavailableError):
            DenseRetriever.connect(self.index_dir, embedder, client=self.client)

    def test_connect_rejects_collection_that_does_not_match_manifest(self):
        self.client.delete(self.built.collection, points_selector=models.PointIdsList(
            points=[str(uuid.uuid5(uuid.NAMESPACE_URL, self.built.chunk_ids[0]))]))
        with self.assertRaises(RetrievalUnavailableError):
            DenseRetriever.connect(self.index_dir, FakeEmbedder(), client=self.client)

    def test_connect_missing_index_or_collection_raises(self):
        with self.assertRaises(RetrievalUnavailableError):
            DenseRetriever.connect(self.dir / "missing", FakeEmbedder(), client=self.client)
        with self.assertRaises(RetrievalUnavailableError):
            DenseRetriever.connect(self.index_dir, FakeEmbedder(), client=QdrantClient(":memory:"))

    def test_unreachable_qdrant_raises_retrieval_unavailable(self):
        with self.assertRaises(RetrievalUnavailableError):
            DenseRetriever.connect(self.index_dir, FakeEmbedder(),
                                   client=QdrantClient(url="http://127.0.0.1:1", timeout=1, check_compatibility=False))

    def test_collection_dropped_after_connect_raises_on_retrieve(self):
        connected = DenseRetriever.connect(self.index_dir, FakeEmbedder(), client=self.client)
        self.client.delete_collection(self.built.collection)
        with self.assertRaises(RetrievalUnavailableError):
            connected.retrieve("tạm ngừng kinh doanh", 5)


if __name__ == "__main__":
    unittest.main()
