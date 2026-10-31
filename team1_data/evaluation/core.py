"""Pipeline đánh giá Retrieval tái lập được (VLRA-48).

Một lần chạy = nhiều cấu hình trên CÙNG Dev Set (golden cố định, ghi sha256). Mỗi cấu hình lưu riêng
config + chỉ số + kết quả từng câu; cả lần chạy có run.json (môi trường, commit, nguồn) và run.log.

Chỉ số tính ở mức "đơn vị pháp lý" (Khoản): chunk_id bỏ hậu tố __<chunk_index>, và các Khoản có nội dung
nguyên văn giống nhau, cùng Điều/Khoản ở hai văn bản (vd Luật 59/2020 và VBHN 67) được coi là một.
Nhờ vậy so sánh được các cấu hình chunk khác nhau; chỉ số "strict" (chunk_id gốc) vẫn được ghi kèm.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import unicodedata
import zlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.eval_retrieval import environment, percentile, validate_cases, validate_output  # noqa: E402
from team1_data.retrieval.common import DEFAULT_LEGAL_STATUS, load_chunks, search_text  # noqa: E402

DEV_SET = ROOT / "team1_data/golden/golden_phase1.json"
CHUNKS = ROOT / "data/doanh-nghiep/processed/chunks.jsonl"
TOP_K = 20
KS = (5, 10, 20)


# ---------- Dữ liệu ----------

def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unit_of(chunk_id: str) -> str:
    """doc__dieu-x__kN__i → doc__dieu-x__kN (Khoản), không phụ thuộc cách cắt chunk."""
    return chunk_id.rsplit("__", 1)[0]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip().lower()


def equivalence(chunks: Iterable[Mapping]) -> dict[str, str]:
    """unit → đại diện: các Khoản trùng nguyên văn, cùng article_id và clause gộp về một."""
    groups: dict[tuple, list[str]] = {}
    for c in chunks:
        if c["chunk_index"] == 0:
            groups.setdefault((c["article_id"], c["clause"], _norm(c["content"])), []).append(unit_of(c["chunk_id"]))
    return {u: min(units) for units in groups.values() for u in units}


def canon_list(ids: Sequence[str], mapping: Callable[[str], str]) -> list[str]:
    seen, out = set(), []
    for i in ids:
        key = mapping(i)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def score(ids: Sequence[str], gold: Iterable[str]) -> dict:
    gold = set(gold)
    if not gold:
        return {f"recall_at_{k}": None for k in KS} | {"mrr_at_20": None}
    out = {f"recall_at_{k}": len(gold.intersection(ids[:k])) / len(gold) for k in KS}
    out["mrr_at_20"] = next((1 / r for r, i in enumerate(ids[:20], 1) if i in gold), 0.0)
    return out


def rechunk(chunks: Sequence[Mapping], size: int | None, overlap: int) -> list[dict]:
    """Cắt Khoản dài hơn `size` từ (token = cụm không khoảng trắng, như chunker) thành cửa sổ trượt.

    size=None giữ nguyên corpus. Mọi metadata giữ nguyên, chỉ đổi content/chunk_id/chunk_index/chunk_count.
    """
    if size is None:
        return [dict(c) for c in chunks]
    if not 0 <= overlap < size:
        raise ValueError("overlap must be in [0, size)")
    out = []
    for c in chunks:
        words = c["content"].split()
        if len(words) <= size:
            out.append(dict(c))
            continue
        step, parts = size - overlap, []
        for start in range(0, len(words), step):
            parts.append(" ".join(words[start:start + size]))
            if start + size >= len(words):
                break
        base = unit_of(c["chunk_id"])
        for i, text in enumerate(parts):
            out.append(dict(c, chunk_id=f"{base}__{i}", content=text, chunk_index=i, chunk_count=len(parts),
                            token_count=len(text.split())))
    return out


def check_inputs(dev_set: Path = DEV_SET, chunks_path: Path = CHUNKS) -> dict:
    """Kiểm tra đầu vào trước khi đánh giá; lỗi thì raise ValueError."""
    cases = json.loads(Path(dev_set).read_text(encoding="utf-8"))
    chunks = load_chunks(chunks_path)
    corpus = {c["chunk_id"]: c for c in chunks}
    if len(corpus) != len(chunks):
        raise ValueError("corpus has duplicate chunk_id")
    validate_cases(cases, set(corpus))
    indexed = {c["chunk_id"] for c in chunks if c["legal_status"] in DEFAULT_LEGAL_STATUS}
    unreachable = sorted({g for c in cases for g in c["gold_chunk_ids"]} - indexed)
    if unreachable:
        raise ValueError(f"gold chunks filtered out by legal_status: {unreachable[:5]}")
    eq = equivalence(chunks)
    gold_docs: dict[str, int] = {}
    for c in cases:
        for g in c["gold_chunk_ids"]:
            gold_docs[corpus[g]["document_id"]] = gold_docs.get(corpus[g]["document_id"], 0) + 1
    return dict(dev_set=dict(path=_rel(dev_set), sha256=sha256(dev_set), cases=len(cases),
                             answered=sum(c["expected_status"] == "answered" for c in cases),
                             gold_ids=sum(len(c["gold_chunk_ids"]) for c in cases)),
                corpus=dict(path=_rel(chunks_path), sha256=sha256(chunks_path), chunks=len(chunks),
                            indexed=len(indexed), merged_equivalent_units=len(eq) - len(set(eq.values()))),
                gold_by_document=dict(sorted(gold_docs.items())))


def _rel(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


# ---------- Embedder chạy offline (không cần tải model) ----------

class HashEmbedder:
    """Túi âm tiết băm vào `dim` chiều. Mốc thấp nhất cho Dense, không học gì."""

    revision = "v1"
    query_prefix = passage_prefix = ""

    def __init__(self, dim: int = 1024):
        self.dim, self.name = dim, f"offline/hash-bow-{dim}"

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for w in re.findall(r"\w+", text.lower()):
            v[zlib.crc32(w.encode("utf-8")) % self.dim] += 1.0
        v[0] += 1e-3
        return v / np.linalg.norm(v)

    def embed_passages(self, texts):
        return np.stack([self._vec(t) for t in texts])

    def embed_query(self, text):
        return self._vec(text)


class LSAEmbedder:
    """TF-IDF (âm tiết 1–2 gram) + TruncatedSVD học trên chính corpus; vector dày `dim` chiều."""

    query_prefix = passage_prefix = ""

    def __init__(self, dim: int = 256, seed: int = 0):
        import sklearn
        self.dim, self.seed = dim, seed
        self.name, self.revision = f"offline/lsa-tfidf-svd{dim}", f"sklearn-{sklearn.__version__}-seed{seed}"
        self._tfidf = self._svd = None

    def embed_passages(self, texts):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._tfidf = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                                      token_pattern=r"(?u)\b\w+\b")
        self._svd = TruncatedSVD(self.dim, random_state=self.seed)
        return self._svd.fit_transform(self._tfidf.fit_transform(list(texts))).astype(np.float32)

    def embed_query(self, text):
        if self._svd is None:
            raise RuntimeError("LSAEmbedder must embed passages before queries")
        vec = self._svd.transform(self._tfidf.transform([text]))[0].astype(np.float32)
        return vec if np.linalg.norm(vec) > 0 else np.eye(self.dim, dtype=np.float32)[0]


def make_embedder(spec: Mapping):
    kind = spec.get("type", "lsa")
    if kind == "hash":
        return HashEmbedder(spec.get("dim", 1024))
    if kind == "lsa":
        return LSAEmbedder(spec.get("dim", 256), spec.get("seed", 0))
    if kind == "sentence_transformers":
        from team1_data.retrieval.embedding import SentenceTransformerEmbedder
        return SentenceTransformerEmbedder(spec["name"], revision=spec.get("revision"),
                                           query_prefix=spec.get("query_prefix", ""),
                                           passage_prefix=spec.get("passage_prefix", ""))
    raise ValueError(f"unknown embedder type {kind}")


# ---------- Chạy ----------

class _Cache:
    """Dùng lại index đã build trong cùng lần chạy (cùng chunking/embedder) để tiết kiệm thời gian."""

    def __init__(self):
        self.items: dict[str, tuple] = {}

    def get(self, key, build):
        if key not in self.items:
            start = time.perf_counter()
            value = build()
            self.items[key] = (value, (time.perf_counter() - start) * 1000)
        return self.items[key]


def build_retriever(cfg: Mapping, chunks: list[dict], cache: _Cache, client):
    from team1_data.retrieval import BM25Retriever, DenseRetriever, HybridRetriever

    ch = cfg.get("chunking", {})
    ckey = f"{ch.get('size')}-{ch.get('overlap', 0)}"
    setup = {}
    bm25_cfg = {"k1": 1.2, "b": 0.75} | cfg.get("bm25", {})
    emb_cfg = cfg.get("embedder", {"type": "lsa", "dim": 256})

    def bm25():
        key = f"bm25|{ckey}|{json.dumps(bm25_cfg, sort_keys=True)}"
        r, ms = cache.get(key, lambda: BM25Retriever(chunks, k1=bm25_cfg["k1"], b=bm25_cfg["b"]))
        setup["bm25_build_ms"] = ms
        return r

    def dense():
        key = f"dense|{ckey}|{json.dumps(emb_cfg, sort_keys=True)}"
        version = hashlib.sha1(key.encode()).hexdigest()[:12]
        r, ms = cache.get(key, lambda: DenseRetriever(chunks, make_embedder(emb_cfg), client=client,
                                                      index_version=version))
        setup["dense_build_ms"] = ms
        return r

    method = cfg["method"]
    if method == "bm25":
        return bm25(), setup
    if method == "dense":
        return dense(), setup
    if method == "hybrid_rrf":
        w = cfg.get("weights", [1.0, 1.0])
        return HybridRetriever(bm25(), dense(), rrf_k=cfg.get("rrf_k", 60), weights=w, timeout=30), setup
    raise ValueError(f"unknown method {method}")


def evaluate_config(cfg: Mapping, cases: list[dict], base_chunks: list[dict], eq: Mapping[str, str],
                    cache: _Cache, client) -> dict:
    ch = cfg.get("chunking", {})
    chunks = rechunk(base_chunks, ch.get("size"), ch.get("overlap", 0))
    corpus = {c["chunk_id"]: c for c in chunks}
    retriever, setup = build_retriever(cfg, chunks, cache, client)
    to_unit = lambda cid: eq.get(unit_of(cid), unit_of(cid))  # noqa: E731
    rows = []
    for case in cases:
        start = time.perf_counter()
        out = retriever.retrieve(case["question"], top_k=TOP_K)
        elapsed = (time.perf_counter() - start) * 1000
        validate_output(out, case["question"], cfg["method"], corpus)
        ids = [r["chunk_id"] for r in out["results"]]
        units = canon_list(ids, to_unit)
        row = dict(id=case["id"], elapsed_ms=round(elapsed, 2), top5=units[:5],
                   gold_units=canon_list(case["gold_chunk_ids"], to_unit),
                   strict=score(ids, case["gold_chunk_ids"]))
        row.update(score(units, row["gold_units"]))
        rows.append(row)
    scored = [r for r in rows if r["recall_at_5"] is not None]
    mean = lambda key, rs: round(sum(rs) / len(rs), 4) if rs else None  # noqa: E731
    keys = [f"recall_at_{k}" for k in KS] + ["mrr_at_20"]
    lat = [r["elapsed_ms"] for r in rows]
    return dict(config=dict(cfg), counts=dict(cases=len(rows), scored=len(scored), corpus_chunks=len(chunks)),
                metrics={k: mean(k, [r[k] for r in scored]) for k in keys},
                metrics_strict_chunk_id={k: mean(k, [r["strict"][k] for r in scored]) for k in keys},
                latency_ms=dict(p50=round(percentile(lat, .5), 2), p95=round(percentile(lat, .95), 2)),
                setup_ms={k: round(v, 1) for k, v in setup.items()},
                cases=rows)


def run(configs: list[dict], out_dir: Path, *, dev_set: Path = DEV_SET, chunks_path: Path = CHUNKS,
        run_id: str | None = None) -> Path:
    from qdrant_client import QdrantClient

    names = [c["name"] for c in configs]
    if len(set(names)) != len(names) or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", n) for n in names):
        raise ValueError("config names must be unique [A-Za-z0-9_.-]+")
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(out_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    log_file = (run_dir / "run.log").open("w", encoding="utf-8")

    def log(fmt, *args):  # file riêng, không dùng logging vì underthesea cấu hình lại logging khi import
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {fmt % args}"
        log_file.write(line + "\n")
        log_file.flush()
        print(line, file=sys.stderr)

    try:
        inputs = check_inputs(dev_set, chunks_path)
        log("inputs %s", json.dumps(inputs, ensure_ascii=False))
        cases = json.loads(Path(dev_set).read_text(encoding="utf-8"))
        base = [c for c in load_chunks(chunks_path) if c["legal_status"] in DEFAULT_LEGAL_STATUS]
        eq = equivalence(base)
        try:
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            head = None
        meta = dict(run_id=run_id, started_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    head=head, inputs=inputs, environment=environment(), top_k=TOP_K, configs=names)
        cache, client, summary = _Cache(), QdrantClient(":memory:"), []
        try:
            for cfg in configs:
                log("config %s start %s", cfg["name"], json.dumps(cfg, ensure_ascii=False))
                result = evaluate_config(cfg, cases, base, eq, cache, client)
                (run_dir / f"{cfg['name']}.json").write_text(
                    json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
                log("config %s done metrics=%s latency=%s setup=%s", cfg["name"], result["metrics"],
                         result["latency_ms"], result["setup_ms"])
                summary.append(dict(name=cfg["name"], **{k: result[k] for k in
                               ("metrics", "metrics_strict_chunk_id", "latency_ms", "setup_ms", "counts")}))
        finally:
            client.close()
        meta["finished_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        meta["summary"] = summary
        (run_dir / "run.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (run_dir / "summary.md").write_text(summary_table(summary, inputs), encoding="utf-8")
        return run_dir
    finally:
        log_file.close()


def summary_table(summary: list[dict], inputs: Mapping) -> str:
    ds = inputs["dev_set"]
    lines = [f"Dev Set `{ds['path']}` sha256 `{ds['sha256'][:12]}` · {ds['answered']} câu có gold · "
             f"corpus {inputs['corpus']['indexed']} chunk được index\n",
             "| Cấu hình | R@5 | R@10 | R@20 | MRR@20 | R@5 strict | p50 ms | p95 ms | build ms | chunk |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for s in summary:
        m, st = s["metrics"], s["metrics_strict_chunk_id"]
        build = sum(s["setup_ms"].values())
        lines.append(f"| {s['name']} | {m['recall_at_5']:.3f} | {m['recall_at_10']:.3f} | {m['recall_at_20']:.3f} | "
                     f"{m['mrr_at_20']:.3f} | {st['recall_at_5']:.3f} | {s['latency_ms']['p50']:.1f} | "
                     f"{s['latency_ms']['p95']:.1f} | {build:.0f} | {s['counts']['corpus_chunks']} |")
    return "\n".join(lines) + "\n"
