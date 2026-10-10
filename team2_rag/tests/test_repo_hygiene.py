import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
class HygieneTests(unittest.TestCase):
    def test_no_python_schema_duplicate(self):
        self.assertFalse((ROOT/"team2_rag"/"llm"/"schema.py").exists())
    def test_env_example_has_no_real_secret(self):
        text=(ROOT/".env.example").read_text(encoding="utf-8")
        self.assertNotIn("sk-",text); self.assertNotIn("AIza",text)
    def test_docs_team2_exists(self):
        self.assertTrue((ROOT/"docs"/"team2_rag").is_dir())

if __name__ == "__main__": unittest.main()
