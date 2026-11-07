"""Test các hàm thuần của data/doanh-nghiep-mo-rong/build_from_hf.py (không cần parquet)."""

import gzip
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "doanh-nghiep-mo-rong"
spec = importlib.util.spec_from_file_location("build_from_hf", DATA / "build_from_hf.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class PureFunctionTests(unittest.TestCase):
    def test_iso_date(self):
        self.assertEqual(build.iso("01/07/2025"), "2025-07-01")
        self.assertIsNone(build.iso(None))
        self.assertIsNone(build.iso(float("nan")))
        self.assertIsNone(build.iso("không rõ"))

    def test_source_url_slug_matches_existing_registry_pattern(self):
        # 68/2025/TT-BTC trong data/doanh-nghiep/registry có source_url dạng này.
        title = "Thông tư số 68/2025/TT-BTC Ban hành biểu mẫu sử dụng trong đăng ký doanh nghiệp, đăng ký hộ kinh doanh"
        self.assertEqual(
            f"https://vbpl.vn/van-ban/chi-tiet/{build.slug(title)}--179097",
            "https://vbpl.vn/van-ban/chi-tiet/thong-tu-so-68-2025-tt-btc-ban-hanh-bieu-mau-su-dung"
            "-trong-dang-ky-doanh-nghiep-dang-ky-ho-kinh-doanh--179097",
        )

    def test_clean_title_strips_type_and_number_and_respects_schema_limit(self):
        self.assertEqual(build.clean_title("Thông tư số 68/2025/TT-BTC ban hành biểu mẫu", "68/2025/TT-BTC"), "Ban hành biểu mẫu")
        self.assertEqual(build.clean_title("Văn bản hợp nhất số 02/VBHN-KTNN Hệ thống", "02/VBHN-KTNN"), "Hệ thống")
        self.assertEqual(build.clean_title("Luật Phục hồi, phá sản số 142/2025/QH15", "142/2025/QH15"), "Luật Phục hồi, phá sản số 142/2025/QH15")
        long_title = build.clean_title("Nghị định số 1/2020/NĐ-CP " + "quy định " * 100, "1/2020/NĐ-CP")
        self.assertLessEqual(len(long_title), build.TITLE_MAX)
        self.assertTrue(long_title.endswith("…"))

    def test_html_to_text_keeps_inline_on_one_line_and_drops_style(self):
        html = (
            "<html><style>p { margin: 0 }</style><body>"
            "<p><strong>Điều 1.</strong> Phạm vi điều chỉnh</p>"
            "<p>1. Khoản một;<br>2. Khoản hai.</p></body></html>"
        )
        self.assertEqual(build.html_to_text(html), "Điều 1. Phạm vi điều chỉnh\n1. Khoản một;\n2. Khoản hai.\n")

    def test_number_in_text(self):
        self.assertTrue(build.number_in_text("122/2021/NĐ-CP", "CHÍNH PHỦ\nSố: 122/2021/NĐ-CP\n"))
        # Toàn văn của văn bản khác số hiệu (lỗi ghép id ở nguồn) phải bị loại.
        self.assertFalse(build.number_in_text("122/2021/NĐ-CP", "CHÍNH PHỦ\nSố: 122/2020/NĐ-CP\n"))

    def test_nghi_quyet_document_id_prefix(self):
        meta = {"document_type": "nghi_quyet", "document_number": "116/2020/QH14"}
        self.assertEqual(build.chunker.document_ids(meta), ("nq-116-2020-qh14", "nq-116-2020-qh14-v1"))


class CommittedOutputTests(unittest.TestCase):
    def test_registry_and_chunks_are_consistent(self):
        registry = json.loads((DATA / "registry" / "documents.json").read_text(encoding="utf-8"))
        ids = {d["document_id"] for d in registry}
        self.assertEqual(len(ids), len(registry))
        main = json.loads((ROOT / "data/doanh-nghiep/registry/documents.json").read_text(encoding="utf-8"))
        self.assertFalse({d["document_number"] for d in main} & {d["document_number"] for d in registry})
        for meta in registry:
            self.assertIn(meta["scope_tier"], {"core", "near", "related"})
            self.assertIn(meta["legal_status"], {"con_hieu_luc", "het_hieu_luc_mot_phan"})
            self.assertTrue((DATA / "interim" / f"{meta['document_id']}.txt").is_file())
        seen_docs, chunk_ids = set(), set()
        with gzip.open(DATA / "processed" / "chunks.jsonl.gz", "rt", encoding="utf-8") as fh:
            for line in fh:
                chunk = json.loads(line)
                self.assertNotIn(chunk["chunk_id"], chunk_ids)
                chunk_ids.add(chunk["chunk_id"])
                seen_docs.add(chunk["document_id"])
        self.assertEqual(seen_docs, ids)


if __name__ == "__main__":
    unittest.main()
