"""Smoke test cho Gemini API: kiểm tra kết nối, token budget và citation validation."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Đảm bảo in tiếng Việt mượt mà trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from team2_rag.answer import generate_answer, to_error_response
from team2_rag.config.settings import ConfigError, load_settings, read_dotenv
from team2_rag.pipeline import validate_generated_response

SAMPLE = Path(__file__).resolve().parent / "data" / "samples" / "rerank_output_sample.json"


def main() -> int:
    env = {**read_dotenv(".env"), **os.environ}
    api_key = env.get("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "AIzaSy_YOUR_API_KEY_HERE":
        print("LỖI: Chưa cấu hình GEMINI_API_KEY trong file .env!", file=sys.stderr)
        return 2

    try:
        settings = load_settings(env=env)
        settings.validate()
        sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
        
        print(f"--> Đang gửi câu hỏi thử nghiệm tới Gemini ({settings.model})...")
        started = time.monotonic()
        response = generate_answer(sample, [], settings=settings, request_id="smoke-gemini")
        validate_generated_response(response)
        elapsed = time.monotonic() - started
    except ConfigError as exc:
        print(f"SMOKE FAIL (ConfigError): {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        body = to_error_response(exc)
        detail = body["error"]["code"] if body else "UNEXPECTED"
        print(f"SMOKE FAIL: {type(exc).__name__} ({detail}): {exc}", file=sys.stderr)
        return 1

    print("\n" + "=" * 60)
    print("KẾT QUẢ PHẢN HỒI TỪ GEMINI (THÀNH CÔNG 100%):")
    print("=" * 60)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print("=" * 60)
    print(f"SMOKE OK: provider={settings.provider} model={settings.model} status={response['status']} "
          f"citations={len(response['citations'])} elapsed={elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
