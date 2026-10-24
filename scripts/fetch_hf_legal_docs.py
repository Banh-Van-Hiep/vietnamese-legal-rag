"""Lấy văn bản pháp luật từ bộ dữ liệu Hugging Face th1nhng0/vietnamese-legal-documents.

Bộ dữ liệu được thu từ vbpl.vn (CSDL quốc gia về pháp luật, Bộ Tư pháp), giấy phép CC BY 4.0.
Dùng thay cho tải trực tiếp vbpl.vn vì cổng mới yêu cầu reCAPTCHA cho nội dung toàn văn.

Đầu vào: CSV có cột so_ky_hieu, muc (P0/P1), nhom, ghi_chu.
Đầu ra (trong --out, mặc định data/doanh-nghiep):
  raw/{document_id}/source.html   HTML gốc của bộ dữ liệu
  raw/{document_id}/source.txt    text đã tách đoạn, chưa sửa câu chữ
  raw/{document_id}/fetch_info.json
  registry/hf_pending.json        mục registry chờ review, CHƯA gộp vào documents.json
  sources/{tên list}_report.csv   kết quả từng dòng: lấy được / bỏ qua và lý do

Cài đặt một lần:  python -m pip install pyarrow huggingface_hub
Chạy từ thư mục gốc repo:
  python scripts/fetch_hf_legal_docs.py --list data/doanh-nghiep/sources/pilot_30.csv

Chỉ đọc cột id của content.parquet rồi tải đúng các row group chứa văn bản cần lấy,
không tải toàn bộ bộ dữ liệu (khoảng 4 GB).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

REPO = "th1nhng0/vietnamese-legal-documents"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "doanh-nghiep"

# Loại văn bản trong bộ dữ liệu -> document_type của registry (phải có trong PREFIX của chunk_documents.py).
DOCUMENT_TYPES = {
    "Luật": "luat",
    "Bộ luật": "bo_luat",
    "Nghị định": "nghi_dinh",
    "Thông tư": "thong_tu",
    "Văn bản hợp nhất": "van_ban_hop_nhat",
}
# Trạng thái được nhận theo tiêu chí "còn hiệu lực + VBHN"; còn lại bị loại và ghi lý do.
LEGAL_STATUS = {
    "Còn hiệu lực": "con_hieu_luc",
    "Hết hiệu lực một phần": "het_hieu_luc_mot_phan",
}
STATUS_RANK = {"Còn hiệu lực": 0, "Hết hiệu lực một phần": 1}
RE_ARTICLE = re.compile(r"^Điều\s+(\d+[a-z]?)[.:]")


def number_key(value: str | None) -> str:
    """Khóa so khớp số ký hiệu: NFC, chữ hoa, bỏ khoảng trắng, Đ -> D."""
    text = unicodedata.normalize("NFC", value or "").upper()
    return re.sub(r"\s+", "", text).replace("Đ", "D")


def iso_date(value: str | None) -> str | None:
    """DD/MM/YYYY -> YYYY-MM-DD; giữ None nếu trống hoặc sai định dạng."""
    match = re.fullmatch(r"\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*", value or "")
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    return f"{year:04d}-{month:02d}-{day:02d}"


class _TextExtractor(HTMLParser):
    """HTML -> các dòng text. Thẻ khối và <br> sinh xuống dòng; ô bảng nối bằng ' | '."""

    BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6",
             "table", "section", "article", "ul", "ol", "blockquote", "hr", "center"}
    SKIP = {"script", "style", "head", "title", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")
        elif tag in ("td", "th"):
            self.parts.append(" | ")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if tag in ("br", "hr"):
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Tách đoạn từ HTML, chuẩn hóa NFC và khoảng trắng; không sửa câu chữ.

    Mỗi đoạn cách nhau một dòng trống, giống raw/*/source.txt hiện có của corpus.
    """
    parser = _TextExtractor()
    parser.feed(html or "")
    parser.close()
    text = unicodedata.normalize("NFC", "".join(parser.parts))
    text = text.replace(" ", " ").replace("\t", " ")
    text = re.sub(r"[​‌‍﻿­]", "", text)
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \r\f\v]+", " ", line).strip()
        line = re.sub(r"^(\| )+|( \|)+$", "", line).strip()
        if line and line != "|":
            lines.append(line)
    return "\n\n".join(lines) + ("\n" if lines else "")


