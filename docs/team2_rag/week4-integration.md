# VLRA-38 / VLRA-45 — Pipeline and internal FastAPI draft

Base: `develop` at `3d64c4d`; work branch: `feature/team2/datdo-week4`.
Scope: wire existing Hybrid Retrieval, reranker, Context Builder and generation;
expose the Python service to Spring Boot; add 10 Golden QA pairs.

## Entry points

- `team2_rag.pipeline.RAGPipeline.query(question, history, request_id=...)`
- `team2_rag.runtime.build_runtime()` loads indexes, embedding, BGE and existing LLM configuration once.
- `team2_rag.api.create_app()` is a FastAPI factory.
- `python -m team2_rag.run_query "..."` runs one configured real query.
- `team2_rag.service.query()` remains the Week 2 mock; it is not this service's handler.

The runtime uses Hybrid RRF from Team 1 and `generate_answer()` from Person 2.
Reranking uses strict mode: missing packages, oversized pairs or inference errors
raise instead of silently claiming BGE succeeded. Model limits remain documented
in [reranker-prototype.md](reranker-prototype.md).

The BM25 `_search` currently returns an envelope while Hybrid's `rrf_fuse` needs
a list. `BM25SearchAdapter` unwraps this at the Team 2 boundary; it also accepts a
future corrected list. No Team 1 ranking source is changed in this branch.

## Internal API

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/internal/v1/query` | `{question, history}` to `{status, answer, citations}` |
| GET | `/internal/v1/health` | Process liveness; does not prove models are ready |
| GET | `/internal/v1/ready` | 503 until runtime loads successfully |

No browser CORS is needed: Spring Boot calls this service. Public chat, SSE,
conversation IDs, storage and the document viewer stay with Team 3. There is no
new public `/api/v1/query` in this Python application.

Input is strict JSON: exactly `question` and `history`, no duplicate keys or
nonfinite numbers. Question: 1–2000 Unicode characters after trimming. History:
at most five complete user/assistant pairs and 20000 content characters. Body:
256 KiB. No scenario, model, top_k or IDs in the request. Trace is carried by
`X-Request-ID`, including safe error responses.

The HTTP wait is capped at 45 seconds, with one active inference at a time.
This is an HTTP deadline, **not cancellation of a CPU/model/provider call**.
A timed-out thread keeps its slot until it finishes; subsequent requests receive
503 rather than accumulating model work. Run one Uvicorn worker for this MVP.
For the overall deadline the draft returns 504 `UPSTREAM_TIMEOUT`; Person 2 and
Team 3 must confirm this whole-pipeline mapping alongside VLRA-47 before release.

Explicit follow-up references such as "trường hợp vừa nêu" receive a request for
clarification. General history-based query rewriting has not been implemented or
claimed; previous answers never become legal source material.

## Required handoff from Person 2 — not yet present on GitHub

The current `team2_rag.types.RAGResponse` is a `TypedDict`, not a Pydantic model.
At the checked baseline, `team2_rag.api.handlers` and the new validating
`RAGResponse` model have **not been pushed** (confirmed by the user).

1. The factory automatically imports and calls
   `install_error_handlers(app)` from `team2_rag.api.handlers` once available.
   The package structure reserves that path; no competing `handlers.py` is added.
   When installed, pipeline exceptions are re-raised to those handlers rather
   than swallowed by the draft's local mapping. Tests currently inject an
   installer double; they do not prove the unpublished implementation works.
2. Pass Person 2's class as `create_app(response_model=RAGResponse)` and/or
   `RAGPipeline(..., response_model=RAGResponse)`. The final result then goes
   through `RAGResponse.model_validate(...).model_dump(mode="json")`.
   Its module path is still pending; do not guess it or duplicate the model.
3. Without these modules, the service remains a development draft: shared JSON
   Schema plus a final marker guard and legacy safe error mapping are used.
   Do not mark shared handler/model integration complete.

The audit reproduced this gap in the existing generator: a valid `[C1]` together
with `[C0]` or `[C01]` was accepted. The new final guard rejects these, lowercase,
spaced/unclosed markers, missing/extra citations, duplicate chunk IDs and numbering
that is not consecutive in first-appearance order. Malformed output returns
`INVALID_LLM_OUTPUT` / 502 in the legacy adapter. Citation provenance errors from
the existing generator remain `CITATION_INVALID` / 502.

Once Person 2 pushes, run the same regressions with the **real shared classes**,
including Team2Error, LLMError and output validation exceptions. An injected test
double is not acceptance evidence for VLRA-47 or VLRA-39.

## Local installation and real smoke run

Run from the repository root (Python 3.10+; Python 3.12 recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test,api,rag,retrieval,dense,reranker]"
```

Use the Team 1 CLI to build BM25 and Dense indexes from the same corpus, with
the same final directory name (`week4-v1` in the example). Dense build requires
Qdrant and its actual embedding model. Existing indexes may be reused when their
manifests agree. This draft does not rebuild a live Qdrant collection on startup.

```bash
python -m team1_data.retrieval build --out data/index/bm25/week4-v1
python -m team1_data.retrieval dense-build --out data/index/dense/week4-v1
```

Copy the entries from `configs/team2-api.env.example` into local `.env`; Person 2
provides LLM model/key settings. Do not overwrite another person's `.env`.
The runtime uses the embedding model/revision and prefixes recorded in the dense
manifest. API keys and `.env` are not included in evidence or commits.

```bash
python -m team2_rag.run_query "Công ty cổ phần có bắt buộc phải có cổ phần phổ thông không?"
python -m uvicorn team2_rag.api:create_app --factory --host 127.0.0.1 --port 8001 --workers 1
```

```bash
curl -i http://127.0.0.1:8001/internal/v1/ready
curl -i http://127.0.0.1:8001/internal/v1/query \
  -H 'Content-Type: application/json' -H 'X-Request-ID: local-smoke-1' \
  -d '{"question":"Công ty cổ phần có bắt buộc phải có cổ phần phổ thông không?","history":[]}'
```

Real BGE and LLM execution are still pending on a configured machine. No API key
or model/index cache is available in the review environment. Passing fake-provider
tests must not be reported as real inference or legal-answer quality evaluation.
OpenAI token budgeting additionally needs `tiktoken`; Gemini/Qwen counters and
model/context settings remain Person 2's work. Without a token counter the existing
generator uses its documented development-only character approximation.

## Validation performed

- 104 existing tests in `team2_rag/tests` passed.
- 44 root Team 2 tests passed (22 existing plus 22 new pipeline/API regressions).
- Actual BM25, Dense/Qdrant in-memory and Hybrid RRF were wired through the
  pipeline and FastAPI TestClient: HTTP 200, original source metadata, trace kept.
  This check used deterministic test embeddings, fake scoring and a fake LLM.
- Golden validator passed 40 samples; new IDs `gold_031` through `gold_040`.
- New QA answers are grounded in the pinned `67/VBHN-VPQH` corpus (15/08/2025),
  each with one existing source chunk. They are not a claim of a fresh review of
  all legal changes through the current date. The original 30 samples are retained.

```bash
python -m unittest discover -s tests -p 'test_team2*.py'
python -m unittest discover -s team2_rag/tests -t .
python -m team2_rag.validate_golden
```
