"""Run retrieval unittest suites and retain JSON, JUnit XML and a readable log."""

import argparse
import json
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.eval_retrieval import environment, fingerprint


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def startTest(self, test):
        super().startTest(test)
        self.current = dict(id=test.id(), status="PASS", details=[])
        self.started = time.perf_counter()

    def stopTest(self, test):
        self.current["seconds"] = time.perf_counter() - self.started
        self.records.append(self.current)
        super().stopTest(test)

    def record_error(self, status, test, err):
        self.current["status"] = status
        detail = self._exc_info_to_string(err, test).replace(str(ROOT), "<repo>")
        self.current["details"].append(detail)

    def addFailure(self, test, err):
        self.record_error("FAIL", test, err)
        super().addFailure(test, err)

    def addError(self, test, err):
        self.record_error("ERROR", test, err)
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.current.update(status="SKIP", details=[reason])
        super().addSkip(test, reason)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.record_error("FAIL" if issubclass(err[0], test.failureException) else "ERROR", subtest, err)
        super().addSubTest(test, subtest, err)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pattern", default="test_*retrieval*.py")
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern=args.pattern)
    with (args.output_dir / "unit.log").open("w", encoding="utf-8") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=RecordedResult).run(suite)
    records = result.records
    counts = {state.lower(): sum(r["status"] == state for r in records) for state in ("PASS", "FAIL", "ERROR", "SKIP")}
    sources = sorted(set((ROOT / "tests").glob(args.pattern)) | {ROOT / "tests/retriever_contract.py"})
    report = dict(run_at=datetime.now(timezone.utc).isoformat(), environment=environment(),
                  pattern=args.pattern, tests_run=result.testsRun, counts=counts, cases=records,
                  sources=[fingerprint(p) for p in sources])
    (args.output_dir / "unit-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    xml = ET.Element("testsuite", name="retrieval", tests=str(result.testsRun), failures=str(counts["fail"]),
                     errors=str(counts["error"]), skipped=str(counts["skip"]))
    for record in records:
        case = ET.SubElement(xml, "testcase", name=record["id"], time=str(record["seconds"]))
        tag = {"FAIL": "failure", "ERROR": "error", "SKIP": "skipped"}.get(record["status"])
        if tag:
            ET.SubElement(case, tag).text = "\n".join(record["details"])
    ET.ElementTree(xml).write(args.output_dir / "junit.xml", encoding="utf-8", xml_declaration=True)
    print(json.dumps(dict(tests_run=result.testsRun, counts=counts)))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