def clean_title(title: str | None, number: str, document_kind: str) -> str:
    """Tiêu đề theo cách đặt tên của registry: bỏ "số <số ký hiệu>", có loại văn bản ở đầu.

    "Luật Hợp tác xã số 17/2023/QH15" -> "Luật Hợp tác xã";
    "Nghị định số 92/2024/NĐ-CP Về đăng ký…" -> "Nghị định về đăng ký…"; "Cạnh tranh" -> "Luật Cạnh tranh".
    """
    text = unicodedata.normalize("NFC", title or "").strip()
    text = re.sub(r"\s*\bsố\s*" + re.escape(number.strip()) + r"\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" ,;-")
    if not text.lower().startswith(document_kind.lower()):
        text = f"{document_kind} {text}".strip()
    head, rest = text[: len(document_kind)], text[len(document_kind):]
    rest = re.sub(r"^\s+(Về|Quy|Hướng|Ban|Sửa)\b", lambda m: " " + m.group(1).lower(), rest)
    return head + rest


def article_stats(text: str) -> dict:
    numbers = [m.group(1) for line in text.split("\n") if (m := RE_ARTICLE.match(line))]
    return {
        "article_count": len(numbers),
        "first_article": numbers[0] if numbers else None,
        "last_article": numbers[-1] if numbers else None,
    }


def choose(candidates: list[dict]) -> dict | None:
    """Chọn bản trung ương, đúng loại hỗ trợ, trạng thái tốt nhất; hòa thì lấy ngày ban hành mới hơn."""
    if not candidates:
        return None
    # VBHN có số ký hiệu riêng (…/VBHN-…); nếu trùng số với văn bản gốc thì ưu tiên văn bản gốc
    # để document_type và document_id đúng với số ký hiệu đã ghi trong danh mục.
    def rank(row):
        return (
            0 if row.get("pham_vi") == "Trung ương" else 1,
            0 if row.get("loai_van_ban") in DOCUMENT_TYPES else 1,
            1 if row.get("loai_van_ban") == "Văn bản hợp nhất" and "VBHN" not in number_key(row.get("so_ky_hieu")) else 0,
            STATUS_RANK.get(row.get("tinh_trang_hieu_luc"), 9),
        )
    best = min(rank(row) for row in candidates)
    tied = [row for row in candidates if rank(row) == best]
    return max(tied, key=lambda row: iso_date(row.get("ngay_ban_hanh")) or "")


def load_document_ids(out_dir: Path):
    """Dùng đúng hàm sinh document_id của chunk_documents.py để ID thống nhất với corpus."""
    path = out_dir / "chunk_documents.py"
    spec = importlib.util.spec_from_file_location("enterprise_chunk_documents", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.document_ids


def build_entry(row: dict, wanted: dict, document_ids, revision: str, text: str) -> dict:
    meta = {
        "document_number": row["so_ky_hieu"].strip(),
        "document_type": DOCUMENT_TYPES[row["loai_van_ban"]],
        "document_title": clean_title(row.get("title"), row["so_ky_hieu"], row["loai_van_ban"]),
        "issuing_authority": (row.get("co_quan_ban_hanh") or "").strip(),
        "issued_date": iso_date(row.get("ngay_ban_hanh")),
        "effective_date": iso_date(row.get("ngay_co_hieu_luc")),
        "legal_status": LEGAL_STATUS[row["tinh_trang_hieu_luc"]],
        "source_url": f"https://vbpl.vn/van-ban/chi-tiet/{row['id']}",
        "source_format": "html",
    }
    document_key, document_id = document_ids(meta)
    data = text.encode("utf-8")
    meta.update({
        "note": (
            f"Lấy từ bộ dữ liệu Hugging Face {REPO} (thu từ vbpl.vn, CC BY 4.0), "
            f"revision {revision}. Trạng thái hiệu lực theo bộ dữ liệu, cần Team 1 xác minh lại trên vbpl.vn."
        ),
        "document_id": document_id,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": hashlib.sha256(data).hexdigest(),
        "chars": len(text),
        "lines": text.count("\n"),
        **article_stats(text),
        "source_dataset": REPO,
        "source_dataset_revision": revision,
        "vbpl_id": row["id"],
        "dataset_effect_status": row.get("tinh_trang_hieu_luc"),
        "expiry_date": iso_date(row.get("ngay_het_hieu_luc")),
        "linh_vuc": row.get("linh_vuc"),
        "nganh": row.get("nganh"),
        "scope_priority": wanted["muc"],
        "scope_group": wanted["nhom"],
    })
    return meta


def read_metadata(path: str) -> list[dict]:
    import pyarrow.parquet as pq
    columns = ["id", "title", "so_ky_hieu", "ngay_ban_hanh", "loai_van_ban", "ngay_co_hieu_luc",
               "ngay_het_hieu_luc", "nganh", "linh_vuc", "co_quan_ban_hanh", "pham_vi", "tinh_trang_hieu_luc"]
    return pq.read_table(path, columns=columns).to_pylist()


def read_content(revision: str, ids: set[str]) -> dict[str, str]:
    """Đọc content_html của các id cần lấy, chỉ tải row group có chứa chúng."""
    import pyarrow.parquet as pq
    from huggingface_hub import HfFileSystem
    found: dict[str, str] = {}
    fs = HfFileSystem()
    with fs.open(f"datasets/{REPO}@{revision}/data/content.parquet", "rb", block_size=8 * 1024 * 1024) as handle:
        parquet = pq.ParquetFile(handle)
        total = parquet.num_row_groups
        for index in range(total):
            group_ids = parquet.read_row_group(index, columns=["id"]).column("id").to_pylist()
            if not ids.intersection(group_ids):
                continue
            table = parquet.read_row_group(index, columns=["id", "content_html"]).to_pylist()
            for row in table:
                if row["id"] in ids:
                    found[row["id"]] = row["content_html"] or ""
            print(f"  row group {index + 1}/{total}: {len(found)}/{len(ids)} văn bản", flush=True)
            if len(found) == len(ids):
                break
    return found


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    args.add_argument("--list", required=True, type=Path, help="CSV: so_ky_hieu,muc,nhom,ghi_chu")
    args.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args.add_argument("--cache", type=Path, default=None, help="thư mục cache (mặc định cache chung của huggingface_hub)")
    args.add_argument("--force", action="store_true", help="ghi đè raw/{id} đã có")
    options = args.parse_args()
    try:
        from huggingface_hub import HfApi, hf_hub_download
        import pyarrow  # noqa: F401
    except ImportError:
        print("Thiếu thư viện. Chạy: python -m pip install pyarrow huggingface_hub")
        return 2

    wanted_rows = list(csv.DictReader(options.list.open(encoding="utf-8-sig")))
    revision = HfApi().dataset_info(REPO).sha
    print(f"Bộ dữ liệu {REPO} @ {revision}")
    metadata_path = hf_hub_download(REPO, "data/metadata.parquet", repo_type="dataset",
                                    revision=revision, cache_dir=str(options.cache) if options.cache else None)
    by_key: dict[str, list[dict]] = {}
    for row in read_metadata(metadata_path):
        by_key.setdefault(number_key(row["so_ky_hieu"]), []).append(row)
    print(f"Đã đọc metadata: {sum(len(v) for v in by_key.values())} văn bản")

    document_ids = load_document_ids(options.out)
    existing = {p.name for p in (options.out / "raw").iterdir() if p.is_dir()}
    report, selected = [], []
    for wanted in wanted_rows:
        row = choose(by_key.get(number_key(wanted["so_ky_hieu"]), []))
        result = {"so_ky_hieu": wanted["so_ky_hieu"], "muc": wanted["muc"], "nhom": wanted["nhom"],
                  "ket_qua": "", "ly_do": "", "vbpl_id": "", "document_id": "", "tieu_de": "",
                  "trang_thai_dataset": "", "so_dieu": ""}
        report.append(result)
        if row is None:
            result.update(ket_qua="bo_qua", ly_do="không có trong bộ dữ liệu")
            continue
        result.update(vbpl_id=row["id"], tieu_de=row.get("title") or "",
                      trang_thai_dataset=row.get("tinh_trang_hieu_luc") or "")
        if row.get("loai_van_ban") not in DOCUMENT_TYPES:
            result.update(ket_qua="bo_qua", ly_do=f"loại chưa hỗ trợ: {row.get('loai_van_ban')}")
        elif row.get("tinh_trang_hieu_luc") not in LEGAL_STATUS:
            result.update(ket_qua="bo_qua", ly_do=f"không đạt tiêu chí hiệu lực: {row.get('tinh_trang_hieu_luc')}")
        else:
            selected.append((wanted, row, result))

    contents = read_content(revision, {row["id"] for _, row, _ in selected}) if selected else {}
    pending = []
    for wanted, row, result in selected:
        html = contents.get(row["id"])
        if not html:
            result.update(ket_qua="bo_qua", ly_do="bộ dữ liệu không có toàn văn")
            continue
        text = html_to_text(html)
        if not text.strip():
            result.update(ket_qua="bo_qua", ly_do="toàn văn trong bộ dữ liệu rỗng")
            continue
        entry = build_entry(row, wanted, document_ids, revision, text)
        result.update(document_id=entry["document_id"], so_dieu=entry["article_count"])
        if entry["document_id"] in existing and not options.force:
            result.update(ket_qua="bo_qua", ly_do="đã có trong corpus")
            continue
        if entry["article_count"] == 0:
            result["ly_do"] = "không nhận ra dòng 'Điều N.', cần xem lại"
        folder = options.out / "raw" / entry["document_id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "source.html").write_text(html, encoding="utf-8", newline="\n")
        (folder / "source.txt").write_text(text, encoding="utf-8", newline="\n")
        (folder / "fetch_info.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
        result["ket_qua"] = "lay_duoc"
        pending.append(entry)

    registry_dir = options.out / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)
    (registry_dir / "hf_pending.json").write_text(json.dumps(pending, ensure_ascii=False, indent=2) + "\n",
                                                  encoding="utf-8", newline="\n")
    report_path = options.list.with_name(options.list.stem + "_report.csv")
    with report_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(report[0].keys()) if report else ["so_ky_hieu"])
        writer.writeheader()
        writer.writerows(report)

    taken = sum(1 for r in report if r["ket_qua"] == "lay_duoc")
    print(f"Xong: lấy được {taken}/{len(report)} văn bản. Báo cáo: {report_path}")
    for r in report:
        if r["ket_qua"] != "lay_duoc" or r["ly_do"]:
            print(f"  - {r['so_ky_hieu']}: {r['ket_qua']} {r['ly_do']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
