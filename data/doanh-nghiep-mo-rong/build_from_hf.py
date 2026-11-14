"""Chọn ~1000 văn bản trung ương về doanh nghiệp từ bộ dữ liệu vbpl.vn trên Hugging Face.

Nguồn: https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents (CC BY 4.0,
crawl từ vbpl.vn). Tải trước 2 file vào một thư mục rồi truyền đường dẫn:
    data/metadata.parquet, data/content.parquet

    python3 data/doanh-nghiep-mo-rong/build_from_hf.py --hf-dir <thư mục parquet>

Cần thêm pandas và pyarrow (chỉ cho main); các hàm còn lại chỉ dùng thư viện chuẩn.

Ghi interim/{document_id}.txt và registry/documents.json, rồi chạy
scripts/preprocess_legal_data.run() để ghi processed/chunks.jsonl (+ bản nén .gz
được commit). Không đụng corpus chính data/doanh-nghiep/ và index đang dùng.
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
import re
import shutil
import unicodedata
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

import jsonschema

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATASET = "th1nhng0/vietnamese-legal-documents"

spec = importlib.util.spec_from_file_location("preprocess_legal_data", ROOT / "scripts" / "preprocess_legal_data.py")
preprocess = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preprocess)
chunker = preprocess.chunk_documents

# Chỉ các loại có trong enum document_type của chunk_metadata.schema.json.
TYPES = {
    "Bộ luật": "bo_luat",
    "Luật": "luat",
    "Văn bản hợp nhất": "van_ban_hop_nhat",
    "Nghị định": "nghi_dinh",
    "Nghị quyết": "nghi_quyet",
    "Thông tư": "thong_tu",
}
STATUS = {"Còn hiệu lực": "con_hieu_luc", "Hết hiệu lực một phần": "het_hieu_luc_mot_phan"}
CORE = r"doanh nghiệp|đăng ký kinh doanh|hộ kinh doanh|phá sản|hợp tác xã|vốn nhà nước|cổ phần hóa|quản trị công ty"
# Nhóm gần: luật điều chỉnh hoạt động của doanh nghiệp. Chỉ so trên tiêu đề vì
# trường lĩnh vực của nguồn quá rộng (vd "Thương mại" gắn cả văn bản quốc phòng).
NEAR = (
    r"luật đầu tư|đầu tư kinh doanh|đầu tư nước ngoài|đầu tư ra nước ngoài|chứng khoán"
    r"|kế toán|kiểm toán độc lập|cạnh tranh|thuế thu nhập doanh nghiệp|quản lý thuế|hóa đơn"
    r"|thuế giá trị gia tăng|thương mại điện tử|luật thương mại|giao dịch bảo đảm|đấu thầu"
    r"|kinh doanh bảo hiểm|bộ luật lao động|hợp đồng lao động|sở hữu trí tuệ|xuất khẩu, nhập khẩu"
)
NEAR_EXCLUDE = r"đầu tư công|kiểm toán nhà nước|khen thưởng|thi đua"
# Tầng 3, chỉ dùng để bù cho đủ số lượng: thuế/phí, hải quan, lao động, tín dụng.
RELATED = r"thuế|lệ phí|hải quan|xuất khẩu|nhập khẩu|lao động|tiền lương|tổ chức tín dụng|bảo hiểm xã hội"
TIERS = {0: "core", 1: "near", 2: "related"}
TITLE_MAX = 500  # maxLength của document_title trong chunk_metadata.schema.json
SCHEMA = json.loads((ROOT / "docs/team1_data/schemas/chunk_metadata.schema.json").read_text(encoding="utf-8"))
BLOCK = ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "table"]


def iso(date) -> str | None:
    if not isinstance(date, str):
        return None
    try:
        return datetime.strptime(date.strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def slug(text: str) -> str:
    text = unicodedata.normalize("NFD", text.replace("Đ", "D").replace("đ", "d"))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


class _TextExtractor(HTMLParser):
    """Giữ chữ của thẻ inline trên cùng dòng; xuống dòng ở <br> và cuối thẻ khối."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0  # đang ở trong <style>/<script>

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self.skip += 1
        elif tag == "br":
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self.skip = max(0, self.skip - 1)
        elif tag in BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return preprocess.clean_text("".join(parser.parts))


def candidates(meta, existing: set[str]):
    """meta: DataFrame metadata.parquet. Trả ứng viên đã gán tầng và sắp thứ tự ưu tiên."""
    m = meta[
        meta.pham_vi.isin(["Trung ương", "Toàn quốc"])
        & meta.loai_van_ban.isin(TYPES)
        & meta.tinh_trang_hieu_luc.isin(STATUS)
        & meta.id.str.fullmatch(r"\d+")
        & meta.so_ky_hieu.fillna("").str.strip().ne("")
    ].copy()
    m["issued"] = m.ngay_ban_hanh.map(iso)
    m = m[m.issued.notna() & ~m.so_ky_hieu.map(slug).isin(existing)]
    title = m.title.fillna("").str.lower()
    m["tier"] = 3
    m.loc[title.str.contains(RELATED, regex=True) & ~title.str.contains(NEAR_EXCLUDE, regex=True), "tier"] = 2
    m.loc[title.str.contains(NEAR, regex=True) & ~title.str.contains(NEAR_EXCLUDE, regex=True), "tier"] = 1
    m.loc[(title + " " + m.linh_vuc.fillna("").str.lower()).str.contains(CORE, regex=True), "tier"] = 0
    m = m[m.tier < 3]
    m["type_rank"] = m.loai_van_ban.map(list(TYPES).index)
    return m.sort_values(["tier", "type_rank", "issued", "id"], ascending=[True, True, False, True])


