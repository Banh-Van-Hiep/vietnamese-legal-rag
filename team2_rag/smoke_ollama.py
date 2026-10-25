"""REAL local smoke test: Ollama + configured model through generate_answer (no Team 1 indexes, no API key).

Run from the directory that CONTAINS team2_rag/ (see README "Local LLM via Ollama"):
    python -m team2_rag.smoke_ollama

Uses data/samples/rerank_output_sample.json -> context builder -> token budget -> Ollama -> citation validation.
Exit 0 only when a real model reply passed the same checks as production; otherwise a short reason and exit 1/2.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from .answer import generate_answer, to_error_response
from .config.settings import ConfigError, load_settings, read_dotenv
from .pipeline import validate_generated_response

SAMPLE = Path(__file__).resolve().parent / "data" / "samples" / "rerank_output_sample.json"


class SmokeError(Exception):
    pass


def preflight(settings, urlopen=urllib.request.urlopen) -> None:
    """Check the Ollama server answers and the model is pulled, before spending time on generation."""
    url = settings.ollama_base_url.rstrip("/") + "/models"
    try:
        with urlopen(url, timeout=min(settings.timeout_seconds, 10)) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ids = {m["id"] for m in data["data"]}
    except urllib.error.HTTPError as exc:
        raise SmokeError(f"Ollama responded HTTP {exc.code} at {url}; check OLLAMA_BASE_URL (should end with /v1).") from None
    except (urllib.error.URLError, OSError):
        raise SmokeError(f"Cannot reach Ollama at {url}. Start it (`ollama serve` or the Ollama app).") from None
    except (ValueError, KeyError, TypeError):
        raise SmokeError(f"{url} did not return an Ollama/OpenAI model list; check OLLAMA_BASE_URL.") from None
    if settings.model not in ids and f"{settings.model}:latest" not in ids:
        raise SmokeError(f"Model '{settings.model}' is not pulled. Run: ollama pull {settings.model}")


def main(argv=None, *, env=None, urlopen=urllib.request.urlopen) -> int:
    env = {**read_dotenv(".env"), **os.environ} if env is None else env
    try:
        settings = load_settings(env=env)
        if settings.provider != "ollama":  # never let a smoke test silently call a paid provider
            raise SmokeError(f"LLM_PROVIDER is '{settings.provider}', expected 'ollama'.")
        settings.validate()
        preflight(settings, urlopen)
        sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
        started = time.monotonic()
        response = generate_answer(sample, [], settings=settings, request_id="smoke-ollama")
        validate_generated_response(response)
    except (SmokeError, ConfigError) as exc:
        print(f"SMOKE FAIL: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # LLMError subclasses carry the internal code; anything else is shown by type only
        body = to_error_response(exc)
        detail = body["error"]["code"] if body else "UNEXPECTED"
        print(f"SMOKE FAIL: {type(exc).__name__} ({detail}): {exc}", file=sys.stderr)
        return 1
    print(json.dumps(response, ensure_ascii=False, indent=2))
    print(f"SMOKE OK: provider=ollama model={settings.model} status={response['status']} "
          f"citations={len(response['citations'])} elapsed={time.monotonic() - started:.1f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
