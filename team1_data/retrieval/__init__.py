"""Retrieval của Team 1: nhánh BM25 và Dense; Hybrid sẽ thêm sau.

Import lười để chỉ cần cài phụ thuộc của nhánh đang dùng (bm25s/underthesea hoặc qdrant-client).
"""

from importlib import import_module

from .errors import RetrievalUnavailableError

_LAZY = {
    "BM25Retriever": ".bm25",
    "tokenize_vi": ".tokenizer",
    "DenseRetriever": ".dense",
    "SentenceTransformerEmbedder": ".embedding",
}

__all__ = ["BM25Retriever", "DenseRetriever", "RetrievalUnavailableError",
           "SentenceTransformerEmbedder", "tokenize_vi"]


def __getattr__(name):
    if name in _LAZY:
        return getattr(import_module(_LAZY[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
