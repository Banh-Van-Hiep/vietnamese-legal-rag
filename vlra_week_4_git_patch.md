--- /dev/null
+++ b/requirements-week4.txt
@@ -0,0 +1,5 @@
+pydantic>=2.6
+pydantic-settings>=2.2
+fastapi>=0.110
+httpx>=0.27
+pytest>=8.0
--- /dev/null
+++ b/.env.example
@@ -0,0 +1,16 @@
+LLM_PROVIDER=openai
+LLM_MODEL=gpt-4o
+OPENAI_API_KEY=
+GEMINI_API_KEY=
+QWEN_API_KEY=
+QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
+LLM_TIMEOUT_SECONDS=30
+LLM_MAX_RETRIES=0
+LLM_TEMPERATURE=0.0
+LLM_MAX_OUTPUT_TOKENS=1500
+LLM_CONTEXT_WINDOW_TOKENS=128000
+LLM_MAX_CONTEXT_TOKENS=3000
+LLM_SAFETY_MARGIN_TOKENS=256
+LLM_MAX_CONTEXT_CHUNKS=5
+LLM_MAX_CONTEXT_CHARS=9000
--- /dev/null
+++ b/team2_rag/config/llm_config.py
@@ -0,0 +1,114 @@
+from __future__ import annotations
+
+from functools import lru_cache
+from typing import Literal, Optional
+
+from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
+from pydantic_settings import BaseSettings, SettingsConfigDict
+
+from team2_rag.config.settings import (
+    DEFAULT_MAX_CONTEXT_CHARS,
+    DEFAULT_MAX_CONTEXT_CHUNKS,
+    DEFAULT_MAX_CONTEXT_TOKENS,
+    DEFAULT_QWEN_BASE_URL,
+    DEFAULT_SAFETY_MARGIN_TOKENS,
+    ConfigError,
+    LLMSettings,
+)
+
+Provider = Literal["openai", "gemini", "qwen"]
+_KEY_ENV = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "qwen": "QWEN_API_KEY"}
+
+
+class LLMClientSettings(BaseSettings):
+    model_config = SettingsConfigDict(
+        env_file=".env",
+        env_file_encoding="utf-8",
+        extra="ignore",
+        populate_by_name=True,
+        env_ignore_empty=True,
+        frozen=True,
+    )
+
+    provider: Provider = Field("openai", validation_alias="LLM_PROVIDER")
+    model: str = Field("", validation_alias="LLM_MODEL")
+    openai_api_key: SecretStr = Field(SecretStr(""), validation_alias="OPENAI_API_KEY")
+    gemini_api_key: SecretStr = Field(SecretStr(""), validation_alias="GEMINI_API_KEY")
+    qwen_api_key: SecretStr = Field(SecretStr(""), validation_alias="QWEN_API_KEY")
+    qwen_base_url: str = Field(DEFAULT_QWEN_BASE_URL, validation_alias="QWEN_BASE_URL")
+
+    timeout_seconds: float = Field(30.0, gt=0, le=30, validation_alias="LLM_TIMEOUT_SECONDS")
+    max_retries: int = Field(0, ge=0, le=0, validation_alias="LLM_MAX_RETRIES")
+    temperature: Optional[float] = Field(0.0, ge=0.0, le=2.0, validation_alias="LLM_TEMPERATURE")
+    max_tokens: int = Field(
+        1500, gt=0, validation_alias=AliasChoices("LLM_MAX_OUTPUT_TOKENS", "LLM_MAX_TOKENS")
+    )
+    context_window_tokens: Optional[int] = Field(
+        None, gt=0, validation_alias="LLM_CONTEXT_WINDOW_TOKENS"
+    )
+    max_context_tokens: int = Field(
+        DEFAULT_MAX_CONTEXT_TOKENS, gt=0, validation_alias="LLM_MAX_CONTEXT_TOKENS"
+    )
+    safety_margin_tokens: int = Field(
+        DEFAULT_SAFETY_MARGIN_TOKENS, gt=0, validation_alias="LLM_SAFETY_MARGIN_TOKENS"
+    )
+    max_context_chunks: int = Field(
+        DEFAULT_MAX_CONTEXT_CHUNKS, ge=1, validation_alias="LLM_MAX_CONTEXT_CHUNKS"
+    )
+    max_context_chars: int = Field(
+        DEFAULT_MAX_CONTEXT_CHARS, ge=1, validation_alias="LLM_MAX_CONTEXT_CHARS"
+    )
+
+    @field_validator("provider", mode="before")
+    @classmethod
+    def _norm_provider(cls, v):
+        return v.strip().lower() if isinstance(v, str) else v
+
+    @field_validator("model", "qwen_base_url", mode="before")
+    @classmethod
+    def _strip(cls, v):
+        return v.strip() if isinstance(v, str) else v
+
+    @model_validator(mode="after")
+    def _window_fits_output(self) -> "LLMClientSettings":
+        if (
+            self.context_window_tokens is not None
+            and self.context_window_tokens <= self.max_tokens + self.safety_margin_tokens
+        ):
+            raise ValueError("LLM_CONTEXT_WINDOW_TOKENS phải lớn hơn max_tokens + safety_margin_tokens.")
+        return self
+
+    def api_key(self, provider: Optional[str] = None) -> str:
+        p = provider or self.provider
+        return {
+            "openai": self.openai_api_key,
+            "gemini": self.gemini_api_key,
+            "qwen": self.qwen_api_key,
+        }[p].get_secret_value()
+
+    def validate_runtime(self) -> "LLMClientSettings":
+        if not self.model:
+            raise ConfigError("LLM_MODEL chưa được cấu hình.")
+        if not self.api_key().strip():
+            raise ConfigError(f"{_KEY_ENV[self.provider]} chưa được cấu hình.")
+        return self
+
+    def to_legacy(self) -> LLMSettings:
+        """Adapter cho llm.factory.create_llm_service / answer.generate_answer."""
+        return LLMSettings(
+            provider=self.provider,
+            model=self.model,
+            openai_api_key=self.openai_api_key.get_secret_value(),
+            gemini_api_key=self.gemini_api_key.get_secret_value(),
+            qwen_api_key=self.qwen_api_key.get_secret_value(),
+            qwen_base_url=self.qwen_base_url,
+            timeout_seconds=self.timeout_seconds,
+            max_retries=self.max_retries,
+            temperature=self.temperature,
+            max_output_tokens=self.max_tokens,
+            max_context_chunks=self.max_context_chunks,
+            max_context_chars=self.max_context_chars,
+            max_context_tokens=self.max_context_tokens,
+            safety_margin_tokens=self.safety_margin_tokens,
+            context_window_tokens=self.context_window_tokens,
+        )
+
+
+@lru_cache(maxsize=1)
+def get_llm_settings() -> LLMClientSettings:
+    return LLMClientSettings()
--- /dev/null
+++ b/team2_rag/models/__init__.py
@@ -0,0 +1,3 @@
+from team2_rag.models.response import Citation, RAGResponse, Status
+
+__all__ = ["Citation", "RAGResponse", "Status"]
--- /dev/null
+++ b/team2_rag/models/response.py
@@ -0,0 +1,81 @@
+from __future__ import annotations
+
+import re
+from typing import Any, Literal, Optional
+from urllib.parse import urlparse
+
+from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
+
+Status = Literal["answered", "insufficient_context"]
+
+_ID = r"^[A-Za-z0-9_-]+$"
+_MARKER = re.compile(r"\[C([1-9][0-9]*)\]")
+
+
+class Citation(BaseModel):
+    model_config = ConfigDict(extra="forbid", frozen=True)
+
+    citation_id: str = Field(pattern=r"^C[1-9][0-9]*$", max_length=20)
+    chunk_id: str = Field(min_length=1, max_length=200)
+    document_id: str = Field(min_length=1, max_length=200, pattern=_ID)
+    article_id: str = Field(min_length=1, max_length=100, pattern=_ID)
+    document_title: str = Field(min_length=1, max_length=500)
+    article: str = Field(min_length=1, max_length=100)
+    clause: Optional[str] = Field(max_length=100)
+    point: Optional[str] = Field(max_length=100)
+    source_url: str = Field(min_length=1, max_length=2048)
+
+    @field_validator("chunk_id", "document_title", "article", "clause", "point")
+    @classmethod
+    def _not_blank(cls, v: Optional[str]) -> Optional[str]:
+        if v is not None and not v.strip():
+            raise ValueError("không được rỗng")
+        return v
+
+    @field_validator("source_url")
+    @classmethod
+    def _https(cls, v: str) -> str:
+        p = urlparse(v)
+        if p.scheme != "https" or not p.netloc:
+            raise ValueError("source_url phải là URL HTTPS tuyệt đối")
+        return v
+
+
+class RAGResponse(BaseModel):
+    model_config = ConfigDict(extra="forbid", frozen=True)
+
+    status: Status
+    answer: str = Field(min_length=1, max_length=12000)
+    citations: list[Citation] = Field(max_length=10)
+
+    @field_validator("answer")
+    @classmethod
+    def _answer_not_blank(cls, v: str) -> str:
+        if not v.strip():
+            raise ValueError("answer không được rỗng")
+        return v
+
+    @model_validator(mode="after")
+    def _check_citations(self) -> "RAGResponse":
+        markers: list[str] = []
+        for m in _MARKER.finditer(self.answer):
+            label = f"C{m.group(1)}"
+            if label not in markers:
+                markers.append(label)
+        ids = [c.citation_id for c in self.citations]
+        if len(set(ids)) != len(ids):
+            raise ValueError("citation_id bị trùng")
+        if self.status == "insufficient_context":
+            if ids or markers:
+                raise ValueError("insufficient_context phải có citations=[] và không có marker")
+            return self
+        if not ids:
+            raise ValueError("answered phải có ít nhất một citation")
+        if markers != ids:
+            raise ValueError("citations phải khớp marker [Ck] theo thứ tự xuất hiện đầu tiên")
+        if ids != [f"C{i}" for i in range(1, len(ids) + 1)]:
+            raise ValueError("citation_id phải liên tục C1..Cn")
+        return self
+
+    def cited_chunk_ids(self) -> list[str]:
+        return [c.chunk_id for c in self.citations]
+
+    def to_payload(self) -> dict[str, Any]:
+        return self.model_dump(mode="json")
--- /dev/null
+++ b/team2_rag/errors.py
@@mo 0,0 +1,78 @@
+from __future__ import annotations
+
+from enum import Enum
+from typing import ClassVar
+
+from pydantic import BaseModel, ConfigDict, ValidationError
+
+from team2_rag.llm.errors import LLMError
+from team2_rag.prompts.context import ContextBudgetError, ContextBuildError
+
+
+class ErrorCode(str, Enum):
+    INVALID_REQUEST = "INVALID_REQUEST"
+    LLM_TIMEOUT = "LLM_TIMEOUT"
+    LLM_UNAVAILABLE = "LLM_UNAVAILABLE"
+    INVALID_LLM_OUTPUT = "INVALID_LLM_OUTPUT"
+    CITATION_INVALID = "CITATION_INVALID"
+    INTERNAL_ERROR = "INTERNAL_ERROR"
+
+
+class ErrorDetail(BaseModel):
+    model_config = ConfigDict(extra="forbid", frozen=True)
+
+    code: ErrorCode
+    message: str
+    retryable: bool
+
+
+class ErrorResponse(BaseModel):
+    model_config = ConfigDict(extra="forbid", frozen=True)
+
+    error: ErrorDetail
+
+
+ERROR_SPECS: dict[ErrorCode, tuple[int, str, bool]] = {
+    ErrorCode.INVALID_REQUEST: (400, "Yêu cầu không hợp lệ.", False),
+    ErrorCode.LLM_TIMEOUT: (504, "Dịch vụ tạm thời không phản hồi.", True),
+    ErrorCode.LLM_UNAVAILABLE: (503, "Dịch vụ xử lý tạm thời không khả dụng.", True),
+    ErrorCode.INVALID_LLM_OUTPUT: (502, "Phản hồi từ dịch vụ xử lý không hợp lệ.", False),
+    ErrorCode.CITATION_INVALID: (502, "Phản hồi từ dịch vụ xử lý không hợp lệ.", False),
+    ErrorCode.INTERNAL_ERROR: (500, "Lỗi hệ thống nội bộ.", False),
+}
+
+
+class Team2Error(Exception):
+    code: ClassVar[ErrorCode] = ErrorCode.INTERNAL_ERROR
+
+    def __init__(self, detail: str = "") -> None:
+        super().__init__(detail)
+        self.detail = detail
+
+
+class InvalidRequestError(Team2Error):
+    code = ErrorCode.INVALID_REQUEST
+
+
+class InternalError(Team2Error):
+    code = ErrorCode.INTERNAL_ERROR
+
+
+def classify(exc: BaseException) -> ErrorCode:
+    if isinstance(exc, Team2Error):
+        return exc.code
+    if isinstance(exc, LLMError):
+        try:
+            return ErrorCode(exc.error_code)
+        except ValueError:
+            return ErrorCode.LLM_UNAVAILABLE
+    if isinstance(exc, (ContextBuildError, ContextBudgetError)):
+        return ErrorCode.INTERNAL_ERROR
+    if isinstance(exc, ValidationError):
+        return ErrorCode.INVALID_LLM_OUTPUT
+    if isinstance(exc, ValueError):
+        return ErrorCode.INVALID_REQUEST
+    return ErrorCode.INTERNAL_ERROR
+
+
+def build_error_response(code: ErrorCode) -> tuple[int, ErrorResponse]:
+    status, message, retryable = ERROR_SPECS[code]
+    return status, ErrorResponse(error=ErrorDetail(code=code, message=message, retryable=retryable))
--- /dev/null
+++ b/team2_rag/api/__init__.py
@@ -0,0 +1,3 @@
+from team2_rag.api.handlers import install_error_handlers
+
+__all__ = ["install_error_handlers"]
--- /dev/null
+++ b/team2_rag/api/handlers.py
@@ -0,0 +1,38 @@
+from __future__ import annotations
+
+import logging
+
+from fastapi import FastAPI, Request
+from fastapi.exceptions import RequestValidationError
+from fastapi.responses import JSONResponse
+from pydantic import ValidationError
+
+from team2_rag.errors import ErrorCode, Team2Error, build_error_response, classify
+from team2_rag.llm.errors import LLMError
+
+logger = logging.getLogger("team2_rag.api")
+
+
+def _respond(code: ErrorCode, exc: BaseException) -> JSONResponse:
+    status, body = build_error_response(code)
+    if status >= 500:
+        logger.error("request_failed code=%s exc=%s", code.value, type(exc).__name__, exc_info=exc)
+    else:
+        logger.warning("request_rejected code=%s exc=%s", code.value, type(exc).__name__)
+    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))
+
+
+async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
+    return _respond(classify(exc), exc)
+
+
+async def handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
+    return _respond(ErrorCode.INVALID_REQUEST, exc)
+
+
+def install_error_handlers(app: FastAPI) -> None:
+    app.add_exception_handler(RequestValidationError, handle_request_validation)
+    app.add_exception_handler(Team2Error, handle_exception)
+    app.add_exception_handler(LLMError, handle_exception)
+    app.add_exception_handler(ValidationError, handle_exception)
+    app.add_exception_handler(ValueError, handle_exception)
+    app.add_exception_handler(Exception, handle_exception)
--- /dev/null
+++ b/team2_rag/data/golden/golden_sample_5qa.json
@@ -0,0 +1,118 @@
+[
+  {
+    "id": "gold_001",
+    "question": "Luật Doanh nghiệp quy định về những vấn đề gì?",
+    "expected_status": "answered",
+    "ground_truth": "Luật Doanh nghiệp quy định về việc thành lập, tổ chức quản lý, tổ chức lại, giải thể và hoạt động có liên quan của doanh nghiệp, bao gồm công ty trách nhiệm hữu hạn, công ty cổ phần, công ty hợp danh, doanh nghiệp tư nhân và nhóm công ty.",
+    "gold_chunk_ids": ["luat-59-2020-qh14-v1__dieu-1__k0__0"],
+    "citation": "Điều 1 - Luật Doanh nghiệp 2020",
+    "category": "Phạm vi điều chỉnh",
+    "author": "Bành Văn Hiệp",
+    "gold_citations": [
+      {
+        "citation_id": "C1",
+        "chunk_id": "luat-59-2020-qh14-v1__dieu-1__k0__0",
+        "document_id": "luat-59-2020-qh14-v1",
+        "article_id": "dieu-1",
+        "document_title": "Luật Doanh nghiệp",
+        "article": "Điều 1",
+        "clause": null,
+        "point": null,
+        "source_url": "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"
+      }
+    ]
+  },
+  {
+    "id": "gold_002",
+    "question": "Những ai thuộc đối tượng áp dụng của Luật Doanh nghiệp?",
+    "expected_status": "answered",
+    "ground_truth": "Đối tượng áp dụng gồm doanh nghiệp và cơ quan, tổ chức, cá nhân có liên quan đến việc thành lập, tổ chức quản lý, tổ chức lại, giải thể và hoạt động có liên quan của doanh nghiệp.",
+    "gold_chunk_ids": [
+      "luat-59-2020-qh14-v1__dieu-2__k1__0",
+      "luat-59-2020-qh14-v1__dieu-2__k2__0"
+    ],
+    "citation": "Điều 2 - Luật Doanh nghiệp 2020",
+    "category": "Đối tượng áp dụng",
+    "author": "Bành Văn Hiệp",
+    "gold_citations": [
+      {
+        "citation_id": "C1",
+        "chunk_id": "luat-59-2020-qh14-v1__dieu-2__k1__0",
+        "document_id": "luat-59-2020-qh14-v1",
+        "article_id": "dieu-2",
+        "document_title": "Luật Doanh nghiệp",
+        "article": "Điều 2",
+        "clause": "Khoản 1",
+        "point": null,
+        "source_url": "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"
+      },
+      {
+        "citation_id": "C2",
+        "chunk_id": "luat-59-2020-qh14-v1__dieu-2__k2__0",
+        "document_id": "luat-59-2020-qh14-v1",
+        "article_id": "dieu-2",
+        "document_title": "Luật Doanh nghiệp",
+        "article": "Điều 2",
+        "clause": "Khoản 2",
+        "point": null,
+        "source_url": "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"
+      }
+    ]
+  },
+  {
+    "id": "gold_003",
+    "question": "Theo Luật Doanh nghiệp, cổ đông là ai?",
+    "expected_status": "answered",
+    "ground_truth": "Cổ đông là cá nhân, tổ chức sở hữu ít nhất một cổ phần của công ty cổ phần.",
+    "gold_chunk_ids": ["luat-59-2020-qh14-v1__dieu-4__k3__0"],
+    "citation": "Khoản 3 Điều 4 - Luật Doanh nghiệp 2020",
+    "category": "Giải thích thuật ngữ",
+    "author": "Bành Văn Hiệp",
+    "gold_citations": [
+      {
+        "citation_id": "C1",
+        "chunk_id": "luat-59-2020-qh14-v1__dieu-4__k3__0",
+        "document_id": "luat-59-2020-qh14-v1",
+        "article_id": "dieu-4",
+        "document_title": "Luật Doanh nghiệp",
+        "article": "Điều 4",
+        "clause": "Khoản 3",
+        "point": null,
+        "source_url": "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"
+      }
+    ]
+  },
+  {
+    "id": "gold_004",
+    "question": "Vốn điều lệ của công ty trách nhiệm hữu hạn được xác định như thế nào?",
+    "expected_status": "answered",
+    "ground_truth": "Vốn điều lệ của công ty trách nhiệm hữu hạn là tổng giá trị tài sản do các thành viên công ty hoặc chủ sở hữu công ty đã góp hoặc cam kết góp khi thành lập công ty.",
+    "gold_chunk_ids": ["luat-59-2020-qh14-v1__dieu-4__k34__0"],
+    "citation": "Khoản 34 Điều 4 - Luật Doanh nghiệp 2020",
+    "category": "Vốn",
+    "author": "Bành Văn Hiệp",
+    "gold_citations": [
+      {
+        "citation_id": "C1",
+        "chunk_id": "luat-59-2020-qh14-v1__dieu-4__k34__0",
+        "document_id": "luat-59-2020-qh14-v1",
+        "article_id": "dieu-4",
+        "document_title": "Luật Doanh nghiệp",
+        "article": "Điều 4",
+        "clause": "Khoản 34",
+        "point": null,
+        "source_url": "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"
+      }
+    ]
+  },
+  {
+    "id": "gold_031",
+    "question": "Mức thuế suất thuế thu nhập cá nhân hiện hành là bao nhiêu?",
+    "expected_status": "insufficient_context",
+    "ground_truth": "Tài liệu được truy xuất chưa đủ căn cứ để trả lời.",
+    "gold_chunk_ids": [],
+    "citation": "",
+    "category": "Ngoài phạm vi",
+    "author": "Team 2",
+    "gold_citations": []
+  }
+]
--- /dev/null
+++ b/team2_rag/tests/test_llm_config.py
@@ -0,0 +1,91 @@
+import pytest
+from pydantic import ValidationError
+
+from team2_rag.config.llm_config import LLMClientSettings
+from team2_rag.config.settings import ConfigError, LLMSettings
+
+_ENV = [
+    "LLM_PROVIDER", "LLM_MODEL", "OPENAI_API_KEY", "GEMINI_API_KEY", "QWEN_API_KEY", "QWEN_BASE_URL",
+    "LLM_TIMEOUT_SECONDS", "LLM_MAX_RETRIES", "LLM_TEMPERATURE", "LLM_MAX_OUTPUT_TOKENS", "LLM_MAX_TOKENS",
+    "LLM_CONTEXT_WINDOW_TOKENS", "LLM_MAX_CONTEXT_TOKENS", "LLM_SAFETY_MARGIN_TOKENS",
+    "LLM_MAX_CONTEXT_CHUNKS", "LLM_MAX_CONTEXT_CHARS",
+]
+
+
+@pytest.fixture(autouse=True)
+def _clean_env(monkeypatch):
+    for k in _ENV:
+        monkeypatch.delenv(k, raising=False)
+
+
+def load(**env):
+    return LLMClientSettings(_env_file=None, **env)
+
+
+def test_defaults():
+    s = load()
+    assert (s.provider, s.timeout_seconds, s.max_retries, s.max_tokens) == ("openai", 30.0, 0, 1500)
+    assert (s.max_context_chunks, s.max_context_tokens, s.safety_margin_tokens) == (5, 3000, 256)
+    assert s.context_window_tokens is None
+
+
+def test_env_overrides(monkeypatch):
+    monkeypatch.setenv("LLM_PROVIDER", " Gemini ")
+    monkeypatch.setenv("LLM_MODEL", "g-model")
+    monkeypatch.setenv("LLM_MAX_OUTPUT_TOKENS", "800")
+    monkeypatch.setenv("LLM_CONTEXT_WINDOW_TOKENS", "32000")
+    s = load()
+    assert (s.provider, s.model, s.max_tokens, s.context_window_tokens) == ("gemini", "g-model", 800, 32000)
+
+
+def test_max_tokens_alias(monkeypatch):
+    monkeypatch.setenv("LLM_MAX_TOKENS", "700")
+    assert load().max_tokens == 700
+
+
+def test_secret_not_in_repr(monkeypatch):
+    monkeypatch.setenv("OPENAI_API_KEY", "super-secret")
+    s = load()
+    assert "super-secret" not in repr(s) and "super-secret" not in str(s)
+    assert s.api_key("openai") == "super-secret"
+
+
+@pytest.mark.parametrize(
+    "name,value",
+    [("LLM_PROVIDER", "claude"), ("LLM_TIMEOUT_SECONDS", "31"), ("LLM_TIMEOUT_SECONDS", "0"), ("LLM_MAX_RETRIES", "1")],
+)
+def test_invalid_values_rejected(monkeypatch, name, value):
+    monkeypatch.setenv(name, value)
+    with pytest.raises(ValidationError):
+        load()
+
+
+def test_window_must_exceed_output_plus_margin(monkeypatch):
+    monkeypatch.setenv("LLM_CONTEXT_WINDOW_TOKENS", "1500")
+    with pytest.raises(ValidationError):
+        load()
+
+
+def test_validate_runtime_requires_model_and_key(monkeypatch):
+    with pytest.raises(ConfigError):
+        load().validate_runtime()
+    monkeypatch.setenv("LLM_MODEL", "m")
+    with pytest.raises(ConfigError):
+        load().validate_runtime()
+    monkeypatch.setenv("OPENAI_API_KEY", "k")
+    assert load().validate_runtime().model == "m"
+
+
+def test_to_legacy_roundtrip(monkeypatch):
+    monkeypatch.setenv("LLM_PROVIDER", "qwen")
+    monkeypatch.setenv("LLM_MODEL", "qwen-max")
+    monkeypatch.setenv("QWEN_API_KEY", "k")
+    monkeypatch.setenv("LLM_MAX_OUTPUT_TOKENS", "900")
+    monkeypatch.setenv("LLM_CONTEXT_WINDOW_TOKENS", "32000")
+    legacy = load().to_legacy()
+    assert isinstance(legacy, LLMSettings)
+    assert (legacy.provider, legacy.model, legacy.max_output_tokens, legacy.context_window_tokens) == (
+        "qwen", "qwen-max", 900, 32000,
+    )
+    legacy.validate()
--- /dev/null
+++ b/team2_rag/tests/test_response_models.py
@@0,0 +1,114 @@
+import pytest
+from pydantic import ValidationError
+
+from team2_rag.mock import make_mock_response
+from team2_rag.models.response import Citation, RAGResponse
+
+URL = "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"
+
+
+def cit(cid="C1", **over):
+    base = {
+        "citation_id": cid,
+        "chunk_id": "luat-59-2020-qh14-v1__dieu-1__k0__0",
+        "document_id": "luat-59-2020-qh14-v1",
+        "article_id": "dieu-1",
+        "document_title": "Luật Doanh nghiệp",
+        "article": "Điều 1",
+        "clause": None,
+        "point": None,
+        "source_url": URL,
+    }
+    base.update(over)
+    return base
+
+
+def answered(answer="Nội dung [C1].", *cits):
+    return {"status": "answered", "answer": answer, "citations": list(cits) or [cit()]}
+
+
+def test_valid_answered_roundtrip_keeps_null_fields():
+    payload = RAGResponse.model_validate(answered()).to_payload()
+    assert set(payload) == {"status", "answer", "citations"}
+    assert set(payload["citations"][0]) == {
+        "citation_id", "chunk_id", "document_id", "article_id", "document_title",
+        "article", "clause", "point", "source_url",
+    }
+    assert payload["citations"][0]["clause"] is None and payload["citations"][0]["point"] is None
+
+
+def test_valid_insufficient():
+    r = RAGResponse.model_validate({"status": "insufficient_context", "answer": "Chưa đủ căn cứ.", "citations": []})
+    assert r.citations == [] and r.cited_chunk_ids() == []
+
+
+@pytest.mark.parametrize("scenario", ["answered", "insufficient_context"])
+def test_mock_responses_match_models(scenario):
+    RAGResponse.model_validate(make_mock_response(scenario))
+
+
+def test_multi_citation_order_and_chunk_ids():
+    c2 = cit("C2", chunk_id="x__dieu-2__k1__0", article_id="dieu-2", article="Điều 2", clause="Khoản 1")
+    r = RAGResponse.model_validate(answered("A [C1] B [C2] C [C1].", cit(), c2))
+    assert r.cited_chunk_ids() == ["luat-59-2020-qh14-v1__dieu-1__k0__0", "x__dieu-2__k1__0"]
+
+
+@pytest.mark.parametrize(
+    "bad",
+    [
+        {**answered(), "extra": 1},
+        {"status": "answered", "answer": "A [C1].", "citations": [{"ref": 1, "chunk_id": "x"}]},
+        {"status": "unknown", "answer": "A", "citations": []},
+        {"status": "answered", "answer": "Không có marker.", "citations": [cit()]},
+        {"status": "answered", "answer": "A [C1].", "citations": []},
+        {"status": "answered", "answer": "A [C2].", "citations": [cit()]},
+        {"status": "answered", "answer": "A [C1] [C2].", "citations": [cit()]},
+        {"status": "answered", "answer": "A [C2] [C1].", "citations": [cit("C1"), cit("C2", chunk_id="y")]},
+        {"status": "answered", "answer": "A [C1].", "citations": [cit("C1"), cit("C1")]},
+        {"status": "answered", "answer": "A [C2].", "citations": [cit("C2")]},
+        {"status": "insufficient_context", "answer": "A.", "citations": [cit()]},
+        {"status": "insufficient_context", "answer": "A [C1].", "citations": []},
+        {"status": "answered", "answer": "  ", "citations": [cit()]},
+    ],
+)
+def test_invalid_responses_rejected(bad):
+    with pytest.raises(ValidationError):
+        RAGResponse.model_validate(bad)
+
+
+@pytest.mark.parametrize(
+    "over",
+    [
+        {"citation_id": "1"},
+        {"citation_id": "C0"},
+        {"source_url": "http://vbpl.vn/x"},
+        {"source_url": "/relative"},
+        {"document_id": "tài-liệu"},
+        {"article_id": "dieu 1"},
+        {"clause": ""},
+        {"point": "   "},
+        {"article": ""},
+        {"chunk_id": "x" * 201},
+    ],
+)
+def test_invalid_citation_fields_rejected(over):
+    with pytest.raises(ValidationError):
+        Citation.model_validate(cit(**over))
+
+
+@pytest.mark.parametrize("missing", ["clause", "point", "source_url", "chunk_id", "article_id"])
+def test_missing_citation_field_rejected(missing):
+    data = cit()
+    data.pop(missing)
+    with pytest.raises(ValidationError):
+        Citation.model_validate(data)
--- /dev/null
+++ b/team2_rag/tests/test_error_handlers.py
@@ 0,0 +1,93 @@
+import pytest
+
+pytest.importorskip("httpx")
+
+from fastapi import FastAPI
+from fastapi.testclient import TestClient
+
+from team2_rag.api.handlers import install_error_handlers
+from team2_rag.errors import (
+    ERROR_SPECS,
+    ErrorCode,
+    InternalError,
+    InvalidRequestError,
+    build_error_response,
+    classify,
+)
+from team2_rag.llm.errors import (
+    CitationInvalidError,
+    LLMAuthError,
+    LLMBadOutputError,
+    LLMProviderError,
+    LLMRateLimitError,
+    LLMTimeoutError,
+)
+from team2_rag.prompts.context import ContextBudgetError, ContextBuildError
+
+SECRET = "sk-very-secret-raw-provider-error"
+
+CASES = {
+    "timeout": (lambda: LLMTimeoutError(SECRET, provider="openai"), 504, "LLM_TIMEOUT", True),
+    "rate": (lambda: LLMRateLimitError(SECRET), 503, "LLM_UNAVAILABLE", True),
+    "provider": (lambda: LLMProviderError(SECRET), 503, "LLM_UNAVAILABLE", True),
+    "auth": (lambda: LLMAuthError(SECRET), 503, "LLM_UNAVAILABLE", True),
+    "bad_output": (lambda: LLMBadOutputError(SECRET, raw_text=SECRET), 502, "INVALID_LLM_OUTPUT", False),
+    "citation": (lambda: CitationInvalidError(SECRET), 502, "CITATION_INVALID", False),
+    "invalid_req": (lambda: InvalidRequestError(SECRET), 400, "INVALID_REQUEST", False),
+    "value": (lambda: ValueError(SECRET), 400, "INVALID_REQUEST", False),
+    "ctx_build": (lambda: ContextBuildError(SECRET), 500, "INTERNAL_ERROR", False),
+    "ctx_budget": (lambda: ContextBudgetError(SECRET), 500, "INTERNAL_ERROR", False),
+    "internal": (lambda: InternalError(SECRET), 500, "INTERNAL_ERROR", False),
+    "unhandled": (lambda: RuntimeError(SECRET), 500, "INTERNAL_ERROR", False),
+}
+
+
+@pytest.fixture(scope="module")
+def client():
+    app = FastAPI()
+    install_error_handlers(app)