def clean_title(title: str, number: str) -> str:
    """Bỏ tiền tố "<Loại> số <số hiệu>" trùng với document_number; cắt nếu quá giới hạn schema."""
    prefix = r"^(?:" + "|".join(TYPES) + r")\s+(?:số\s+)?" + re.escape(number.strip()) + r"\s*"
    title = re.sub(prefix, "", title.strip())
    title = title[:1].upper() + title[1:]
    if len(title) > TITLE_MAX:
        title = title[: TITLE_MAX - 1].rsplit(" ", 1)[0] + "…"
    return title


def registry_entry(row) -> dict:
    document_type = TYPES[row.loai_van_ban]
    meta = {
        "document_number": row.so_ky_hieu.strip(),
        "document_type": document_type,
        "document_title": clean_title(row.title, row.so_ky_hieu),
        "issuing_authority": row.co_quan_ban_hanh.strip() if isinstance(row.co_quan_ban_hanh, str) and row.co_quan_ban_hanh.strip() else "Không rõ",
        "issued_date": row.issued,
        "effective_date": iso(row.ngay_co_hieu_luc),
        "legal_status": STATUS[row.tinh_trang_hieu_luc],
        "source_url": f"https://vbpl.vn/van-ban/chi-tiet/{slug(row.title)}--{row.id}",
        "source_format": "html",
        "source_dataset": f"https://huggingface.co/datasets/{DATASET}",
        "source_dataset_id": row.id,
        "scope_tier": TIERS[row.tier],
        "note": "Lấy từ bộ dữ liệu HF (crawl vbpl.vn); source_url dựng theo mẫu vbpl.vn, chưa mở kiểm tra.",
    }
    meta["document_id"] = chunker.document_ids(meta)[1]
    return meta


def number_in_text(number: str, text: str) -> bool:
    head = slug(text[:4000])
    return slug(number) in head


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hf-dir", type=Path, required=True)
    ap.add_argument("--target", type=int, default=1000)
    ap.add_argument("--out", type=Path, default=HERE)
    args = ap.parse_args()
    import pandas as pd
    import pyarrow.parquet as pq

    existing_registry = json.loads((ROOT / "data/doanh-nghiep/registry/documents.json").read_text(encoding="utf-8"))
    existing = {slug(d["document_number"]) for d in existing_registry}
    cand = candidates(pd.read_parquet(args.hf_dir / "metadata.parquet"), existing)
    print(f"ứng viên: {len(cand)} theo tầng {cand.tier.map(TIERS).value_counts().to_dict()}")

    content = pq.ParquetFile(args.hf_dir / "content.parquet")
    wanted = set(cand.id)
    html = {}
    for batch in content.iter_batches(batch_size=2000, columns=["id", "content_html"]):
        for doc_id, body in zip(batch.column(0).to_pylist(), batch.column(1).to_pylist()):
            if doc_id in wanted and body:
                html[doc_id] = body

    interim = args.out / "interim"
    interim.mkdir(parents=True, exist_ok=True)
    validator = jsonschema.Draft202012Validator(SCHEMA, format_checker=jsonschema.FormatChecker())
    registry, seen, skipped = [], set(), {}
    for row in cand.itertuples():
        if len(registry) >= args.target:
            break
        reason = None
        if row.id not in html:
            reason = "không có toàn văn"
        else:
            meta = registry_entry(row)
            text = html_to_text(html[row.id])
            if meta["document_id"] in seen:
                reason = "trùng document_id"
            elif not number_in_text(meta["document_number"], text):
                reason = "số hiệu không có trong toàn văn"
            else:
                chunks = chunker.chunk_document(meta, text)
                ids = [c["chunk_id"] for c in chunks]
                if not ids:
                    reason = "không tách được Điều"
                elif len(ids) != len(set(ids)):
                    # Văn bản kèm quy chế/điều lệ đánh số Điều lại từ đầu: chunker chưa hỗ trợ.
                    reason = "số Điều lặp (có văn bản kèm theo)"
                elif any(next(validator.iter_errors(c), None) for c in chunks):
                    # Chunker chưa tách khoản dài: chunk > maxLength content của schema.
                    reason = "chunk sai schema (khoản quá dài)"
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        seen.add(meta["document_id"])
        (interim / f"{meta['document_id']}.txt").write_text(text, encoding="utf-8", newline="\n")
        registry.append(meta)

    (args.out / "registry").mkdir(exist_ok=True)
    (args.out / "registry" / "documents.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"chọn {len(registry)} văn bản; bỏ qua: {skipped}")
    report = preprocess.run(args.out)
    # chunks.jsonl (~130MB) vượt giới hạn file của GitHub: chỉ commit bản nén.
    jsonl = args.out / "processed" / "chunks.jsonl"
    with jsonl.open("rb") as src, open(jsonl.with_suffix(".jsonl.gz"), "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as dst:
            shutil.copyfileobj(src, dst)
    print(f"{report['chunk_count']} chunks, {len(report['errors'])} lỗi")


if __name__ == "__main__":
    main()
