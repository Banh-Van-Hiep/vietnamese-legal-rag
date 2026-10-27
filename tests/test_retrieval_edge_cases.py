"""Additional QA regressions. Confirmed production defects remain visible failures."""

import importlib.util
import json
import tempfile
import types
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

HAS_DENSE = all(importlib.util.find_spec(m) for m in ("numpy", "qdrant_client"))
HAS_BM25 = all(importlib.util.find_spec(m) for m in ("bm25s", "underthesea"))
if HAS_DENSE:
    import numpy as np
    from qdrant_client import QdrantClient, models
    from team1_data.retrieval.dense import DenseRetriever
    from team1_data.retrieval.embedding import SentenceTransformerEmbedder, l2_normalize
    from team1_data.retrieval.errors import RetrievalUnavailableError
    from test_dense_retrieval import CHUNKS, FakeEmbedder


@unittest.skipUnless(HAS_DENSE, "requires numpy and qdrant-client")
class EmbeddingEdgeTests(unittest.TestCase):
    def test_zero_and_nonfinite_vectors_rejected(self):
        for vector in ([0, 0], [float("nan"), 1], [float("inf"), 1], [float("-inf"), 1]):
            with self.subTest(vector=vector), self.assertRaises(ValueError):
                l2_normalize(vector)

    def test_normal_vectors_have_unit_length(self):
        np.testing.assert_allclose(l2_normalize([[3, 4], [-5, 12]]), [[.6, .8], [-5/13, 12/13]], rtol=1e-6)

    def test_large_finite_vectors_never_silently_become_zero(self):
        # Either reject an unsafe norm or produce a unit vector; a zero vector is invalid.
        with np.errstate(over="ignore"):
            try:
                normalized = l2_normalize([3e38, 3e38])
            except ValueError:
                return
        self.assertAlmostEqual(float(np.linalg.norm(normalized)), 1.0, places=5)

    def test_adapter_nfc_trim_case_and_prefix_without_loading_model(self):
        encoded = []
        class Model:
            def __init__(self, *args, **kwargs):
                pass
            def get_sentence_embedding_dimension(self):
                return 2
            def encode(self, texts, **kwargs):
                encoded.append(texts)
                return np.array([[3., 4.]] * len(texts))
        module = types.ModuleType("sentence_transformers")
        module.SentenceTransformer = Model
        with patch.dict("sys.modules", sentence_transformers=module):
            embedder = SentenceTransformerEmbedder("test/model", revision="test-rev", query_prefix="query: ", passage_prefix="passage: ")
            embedder.embed_query("  Điều 17  ")
            embedder.embed_passages(["Điều 17"])
        self.assertEqual(encoded, [["query: Điều 17"], ["passage: Điều 17"]])


@unittest.skipUnless(HAS_DENSE, "requires numpy and qdrant-client")
class DenseIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.client = QdrantClient(":memory:")
        self.addCleanup(self.client.close)
        self.built = DenseRetriever(CHUNKS, FakeEmbedder(), client=self.client, index_version="qa-edge")
        self.index = self.built.save(Path(self.tmp.name) / "qa-edge")

    def test_manifest_id_hash_mismatch_rejected(self):
        path = self.index / "index_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["chunk_ids_sha256"] = "bad-hash"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(RetrievalUnavailableError):
            DenseRetriever.connect(self.index, FakeEmbedder(), client=self.client)

    def test_query_dimension_mismatch_is_not_empty_success(self):
        self.built.embedder.embed_query = lambda text: np.ones(3)
        with self.assertRaises((ValueError, RetrievalUnavailableError)):
            self.built.retrieve("doanh nghiệp")

    def test_connect_rejects_changed_query_prefix(self):
        manifest_path = self.index / "index_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["query_prefix"] = "query: "
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        embedder = FakeEmbedder()
        embedder.query_prefix = "different: "
        with self.assertRaises(RetrievalUnavailableError):
            DenseRetriever.connect(self.index, embedder, client=self.client)

    def test_connect_rejects_duplicate_physical_point_for_same_chunk(self):
        chunk = self.built.chunks[0]
        self.client.upsert(self.built.collection, points=[models.PointStruct(
            id=str(uuid.uuid4()), vector={"dense": self.built.embeddings[0].tolist()}, payload=chunk)])
        with self.assertRaises(RetrievalUnavailableError):
            DenseRetriever.connect(self.index, FakeEmbedder(), client=self.client)


@unittest.skipUnless(HAS_BM25, "requires bm25s and underthesea")
class BM25EdgeTests(unittest.TestCase):
    def test_nfc_and_nfd_queries_retrieve_same_ids(self):
        import unicodedata
        from team1_data.retrieval.bm25 import BM25Retriever
        from test_bm25_retrieval import CHUNKS as BM25_CHUNKS
        retriever = BM25Retriever(BM25_CHUNKS)
        question = "Điều 17 thành lập doanh nghiệp"
        get_ids = lambda q: [r["chunk_id"] for r in retriever.retrieve(q)["results"]]
        self.assertEqual(get_ids(question), get_ids(unicodedata.normalize("NFD", question)))
