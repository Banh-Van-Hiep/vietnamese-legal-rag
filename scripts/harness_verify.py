"""Executable Verification Harness cho dự án Vietnamese Legal RAG.

Thực thi 4 chốt chặn kiểm chứng tự động (Verification Gates):
  - Gate 1 [Hygiene & Structure]: Kiểm tra cấu trúc docs/, AGENTS.md phân tầng, không rò rỉ file checkpoint tạm.
  - Gate 2 [Contract Schemas]: Kiểm tra tính hợp lệ và đồng bộ của các JSON Schema trong contracts/v0.1/.
  - Gate 3 [Report Data Integrity]: Đối soát chéo báo cáo tải NFR-07/08/09 giữa mảng raw_results và bảng tổng.
  - Gate 4 [Automated Test Suite]: Chạy bộ unit test & timeout/concurrency test cốt lõi.
"""
from __future__ import annotations

import hashlib
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

    # Gate 1 chỉ xét file được Git track: file cá nhân chưa track trên máy không làm fail gate,
    # còn file tạm đã lỡ commit thì bị bắt.
    try:
        tracked = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT, text=True, encoding="utf-8"
        ).split("\0")
        tracked = [f for f in tracked if f]
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"[Gate 1 - Hygiene] Không chạy được 'git ls-files' ({exc}); Gate 1 cần một Git checkout."]

    # 2. Kiểm tra cấu trúc thư mục docs/ gốc
    allowed_docs_root = {
        "ARCHITECTURE.md",
        "CODING_CONVENTIONS.md",
        "README.md",
        "REQUIREMENTS.md",
        "decisions",
        "team1_data",
        "team2_rag",
        "team3_fullstack",
    }
    docs_root = {f.split("/")[1] for f in tracked if f.startswith("docs/") and f.count("/") >= 1}
    unexpected = docs_root - allowed_docs_root
    if unexpected:
        errors.append(
            f"[Gate 1 - Hygiene] Thư mục docs/ gốc chứa mục sai quy ước: {sorted(unexpected)}. "
            "Báo cáo của team đặt trong docs/teamX_*/; xem quy tắc tài liệu trong AGENTS.md."
        )

    # 3. Kiểm tra không còn file checkpoint hoặc file tạm bị commit
    for f in tracked:
        name = f.rsplit("/", 1)[-1]
        if name.endswith("checkpoint.json"):
            errors.append(f"[Gate 1 - Hygiene] File checkpoint tạm đang bị Git track: {f}. Chạy 'git rm --cached {f}'.")
        if ".timestamp-" in name and name.endswith(".mjs"):
            errors.append(f"[Gate 1 - Hygiene] File tạm của Vite đang bị Git track: {f}. Chạy 'git rm --cached {f}'.")

    # 4. Kiểm tra git index không track file .env hoặc node_modules
    if any(f == ".env" or f.endswith("/.env") for f in tracked):
        errors.append("[Gate 1 - Hygiene] File nhạy cảm '.env' đang bị Git track! Hãy chạy 'git rm --cached .env'.")
    if any("node_modules/" in f for f in tracked):
        errors.append("[Gate 1 - Hygiene] Thư mục 'node_modules/' đang bị Git track!")

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

    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError:
        return errors + ["[Gate 2 - Contracts] Thiếu gói jsonschema. Cài bằng: pip install -e \".[test]\""]

    for sf in schema_files:
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
            if "type" not in data and "$schema" not in data:
                errors.append(f"[Gate 2 - Contracts] File schema thiếu trường định nghĩa chuẩn: {sf.name}")
            Draft202012Validator.check_schema(data)
        except SchemaError as exc:
            errors.append(f"[Gate 2 - Contracts] {sf.name} không phải JSON Schema 2020-12 hợp lệ: {exc.message}")
        except Exception as exc:
            errors.append(f"[Gate 2 - Contracts] Lỗi cú pháp JSON tại {sf.name}: {exc}")

    # Chạy bộ ví dụ public (positive và negative) của contract SSE.
    validator = contracts_dir / "validate_public_contract.py"
    if validator.exists():
        res = subprocess.run(
            [sys.executable, str(validator)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
        )
        if res.returncode != 0:
            detail = (res.stdout + res.stderr).strip().splitlines()[-3:]
            errors.append(
                "[Gate 2 - Contracts] validate_public_contract.py thất bại: " + " | ".join(detail)
                + ". Kiểm tra đã cài jsonschema[format] chưa."
            )
    return errors


def check_g5_report(report_path: Path) -> list[str]:
    """Báo cáo G5 B0 vs T0 (VLRA-78): chỉ số phải tính lại được từ raw_results, hai bên cùng dataset."""
    if not report_path.exists():
        return []
    sys.path.insert(0, str(ROOT))
    from team2_rag.verification.metrics import summarize_g5_records

    tag = "[Gate 3 - G5]"
    try:
        rep = json.loads(report_path.read_text(encoding="utf-8"))
        systems = rep["systems"]
    except Exception as exc:
        return [f"{tag} Không đọc được {report_path.name}: {exc}"]
    errors: list[str] = []
    if set(systems) != {"b0", "t0"}:
        errors.append(f"{tag} Cần đúng hai hệ thống b0 và t0, đang có {sorted(systems)}.")
    ids = {name: [r.get("id") for r in s.get("raw_results", [])] for name, s in systems.items()}
    for name, s in systems.items():
        raw = s.get("raw_results") or []
        if not raw:
            errors.append(f"{tag} {name} thiếu raw_results.")
        elif summarize_g5_records(raw) != s.get("metrics"):
            errors.append(f"{tag} Bảng chỉ số của {name} khác với kết quả tính lại từ raw_results.")
    if len({tuple(sorted(map(str, v))) for v in ids.values()}) > 1:
        errors.append(f"{tag} B0 và T0 không chạy cùng tập câu hỏi.")
    for d in rep.get("datasets", []):
        path = ROOT / d["path"]
        if path.exists() and hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() != d["sha256"]:
            errors.append(f"{tag} Dataset {d['path']} đã đổi so với lúc đo (sha256 lệch).")
    return errors


def check_gate_3_report_integrity() -> list[str]:
    errors: list[str] = check_g5_report(ROOT / "docs/team2_rag/g5_b0_vs_t0_report.json")
    report_path = ROOT / "docs/team2_rag/ai_service_load_and_stability_report.json"
    if not report_path.exists():
        return errors

    try:
        rep = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return errors + [f"[Gate 3 - Report] Không đọc được file JSON báo cáo tải: {exc}"]

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
    suites = ["team2_rag/tests", "tests"]
    cmd = [sys.executable, "-m", "pytest", *suites, "-q", "-p", "no:cacheprovider"]
    res = subprocess.run(cmd, cwd=ROOT)
    if res.returncode == 5:
        return ["[Gate 4 - Unit Tests] pytest không tìm thấy test nào."]
    if res.returncode != 0:
        return [f"[Gate 4 - Unit Tests] Bộ kiểm thử {suites} thất bại (pytest exit {res.returncode}). "
                "Nếu báo 'No module named pytest', cài bằng: pip install -e \".[test,api,retrieval]\""]
    return []


def main() -> int:
    # Trên Windows, stdout bị chuyển sang file/pipe mặc định dùng cp1252 và crash với tiếng Việt.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
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
