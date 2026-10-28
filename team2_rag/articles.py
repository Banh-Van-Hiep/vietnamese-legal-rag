"""Article Store reader and lookup for Document Viewer (contracts/v0.1/internal_article.schema.json)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_ID = re.compile(r"^[A-Za-z0-9_-]+$")

ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = ROOT / "data" / "doanh-nghiep" / "processed" / "chunks.jsonl"
ARTICLES_PATH = ROOT / "data" / "doanh-nghiep" / "processed" / "articles.jsonl"

MOCK_ARTICLE = {
    "document_id": "mock_v1",
    "document_title": "Văn bản kiểm thử",
    "article_id": "art1",
    "article": "Điều 1",
    "content": "Nội dung đầy đủ của điều luật dùng để kiểm thử.",
    "source_url": "https://example.com/mock-law",
}


class ArticleLookupError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 404):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@lru_cache(maxsize=1)
def _load_article_cache() -> dict[str, dict[str, dict[str, Any]]]:
    """Cache structure: {document_id: {article_id: article_dict}}."""
    cache: dict[str, dict[str, dict[str, Any]]] = {}

    # 1. If articles.jsonl exists, use it first
    if ARTICLES_PATH.is_file():
        with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                doc_id = item.get("document_id")
                art_id = item.get("article_id")
                if doc_id and art_id:
                    cache.setdefault(doc_id, {})[art_id] = {
                        "document_id": doc_id,
                        "document_title": item.get("document_title", ""),
                        "article_id": art_id,
                        "article": item.get("article", ""),
                        "content": item.get("content", ""),
                        "source_url": item.get("source_url", ""),
                    }
        return cache

    # 2. Fallback: Reconstruct articles by aggregating chunks from chunks.jsonl
    if CHUNKS_PATH.is_file():
        grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                doc_id = item.get("document_id")
                art_id = item.get("article_id")
                if doc_id and art_id:
                    grouped.setdefault(doc_id, {}).setdefault(art_id, []).append(item)

        for doc_id, articles in grouped.items():
            cache[doc_id] = {}
            for art_id, chunk_list in articles.items():
                first = chunk_list[0]
                chunk_list.sort(key=lambda c: (c.get("chunk_index", 0), c.get("chunk_id", "")))
                full_content = "\n".join(c.get("content", "") for c in chunk_list if c.get("content"))
                cache[doc_id][art_id] = {
                    "document_id": doc_id,
                    "document_title": first.get("document_title", ""),
                    "article_id": art_id,
                    "article": first.get("article", ""),
                    "content": full_content,
                    "source_url": first.get("source_url", ""),
                }
    return cache


def get_article(document_id: str, article_id: str) -> dict[str, Any]:
    """Retrieve full text of an article for the document viewer."""
    if not isinstance(document_id, str) or not _ID.fullmatch(document_id) or len(document_id) > 200:
        raise ArticleLookupError("INVALID_REQUEST", "Định danh document_id không hợp lệ.", status_code=400)
    if not isinstance(article_id, str) or not _ID.fullmatch(article_id) or len(article_id) > 100:
        raise ArticleLookupError("INVALID_REQUEST", "Định danh article_id không hợp lệ.", status_code=400)

    if document_id == MOCK_ARTICLE["document_id"] and article_id == MOCK_ARTICLE["article_id"]:
        return dict(MOCK_ARTICLE)

    cache = _load_article_cache()
    if document_id not in cache:
        raise ArticleLookupError("DOCUMENT_NOT_FOUND", f"Không tìm thấy văn bản: {document_id}", status_code=404)
    if article_id not in cache[document_id]:
        raise ArticleLookupError("ARTICLE_NOT_FOUND", f"Không tìm thấy điều luật: {article_id} trong văn bản: {document_id}", status_code=404)

    return dict(cache[document_id][article_id])
