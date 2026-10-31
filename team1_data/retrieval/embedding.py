"""Tạo embedding cho câu hỏi và chunk, theo docs/team1_data/dense-retrieval-proposal.md mục 2–3.

DenseRetriever chỉ cần một đối tượng có `name`, `revision`, `dim`,
`embed_passages(texts)` và `embed_query(text)`; test tiêm embedder giả, không tải model thật.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from typing import Protocol

import numpy as np

DEFAULT_MODEL = "AITeamVN/Vietnamese_Embedding"


class Embedder(Protocol):
    name: str
    revision: str | None
    dim: int

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray: ...


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """Chuẩn hóa L2 theo hàng để cosine = dot product; vector 0 thì raise."""
    vectors = np.asarray(vectors, dtype=np.float64)
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    if not np.all(np.isfinite(vectors)) or np.any(norms == 0):
        raise ValueError("embedding contains a zero or non-finite vector")
    # Tính trên float64 để vector float32 rất lớn không tràn norm thành inf rồi thành vector 0.
    return (vectors / norms).astype(np.float32)


class SentenceTransformerEmbedder:
    """Model sentence-transformers, nạp một lần và dùng lại cho mọi truy vấn.

    Không chữ thường, không tách từ (mục 3). Tiền tố là cấu hình của từng model:
    rỗng với model mặc định, "query: " / "passage: " với họ E5.
    """

    def __init__(
        self,
        name: str = DEFAULT_MODEL,
        *,
        revision: str | None = None,
        query_prefix: str = "",
        passage_prefix: str = "",
        batch_size: int = 32,
        device: str | None = None,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self.name, self.revision = name, revision
        self.query_prefix, self.passage_prefix = query_prefix, passage_prefix
        self.batch_size = batch_size
        self._model = SentenceTransformer(name, revision=revision, device=device)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        vectors = self._model.encode(
            list(texts), batch_size=self.batch_size, normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=False,
        )
        return l2_normalize(vectors)

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray:
        return self._encode([self.passage_prefix + t for t in texts])

    def embed_query(self, text: str) -> np.ndarray:
        text = unicodedata.normalize("NFC", text.strip())
        return self._encode([self.query_prefix + text])[0]