+    @app.get("/raise/{kind}")
+    def raise_(kind: str):
+        raise CASES[kind][0]()
+
+    @app.get("/int")
+    def int_(x: int):
+        return {"x": x}
+
+    return TestClient(app, raise_server_exceptions=False)
+
+
+@pytest.mark.parametrize("kind", list(CASES))
+def test_exception_to_standard_json(client, kind):
+    _, status, code, retryable = CASES[kind]
+    r = client.get(f"/raise/{kind}")
+    assert r.status_code == status
+    body = r.json()
+    assert set(body) == {"error"}
+    assert set(body["error"]) == {"code", "message", "retryable"}
+    assert body["error"]["code"] == code
+    assert body["error"]["retryable"] is retryable
+    assert SECRET not in r.text
+
+
+def test_request_validation_error_is_400(client):
+    r = client.get("/int", params={"x": "abc"})
+    assert r.status_code == 400
+    assert r.json()["error"]["code"] == "INVALID_REQUEST"
+    assert set(r.json()) == {"error"}
+
+
+def test_every_error_code_has_spec_and_builds_response():
+    for code in ErrorCode:
+        status, body = build_error_response(code)
+        assert status == ERROR_SPECS[code][0]
+        assert body.error.code is code
+
+
+def test_classify_unknown_llm_code_falls_back_to_unavailable():
+    exc = LLMProviderError("x")
+    exc.error_code = "SOMETHING_NEW"
+    assert classify(exc) is ErrorCode.LLM_UNAVAILABLE
--- /dev/null
+++ b/team2_rag/tests/test_answer_citation_accuracy.py
@@ 0,0 +1,114 @@
+import json
+from pathlib import Path
+
+import pytest
+
+from team2_rag.answer import NO_CONTEXT_ANSWER, answer_from_rerank, cited_chunk_ids
+from team2_rag.llm.errors import CitationInvalidError, LLMBadOutputError
+from team2_rag.llm.fake import FakeLLMProvider
+from team2_rag.llm.service import LLMService
+from team2_rag.models.response import RAGResponse
+
+GOLDEN = Path(__file__).resolve().parents[1] / "data" / "golden" / "golden_sample_5qa.json"
+ITEMS = json.loads(GOLDEN.read_text(encoding="utf-8"))
+REQUIRED = {
+    "id", "question", "expected_status", "ground_truth", "gold_chunk_ids",
+    "citation", "category", "author", "gold_citations",
+}
+URL = "https://vbpl.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=142881"
+DISTRACTOR = {
+    "chunk_id": "luat-59-2020-qh14-v1__dieu-9__k1__0", "document_id": "luat-59-2020-qh14-v1",
+    "article_id": "dieu-9", "content": "Nội dung không liên quan.", "document_title": "Luật Doanh nghiệp",
+    "article": "Điều 9", "clause": "Khoản 1", "point": None, "source_url": URL,
+    "score": 0.001, "rank": 99, "retrieval_method": "hybrid_rrf",
+}
+
+
+def rerank_output(item):
+    results = []
+    for i, c in enumerate(item["gold_citations"], 1):
+        row = {k: v for k, v in c.items() if k != "citation_id"}
+        row.update(content=item["ground_truth"], score=1.0 / (i + 1), rank=i, retrieval_method="hybrid_rrf")
+        results.append(row)
+    if results:
+        results.append({**DISTRACTOR, "rank": len(results) + 1})
+    return {"question": item["question"], "results": results}
+
+
+def llm_for(item):
+    cits = item["gold_citations"]
+    answer = item["ground_truth"] + " " + "".join(f"[{c['citation_id']}]" for c in cits)
+    provider = FakeLLMProvider(
+        [{"status": "answered", "answer": answer, "citations": cits}] if cits else []
+    )
+    return provider, LLMService(provider)
+
+
+def by_id(i):
+    return next(x for x in ITEMS if x["id"] == i)
+
+
+def test_golden_dataset_shape():
+    assert len(ITEMS) == 5
+    assert len({x["id"] for x in ITEMS}) == 5
+    for x in ITEMS:
+        assert REQUIRED <= set(x)
+        assert [c["chunk_id"] for c in x["gold_citations"]] == x["gold_chunk_ids"]
+        assert (x["expected_status"] == "answered") == bool(x["gold_chunk_ids"])
+        assert [c["citation_id"] for c in x["gold_citations"]] == [
+            f"C{i}" for i in range(1, len(x["gold_citations"]) + 1)
+        ]
+
+
+@pytest.mark.parametrize("item", ITEMS, ids=[x["id"] for x in ITEMS])
+def test_answer_and_citations_match_ground_truth(item):
+    provider, svc = llm_for(item)
+    resp = answer_from_rerank(rerank_output(item), svc)
+    model = RAGResponse.model_validate(resp)
+    assert model.status == item["expected_status"]
+    assert cited_chunk_ids(resp) == item["gold_chunk_ids"]
+    assert resp["citations"] == item["gold_citations"]
+    if item["expected_status"] == "answered":
+        assert item["ground_truth"] in resp["answer"]
+        assert DISTRACTOR["chunk_id"] not in cited_chunk_ids(resp)
+    else:
+        assert resp["answer"] == NO_CONTEXT_ANSWER
+        assert provider.calls == []
+
+
+def test_citation_metadata_tampering_rejected():
+    item = by_id("gold_003")
+    cits = [{**item["gold_citations"][0], "document_title": "Luật Khác"}]
+    out = {"status": "answered", "answer": "Nội dung [C1].", "citations": cits}
+    with pytest.raises(CitationInvalidError):
+        answer_from_rerank(rerank_output(item), LLMService(FakeLLMProvider([out])))
+
+
+def test_citation_to_chunk_not_in_context_rejected():
+    item = by_id("gold_003")
+    cits = [{**item["gold_citations"][0], "chunk_id": "luat-59-2020-qh14-v1__dieu-99__k1__0"}]
+    out = {"status": "answered", "answer": "Nội dung [C1].", "citations": cits}
+    with pytest.raises(CitationInvalidError):
+        answer_from_rerank(rerank_output(item), LLMService(FakeLLMProvider([out])))
+
+
+def test_answer_without_marker_rejected():
+    item = by_id("gold_003")
+    out = {"status": "answered", "answer": "Không có marker.", "citations": item["gold_citations"]}
+    with pytest.raises(LLMBadOutputError):
+        answer_from_rerank(rerank_output(item), LLMService(FakeLLMProvider([out])))