import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "doanh-nghiep"
REGISTRY_FILE = DATA_DIR / "registry" / "documents.json"
INTERIM_DIR = DATA_DIR / "interim"
OUTPUT_FILE = DATA_DIR / "processed" / "chunks.jsonl"


class TestPreprocessingPipeline(unittest.TestCase):

    def test_registry_is_valid(self):
        """Registry phải chứa danh sách tài liệu hợp lệ."""
        self.assertTrue(REGISTRY_FILE.is_file())

        registry = json.loads(
            REGISTRY_FILE.read_text(encoding="utf-8")
        )

        self.assertIsInstance(registry, list)
        self.assertGreater(len(registry), 0)

        document_ids = [item.get("document_id") for item in registry]
        self.assertTrue(all(document_ids))
        self.assertEqual(len(document_ids), len(set(document_ids)))

    def test_input_files_exist_and_not_empty(self):
        """Mỗi tài liệu trong registry phải có file đầu vào."""
        registry = json.loads(
            REGISTRY_FILE.read_text(encoding="utf-8")
        )

        for item in registry:
            with self.subTest(document_id=item.get("document_id")):
                path = INTERIM_DIR / f"{item['document_id']}.txt"
                self.assertTrue(path.is_file(), f"Thiếu file {path.name}")
                self.assertTrue(
                    path.read_text(encoding="utf-8").strip(),
                    f"File rỗng: {path.name}",
                )

    def test_output_chunks_are_valid(self):
        """Chunks đầu ra phải có nội dung và ID duy nhất."""
        self.assertTrue(OUTPUT_FILE.is_file())

        seen_ids = set()
        count = 0
        required_fields = {"chunk_id", "document_id", "content"}

        with OUTPUT_FILE.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                with self.subTest(line=line_number):
                    self.assertTrue(line.strip())

                    chunk = json.loads(line)
                    self.assertIsInstance(chunk, dict)
                    self.assertTrue(required_fields.issubset(chunk.keys()))
                    self.assertTrue(str(chunk["chunk_id"]).strip())
                    self.assertTrue(str(chunk["document_id"]).strip())
                    self.assertTrue(str(chunk["content"]).strip())

                    self.assertNotIn(chunk["chunk_id"], seen_ids)
                    seen_ids.add(chunk["chunk_id"])
                    count += 1

        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()