"""Technical fixtures only: no legal QA is generated or added to the shared set."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from team3_fullstack.tools.split_golden_dataset import FILENAMES, SplitError, split_records, validate_records, write_split

TOOL = Path(__file__).resolve().parents[1] / "tools/split_golden_dataset.py"


def fixture(answered=112):
    return [dict(id=f"fixture_{i:03}", question=f"Synthetic test question {i}?",
                 expected_status="answered" if i < answered else "insufficient_context",
                 ground_truth="Technical fixture only.", gold_chunk_ids=[f"fixture_chunk_{i}"] if i < answered else [],
                 citation="Fixture only", category="Technical fixture", author="test-role",
                 extra_metadata={"fixture_index": i}) for i in range(150)]


class SplitTests(unittest.TestCase):
    def test_112_38_rounding_preserves_every_record_and_extra_field(self):
        rows = fixture(); before = copy.deepcopy(rows)
        dev, test = split_records(rows)
        self.assertEqual((len(dev), len(test)), (90, 60))
        self.assertEqual(Counter(x["expected_status"] for x in dev), {"answered": 67, "insufficient_context": 23})
        self.assertEqual(Counter(x["expected_status"] for x in test), {"answered": 45, "insufficient_context": 15})
        self.assertFalse({x["id"] for x in dev} & {x["id"] for x in test})
        self.assertEqual(sorted(dev + test, key=lambda x: x["id"]), rows)
        self.assertEqual(rows, before)

    def test_113_37_rounding_still_has_exact_90_60(self):
        dev, test = split_records(fixture(113))
        self.assertEqual(Counter(x["expected_status"] for x in dev), {"answered": 68, "insufficient_context": 22})
        self.assertEqual(Counter(x["expected_status"] for x in test), {"answered": 45, "insufficient_context": 15})

    def test_reproducible_independent_of_input_order_and_changes_with_seed(self):
        rows = fixture()
        first = split_records(rows, 42)
        self.assertEqual(first, split_records(list(reversed(rows)), 42))
        self.assertNotEqual(first, split_records(rows, 43))

    def test_duplicate_ids_and_normalized_questions_are_rejected(self):
        for field in ("id", "question"):
            with self.subTest(field=field):
                rows = fixture(); rows[1][field] = "  " + rows[0][field].upper() + "  "
                with self.assertRaisesRegex(SplitError, "duplicate normalized"):
                    split_records(rows)

    def test_wrong_sizes_and_non_array_are_rejected(self):
        for value in ([], fixture()[:50], fixture() + [fixture()[0]], {"records": fixture()}):
            with self.subTest(kind=type(value).__name__), self.assertRaises(SplitError):
                validate_records(value)

    def test_required_fields_types_enum_and_chunk_logic(self):
        mutations = [lambda x: x.pop("question"), lambda x: x.update(author=" "),
                     lambda x: x.update(question=123), lambda x: x.update(expected_status="answerable"),
                     lambda x: x.update(gold_chunk_ids=[]), lambda x: x.update(gold_chunk_ids="chunk"),
                     lambda x: x.update(gold_chunk_ids=[1]), lambda x: x.update(gold_chunk_ids=["x", "x"]),
                     lambda x: x.update(expected_status="insufficient_context"),
                     lambda x: x.update(question="Cafe\u0301")]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                rows = fixture(); mutation(rows[0])
                with self.assertRaises(SplitError):
                    split_records(rows)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "input.json"

    def source_file(self, rows=None):
        self.source.write_text(json.dumps(fixture() if rows is None else rows), encoding="utf-8")
        return self.source

    def test_cli_end_to_end_hashes_and_no_source_change(self):
        self.source_file(); before = self.source.read_bytes(); output = self.root / "out"
        run = subprocess.run([sys.executable, str(TOOL), "--input", str(self.source), "--output-dir", str(output)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["status"], "split_only")
        self.assertEqual(report["input"]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(report["input"]["file"], "input.json")
        self.assertNotIn(str(self.root), json.dumps(report))
        for key, expected in (("dev", 90), ("test", 60)):
            item = report["outputs"][key]; raw = (output / item["file"]).read_bytes()
            self.assertEqual(item["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(len(json.loads(raw)), expected)
        self.assertEqual(json.loads((output / FILENAMES[2]).read_bytes()), report)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse((output / "golden_dataset_v1.manifest.json").exists())

    def test_existing_output_is_not_overwritten_or_partially_created(self):
        self.source_file(); output = self.root / "out"; output.mkdir()
        protected = output / FILENAMES[1]; protected.write_bytes(b"keep")
        with self.assertRaisesRegex(SplitError, "already exists"):
            write_split(self.source, output)
        self.assertEqual(protected.read_bytes(), b"keep")
        self.assertEqual(list(output.iterdir()), [protected])

    def test_invalid_50_records_has_exit_2_and_no_output(self):
        self.source_file(fixture()[:50]); output = self.root / "out"
        run = subprocess.run([sys.executable, str(TOOL), "--input", str(self.source), "--output-dir", str(output)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn("exactly 150", run.stderr)
        self.assertFalse(output.exists())

    def test_duplicate_json_keys_and_nan_rejected_without_output(self):
        for value in ('[{"id":"a","id":"b"}]', '[NaN]'):
            self.source.write_text(value, encoding="utf-8")
            with self.subTest(value=value), self.assertRaises(SplitError):
                write_split(self.source, self.root / "out")
            self.assertFalse((self.root / "out").exists())

    def test_reproducible_output_bytes(self):
        self.source_file()
        write_split(self.source, self.root / "first", 11)
        write_split(self.source, self.root / "second", 11)
        for name in FILENAMES:
            self.assertEqual((self.root / "first" / name).read_bytes(), (self.root / "second" / name).read_bytes())

    def test_singleton_and_single_class_warn_without_duplication(self):
        for answered in (149, 150):
            with self.subTest(answered=answered):
                self.source_file(fixture(answered))
                out = self.root / str(answered); report = write_split(self.source, out)
                self.assertTrue(report["warnings"])
                rows = json.loads((out / FILENAMES[0]).read_bytes()) + json.loads((out / FILENAMES[1]).read_bytes())
                self.assertEqual(len({x["id"] for x in rows}), 150)

    def test_write_failure_rolls_back_only_its_own_created_files(self):
        self.source_file(); output = self.root / "out"; output.mkdir()
        other = output / "unrelated.txt"; other.write_text("keep", encoding="utf-8")
        original = Path.open
        def failing_open(path, *args, **kwargs):
            if path.name == FILENAMES[1] and args and args[0] == "xb":
                raise OSError("simulated write failure")
            return original(path, *args, **kwargs)
        with patch.object(Path, "open", failing_open), self.assertRaises(OSError):
            write_split(self.source, output)
        self.assertEqual(list(output.iterdir()), [other])


if __name__ == "__main__":
    unittest.main()
