"""Test pipeline tiền xử lý trên văn bản giả, không đụng corpus đã commit."""

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "preprocess_legal_data",
    ROOT / "scripts" / "preprocess_legal_data.py",
)
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


SAMPLE = """\
Chương I
THÀNH LẬP
Điều 1. Phạm vi
Luật này quy định việc thành lập doanh nghiệp.
Điều 2. Đối tượng
1. Doanh nghiệp.
2. Cơ quan liên quan.
"""


class PreprocessTests(unittest.TestCase):
    def test_clean_text_removes_invisible_and_keeps_words(self):
        dirty = "Luật\u200b này\u00a0quy định"
        cleaned = pipeline.clean_text(dirty)
        self.assertEqual(cleaned, "Luật này quy định\n")
        self.assertNotIn("\u200b", cleaned)

    def test_chunk_document_splits_article_and_clause(self):
        meta = {
            "document_id": "luat-test-v1",
            "document_number": "1/2020/QH14",
            "document_type": "luat",
            "document_title": "Luật thử",
            "issuing_authority": "Quốc hội",
            "issued_date": "2020-01-01",
            "effective_date": "2020-01-01",
            "legal_status": "con_hieu_luc",
            "source_url": "https://vbpl.vn/test",
        }
        chunks = pipeline.chunk_documents.chunk_document(meta, SAMPLE)
        ids = [item["chunk_id"] for item in chunks]
        self.assertIn("luat-1-2020-qh14-v1__dieu-1__k0__0", ids)
        self.assertIn("luat-1-2020-qh14-v1__dieu-2__k1__0", ids)
        self.assertIn("luat-1-2020-qh14-v1__dieu-2__k2__0", ids)
        self.assertTrue(all(item["content"].strip() for item in chunks))

    def test_run_writes_chunks_and_report(self):
        import tempfile

        meta = {
            "document_number": "1/2020/QH14",
            "document_type": "luat",
            "document_title": "Luật thử",
            "issuing_authority": "Quốc hội",
            "issued_date": "2020-01-01",
            "effective_date": "2020-01-01",
            "legal_status": "con_hieu_luc",
            "source_url": "https://vbpl.vn/test",
            "document_id": "luat-test-v1",
        }
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            raw = data_dir / "raw" / "luat-test-v1"
            raw.mkdir(parents=True)
            (raw / "source.txt").write_text("Điều 1. Phạm vi\nNội dung điều 1.\n", encoding="utf-8")
            registry = data_dir / "registry"
            registry.mkdir()
            (registry / "documents.json").write_text(
                json.dumps([meta], ensure_ascii=False),
                encoding="utf-8",
            )
            report = pipeline.run(data_dir)
            self.assertEqual(report["document_count"], 1)
            self.assertGreater(report["chunk_count"], 0)
            self.assertEqual(report["errors"], [])
            chunks = (data_dir / "processed" / "chunks.jsonl").read_text(encoding="utf-8")
            self.assertIn("dieu-1", chunks)
            self.assertTrue((data_dir / "processed" / "processing_report.json").is_file())
            self.assertTrue((data_dir / "interim" / "luat-test-v1.txt").is_file())


if __name__ == "__main__":
    unittest.main()
