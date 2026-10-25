"""ArticleRepositoryPort adapter: serve complete articles, never reconstruct them from chunks."""
from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .config.settings import read_dotenv
from .errors import ArticleNotFoundError, ArticleStoreUnavailableError, DocumentNotFoundError

_ID = re.compile(r"[A-Za-z0-9_-]+")


def validate_article_ids(document_id: str, article_id: str) -> None:
    for value, limit in ((document_id, 200), (article_id, 100)):
        if not isinstance(value, str) or not 1 <= len(value) <= limit or not _ID.fullmatch(value):
            raise ValueError("Invalid document_id or article_id")


class ArticleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    document_id: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9_-]+$")
    document_title: str = Field(min_length=1, max_length=500)
    article_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    article: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=200000)
    source_url: str = Field(min_length=1, max_length=2048)

    @field_validator("document_title", "article", "content")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Article fields must not be blank")
        return value

    @field_validator("source_url")
    @classmethod
    def _https(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname or any(c.isspace() for c in value):
            raise ValueError("Article source must be absolute HTTPS")
        return value


class ArticleRepository(Protocol):
    def get_article(self, document_id: str, article_id: str) -> dict: ...


class JsonlArticleStore:
    """Read a Team 1 article snapshot once; missing/corrupt source is 503, not a false 404.

    Each JSONL record contains the six ArticleResponse fields. Extra storage
    metadata may exist but is not exposed on the wire. No chunk store is read.
    A failed load is retryable after Team 1 supplies the snapshot.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._records = None
        self._lock = threading.Lock()

    @classmethod
    def from_environment(cls):
        env = {**read_dotenv(".env"), **os.environ}
        return cls(env.get("RAG_ARTICLES", "data/doanh-nghiep/processed/articles.jsonl"))

    def _load(self):
        if self._records is not None:
            return self._records
        with self._lock:
            if self._records is None:
                records = {}
                try:
                    with self.path.open(encoding="utf-8") as stream:
                        for line in stream:
                            if not line.strip():
                                continue
                            raw = json.loads(line)
                            row = ArticleResponse.model_validate({k: raw[k] for k in ArticleResponse.model_fields})
                            key = (row.document_id, row.article_id)
                            if key in records:
                                raise ValueError("Duplicate article identity")
                            records[key] = row
                    if not records:
                        raise ValueError("Empty article snapshot")
                except (OSError, ValueError, KeyError, TypeError, ValidationError):
                    raise ArticleStoreUnavailableError("Article snapshot is unavailable or invalid") from None
                self._records = records
        return self._records

    def get_article(self, document_id: str, article_id: str) -> dict:
        validate_article_ids(document_id, article_id)
        records = self._load()
        if not any(doc == document_id for doc, _ in records):
            raise DocumentNotFoundError()
        row = records.get((document_id, article_id))
        if row is None:
            raise ArticleNotFoundError()
        return row.model_dump(mode="json")
