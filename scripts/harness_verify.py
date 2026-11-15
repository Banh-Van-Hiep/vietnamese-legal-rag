"""Executable Verification Harness cho dự án Vietnamese Legal RAG.

Thực thi 4 chốt chặn kiểm chứng tự động (Verification Gates):
  - Gate 1 [Hygiene & Structure]: Kiểm tra cấu trúc docs/, AGENTS.md phân tầng, không rò rỉ file checkpoint tạm.
  - Gate 2 [Contract Schemas]: Kiểm tra tính hợp lệ và đồng bộ của các JSON Schema trong contracts/v0.1/.
  - Gate 3 [Report Data Integrity]: Đối soát chéo báo cáo tải NFR-07/08/09 giữa mảng raw_results và bảng tổng.
  - Gate 4 [Automated Test Suite]: Chạy bộ unit test & timeout/concurrency test cốt lõi.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def check_gate_1_hygiene() -> list[str]:
    errors: list[str] = []
    # 1. Kiểm tra sự tồn tại của hệ thống AGENTS.md phân tầng
    required_agents_files = [
        ROOT / "AGENTS.md",
        ROOT / "team1_data/AGENTS.md",
        ROOT / "team2_rag/AGENTS.md",
        ROOT / "team3_fullstack/AGENTS.md",
    ]
    for af in required_agents_files:
        if not af.exists():
            errors.append(f"[Gate 1 - Hygiene] Thiếu file định tuyến ngữ cảnh: {af.relative_to(ROOT)}")

    # 2. Kiểm tra cấu trúc thư mục docs/ gốc
    docs_dir = ROOT / "docs"
    allowed_docs_root = {
        "ARCHITECTURE.md",
        "CODING_CONVENTIONS.md",
        "README.md",
        "team1_data",
        "team2_rag",
        "team3_fullstack",
    }
    if docs_dir.exists():
        actual_docs_root = {p.name for p in docs_dir.iterdir()}
        unexpected = actual_docs_root - allowed_docs_root
        if unexpected:
            errors.append(f"[Gate 1 - Hygiene] Thư mục docs/ gốc chứa mục sai quy ước: {sorted(unexpected)}")

    # 3. Kiểm tra không còn file checkpoint tạm chưa xóa
    ckpt = ROOT / "docs/team2_rag/e2e_nfr07_checkpoint.json"
    if ckpt.exists():
        errors.append(f"[Gate 1 - Hygiene] File checkpoint tạm chưa được xóa: {ckpt.relative_to(ROOT)}")

    # 4. Kiểm tra git index không track file .env hoặc node_modules
    try:
        tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
        if ".env" in tracked:
            errors.append("[Gate 1 - Hygiene] File nhạy cảm '.env' đang bị Git track! Hãy chạy 'git rm --cached .env'.")
        if any("node_modules/" in f for f in tracked):
            errors.append("[Gate 1 - Hygiene] Thư mục 'node_modules/' đang bị Git track!")
    except Exception:
        pass

    return errors


def check_gate_2_contracts() -> list[str]:
    errors: list[str] = []
    contracts_dir = ROOT / "contracts/v0.1"
    if not contracts_dir.exists():
        errors.append("[Gate 2 - Contracts] Thiếu thư mục hợp đồng chuẩn 'contracts/v0.1/'.")
        return errors

    schema_files = sorted(contracts_dir.glob("*.schema.json"))
    if len(schema_files) < 5:
        errors.append(f"[Gate 2 - Contracts] Số lượng schema trong contracts/v0.1/ quá ít ({len(schema_files)} file).")

    for sf in schema_files:
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
            if "type" not in data and "$schema" not in data:
                errors.append(f"[Gate 2 - Contracts] File schema thiếu trường định nghĩa chuẩn: {sf.name}")
        except Exception as exc:
            errors.append(f"[Gate 2 - Contracts] Lỗi cú pháp JSON tại {sf.name}: {exc}")
    return errors


def check_gate_3_report_integrity() -> list[str]:
    errors: list[str] = []
    report_path = ROOT / "docs/team2_rag/ai_service_load_and_stability_report.json"
    if not report_path.exists():
        return errors

    try:
        rep = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"[Gate 3 - Report] Không đọc được file JSON báo cáo tải: {exc}"]

    raw = rep.get("raw_results", [])
    outcomes = rep.get("request_outcomes", {})
    if not raw:
        errors.append("[Gate 3 - Report] Báo cáo tải thiếu mảng 'raw_results' chi tiết từng câu.")
        return errors

    if len(raw) != outcomes.get("total"):
        errors.append(f"[Gate 3 - Report] Số phần tử raw_results ({len(raw)}) != total ({outcomes.get('total')}).")

    counts = {"answered": 0, "insufficient_context": 0, "error": 0, "timeout": 0}
    e2e_vals: list[float] = []
    for item in raw:
        st = item.get("outcome")
        counts[st] = counts.get(st, 0) + 1
        e2e_vals.append(float(item["stage_latency_s"]["e2e_total"]))

    for k, v in counts.items():
        if outcomes.get(k) != v:
            errors.append(f"[Gate 3 - Report] Lệch số ca '{k}': bảng tổng={outcomes.get(k)}, raw_results={v}.")

    # Đảm bảo dữ liệu là số đo thật (không phải hằng số gán cứng)
    if len(set(round(x, 3) for x in e2e_vals)) <= 2 and len(e2e_vals) >= 10:
        errors.append("[Gate 3 - Report] Độ trễ trong raw_results trùng lặp bất thường (không phải số đo thực nghiệm).")

    calc_p95 = round(float(np.percentile(e2e_vals, 95)), 3)
    rep_p95 = rep["stage_latency"]["e2e_total"]["p95_s"]
    if abs(calc_p95 - rep_p95) > 0.01:
        errors.append(f"[Gate 3 - Report] P95 bảng tổng ({rep_p95}s) != P95 tính từ raw_results ({calc_p95}s).")

    return errors


def check_gate_4_unit_tests() -> list[str]:
    cmd = [sys.executable, "-m", "pytest", "team2_rag/tests", "-q"]
    res = subprocess.run(cmd, cwd=ROOT)
    if res.returncode != 0:
        return ["[Gate 4 - Unit Tests] Bộ kiểm thử 'team2_rag/tests' thất bại."]
    return []


def main() -> int:
    print("==========================================================")
    print("   VIETNAMESE LEGAL RAG — HARNESS VERIFICATION GATES")
    print("==========================================================")
    all_errors: list[str] = []
    gates = [
        ("Gate 1: Repo Hygiene & Progressive Disclosure Map", check_gate_1_hygiene),
        ("Gate 2: Contract-First JSON Schemas (contracts/v0.1)", check_gate_2_contracts),
        ("Gate 3: Benchmark Report & Raw Results Integrity", check_gate_3_report_integrity),
        ("Gate 4: Core Unit & NFR-08 Timeout/Concurrency Tests", check_gate_4_unit_tests),
    ]
    for title, fn in gates:
        print(f"-> Đang kiểm tra {title}...")
        errs = fn()
        if errs:
            all_errors.extend(errs)
            for e in errs:
                print(f"   [FAIL] {e}")
        else:
            print(f"   [PASS] {title}")

    if all_errors:
        print(f"\n[FAILED] Phát hiện {len(all_errors)} lỗi vi phạm Harness.")
        return 1
    print("\n[SUCCESS] Toàn bộ 4 chốt chặn Harness đều PASSED 100%!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
