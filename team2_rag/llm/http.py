"""Transport HTTP tối thiểu (chỉ dùng thư viện chuẩn) để adapter không phụ thuộc SDK.

Adapter nhận `transport` qua constructor nên test có thể thay bằng transport giả,
không cần mạng hay API key.
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping, Optional, Protocol

from team2_rag.llm.errors import LLMProviderError, LLMTimeoutError


@dataclass(frozen=True)
class HttpResponse:
    status: int
    json: Optional[dict]
    text: str = ""


class Transport(Protocol):
    def post_json(self, url: str, headers: Mapping[str, str], body: dict, timeout: float) -> HttpResponse: ...


def _decode(raw: bytes) -> HttpResponse:  # pragma: no cover - helper
    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    return HttpResponse(status=0, json=data if isinstance(data, dict) else None, text=text)


class UrllibTransport:
    def post_json(self, url: str, headers: Mapping[str, str], body: dict, timeout: float) -> HttpResponse:
        req = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                r = _decode(resp.read())
                return HttpResponse(resp.status, r.json, r.text)
        except urllib.error.HTTPError as e:
            r = _decode(e.read())
            return HttpResponse(e.code, r.json, r.text)
        except (socket.timeout, TimeoutError):
            raise LLMTimeoutError("Hết thời gian chờ phản hồi từ LLM provider.") from None
        except urllib.error.URLError as e:
            if isinstance(e.reason, (socket.timeout, TimeoutError)):
                raise LLMTimeoutError("Hết thời gian chờ phản hồi từ LLM provider.") from None
            # Không đưa chi tiết URL/header vào thông báo.
            raise LLMProviderError("Không kết nối được tới LLM provider.") from None
