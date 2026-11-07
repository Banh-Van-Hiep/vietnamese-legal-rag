from __future__ import annotations

import gzip
import json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPANDED = ROOT / "data" / "doanh-nghiep-mo-rong"
REGISTRY = EXPANDED / "registry" / "documents.json"
REPORT = EXPANDED / "processed" / "processing_report.json"
CHUNKS = EXPANDED / "processed" / "chunks.jsonl.gz"
CHUNK_SCHEMA = ROOT / "docs" / "team1_data" / "schemas" / "chunk_metadata.schema.json"
BASE_CHUNKS = ROOT / "data" / "doanh-nghiep" / "processed" / "chunks.jsonl"
EDGE_CASES = ROOT / "team1_data" / "golden" / "edge_cases_v1.json"

EXPECTED_DOCS = 1000
EXPECTED_CHUNKS = 60382
ALLOWED_STATUS = {"con_hieu_luc", "het_hieu_luc_mot_phan", "chua_co_hieu_luc", "het_hieu_luc"}
ALLOWED_CASE_TYPES = {
    "multi_citation", "out_of_corpus", "insufficient_context", "amended_law",
    "partially_expired", "citation_mismatch", "version_conflict",
}
# These are fixture evaluation labels, not claims about Team 2's HTTP API contract.
ALLOWED_EXPECTED_STATUS = {"answered", "insufficient_context"}


def read_json(path: Path):
    assert path.is_file(), f"Missing file: {path}"
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def iter_chunks(path: Path):
    assert path.is_file(), f"Missing file: {path}"
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig") as f:
        for line_number, line in enumerate(f, start=1):
            if line.strip():
                try:
                    yield line_number, json.loads(line)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSONL at {path}:{line_number}: {e}")


@pytest.fixture(scope="module")
def registry():
    records = read_json(REGISTRY)
    assert isinstance(records, list), "Registry root must be a list"
    return records


@pytest.fixture(scope="module")
def report():
    value = read_json(REPORT)
    assert isinstance(value, dict), "Processing report root must be an object"
    return value


@pytest.fixture(scope="module")
def expanded_scan():
    """Parse compressed chunks once for all cross-document integrity checks."""
    by_doc = Counter()
    ids = set()
    duplicate_ids = []
    blank_content = []
    malformed_metadata = []
    doc_numbers = {}
    doc_statuses = {}
    total = 0
    for line_number, chunk in iter_chunks(CHUNKS):
        total += 1
        if not isinstance(chunk, dict):
            malformed_metadata.append((line_number, "chunk not an object"))
            continue
        chunk_id = chunk.get("chunk_id")
        doc_id = chunk.get("document_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            malformed_metadata.append((line_number, "missing chunk_id"))
        elif chunk_id in ids:
            duplicate_ids.append(chunk_id)
        else:
            ids.add(chunk_id)
        if not isinstance(doc_id, str) or not doc_id:
            malformed_metadata.append((line_number, "missing document_id"))
        else:
            by_doc[doc_id] += 1
            doc_numbers.setdefault(doc_id, set()).add(chunk.get("document_number"))
            doc_statuses.setdefault(doc_id, set()).add(chunk.get("legal_status"))
        if not isinstance(chunk.get("content"), str) or not chunk["content"].strip():
            blank_content.append(line_number)
    return {
        "total": total,
        "by_doc": by_doc,
        "ids": ids,
        "duplicates": duplicate_ids,
        "blank_content": blank_content,
        "malformed_metadata": malformed_metadata,
        "doc_numbers": doc_numbers,
        "doc_statuses": doc_statuses,
    }


@pytest.fixture(scope="module")
def base_ids():
    return {chunk["chunk_id"] for _, chunk in iter_chunks(BASE_CHUNKS)}


@pytest.fixture(scope="module")
def cases():
    value = read_json(EDGE_CASES)
    assert isinstance(value, list), "edge_cases_v1.json root must be a list"
    return value


class TestCorpus1000:
    def test_registry_has_1000_unique_documents(self, registry):
        assert len(registry) == EXPECTED_DOCS
        ids = [doc.get("document_id") for doc in registry]
        assert all(isinstance(x, str) and x.strip() for x in ids)
        assert len(set(ids)) == len(ids), "Duplicate document_id in registry"

    def test_registry_metadata(self, registry):
        missing = []
        invalid = []
        required = ("document_id", "document_number", "document_title",
                    "document_type", "issued_date", "effective_date", "legal_status", "source_url")
        for doc in registry:
            doc_id = doc.get("document_id", "<unknown>")
            missing_fields = [key for key in required if not doc.get(key)]
            if missing_fields:
                missing.append((doc_id, missing_fields))
            if doc.get("legal_status") not in ALLOWED_STATUS:
                invalid.append((doc_id, "legal_status", doc.get("legal_status")))
            for key in ("issued_date", "effective_date"):
                value = doc.get(key)
                if value:
                    try:
                        date.fromisoformat(value)
                    except (ValueError, TypeError):
                        invalid.append((doc_id, key, value))
            url = doc.get("source_url")
            if url:
                parsed = urlparse(url)
                if parsed.scheme != "https" or not parsed.netloc:
                    invalid.append((doc_id, "source_url", url))
        assert not missing, f"Missing registry fields (first 10): {missing[:10]}"
        assert not invalid, f"Invalid registry values (first 10): {invalid[:10]}"

    def test_processing_report_matches_registry(self, registry, report):
        rows = report.get("documents")
        assert isinstance(rows, list)
        assert report.get("document_count") == EXPECTED_DOCS
        assert len(rows) == EXPECTED_DOCS
        registry_ids = {x["document_id"] for x in registry}
        report_ids = [x.get("document_id") for x in rows]
        assert len(set(report_ids)) == EXPECTED_DOCS, "Duplicate report document_id"
        assert set(report_ids) == registry_ids, "Registry/report document IDs differ"
        assert report.get("chunk_count") == EXPECTED_CHUNKS
        assert sum(x.get("chunk_count", 0) for x in rows) == EXPECTED_CHUNKS
        assert all(isinstance(x.get("chunk_count"), int) and x["chunk_count"] > 0 for x in rows)
        processing_errors = [(x["document_id"], x["errors"]) for x in rows if x.get("errors")]
        assert not processing_errors, f"Processing errors: {processing_errors[:10]}"

    def test_real_chunks_match_report(self, registry, report, expanded_scan):
        scan = expanded_scan
        assert scan["total"] == EXPECTED_CHUNKS
        expected = {x["document_id"]: x["chunk_count"] for x in report["documents"]}
        assert set(scan["by_doc"]) == {x["document_id"] for x in registry}
        diff = [(doc_id, count, scan["by_doc"].get(doc_id, 0))
                for doc_id, count in expected.items() if scan["by_doc"].get(doc_id, 0) != count]
        assert not diff, f"Report/real chunk count mismatch: {diff[:10]}"
        assert not scan["duplicates"], f"Duplicate chunk_id: {scan['duplicates'][:10]}"
        assert not scan["malformed_metadata"], f"Malformed chunk metadata: {scan['malformed_metadata'][:10]}"
        assert not scan["blank_content"], f"Blank content lines: {scan['blank_content'][:10]}"

    def test_chunk_metadata_consistent_with_registry(self, registry, expanded_scan):
        by_id = {x["document_id"]: x for x in registry}
        discrepancies = []
        for doc_id, numbers in expanded_scan["doc_numbers"].items():
            expected_number = by_id[doc_id].get("document_number")
            if numbers != {expected_number}:
                discrepancies.append((doc_id, "document_number", numbers, expected_number))
        for doc_id, statuses in expanded_scan["doc_statuses"].items():
            expected_status = by_id[doc_id].get("legal_status")
            if statuses != {expected_status}:
                discrepancies.append((doc_id, "legal_status", statuses, expected_status))
        assert not discrepancies, f"Metadata mismatch (first 10): {discrepancies[:10]}"

    def test_all_chunks_follow_metadata_schema(self):
        """Requires jsonschema; validates every one of the 60,382 chunks."""
        jsonschema = pytest.importorskip("jsonschema", reason="Install with: python -m pip install jsonschema")
        schema = read_json(CHUNK_SCHEMA)
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        errors = []
        error_count = 0
        for line_number, chunk in iter_chunks(CHUNKS):
            # Do not hold all error objects/whole corpus in memory.
            for err in validator.iter_errors(chunk):
                error_count += 1
                if len(errors) < 8:
                    errors.append(f"line {line_number}, {list(err.absolute_path)}: {err.message}")
        assert error_count == 0, f"{error_count} schema errors; examples: {errors}"


class TestEdgeCases:
    def test_edge_case_ids_unique_and_fields_valid(self, cases):
        assert cases, "No edge cases provided"
        ids = []
        for case in cases:
            assert isinstance(case, dict)
            for key in ("id", "question", "case_type", "expected_status",
                        "corpus", "gold_chunk_ids", "expected_citations", "review_status"):
                assert key in case, f"Missing {key} in case {case.get('id')}"
            assert isinstance(case["id"], str) and case["id"]
            assert isinstance(case["question"], str) and case["question"].strip()
            assert case["case_type"] in ALLOWED_CASE_TYPES
            assert case["expected_status"] in ALLOWED_EXPECTED_STATUS
            assert case["corpus"] in {"base", "expanded"}
            assert isinstance(case["gold_chunk_ids"], list)
            assert isinstance(case["expected_citations"], list)
            ids.append(case["id"])
        assert len(set(ids)) == len(ids), "Duplicate edge case ID"

    def test_gold_chunk_ids_exist(self, cases, base_ids, expanded_scan):
        missing = []
        for case in cases:
            available = base_ids if case["corpus"] == "base" else expanded_scan["ids"]
            for chunk_id in case["gold_chunk_ids"]:
                if chunk_id not in available:
                    missing.append((case["id"], case["corpus"], chunk_id))
        assert not missing, f"gold_chunk_id does not exist (first 10): {missing[:10]}"

    def test_expected_citations_use_real_chunks(self, cases, base_ids, expanded_scan):
        problems = []
        for case in cases:
            available = base_ids if case["corpus"] == "base" else expanded_scan["ids"]
            for chunk_id in case["expected_citations"]:
                if not isinstance(chunk_id, str) or chunk_id not in available:
                    problems.append((case["id"], chunk_id))
            if set(case["expected_citations"]) != set(case["gold_chunk_ids"]):
                problems.append((case["id"], "expected_citations != gold_chunk_ids"))
        assert not problems, f"Citation fixture errors (first 10): {problems[:10]}"

    def test_multi_citation_and_insufficient_context_rules(self, cases):
        for case in cases:
            citations = case["expected_citations"]
            if case["case_type"] == "multi_citation":
                assert case["expected_status"] == "answered"
                assert len(set(citations)) >= 2, f"{case['id']} needs >= 2 unique citations"
            if case["case_type"] in {"out_of_corpus", "insufficient_context"}:
                assert case["expected_status"] == "insufficient_context"
                assert not citations, f"{case['id']} should not cite unsupported chunks"



class TestEdgeCaseCoverage:

    def test_required_case_types(self, cases):
        required = {
            "amended_law",
            "partially_expired",
            "multi_citation",
            "out_of_corpus",
            "insufficient_context",
            "citation_mismatch",
            "version_conflict",
        }

        actual = {case["case_type"] for case in cases}

        assert required.issubset(actual), (
            f"Missing case types: {required - actual}"
        )
        assert len(cases) >= 11, (
            f"Only {len(cases)} edge cases found"
        )

    def test_citation_mismatch_candidates(
        self, cases, base_ids, expanded_scan
    ):
        mismatch_cases = [
            c for c in cases
            if c["case_type"] == "citation_mismatch"
        ]

        assert len(mismatch_cases) >= 2

        for case in mismatch_cases:
            correct = set(case["expected_citations"])
            wrong = case.get("candidate_citations", [])
            available = (
                base_ids if case["corpus"] == "base"
                else expanded_scan["ids"]
            )

            assert correct
            assert wrong
            assert set(wrong).issubset(available)
            assert set(wrong).isdisjoint(correct), (
                f"{case['id']}: wrong citation overlaps gold"
            )

    def test_insufficient_context_no_citations(self, cases):
        selected = [
            c for c in cases
            if c["case_type"] == "insufficient_context"
        ]

        assert len(selected) >= 2

        for case in selected:
            assert case["expected_status"] == "insufficient_context"
            assert case["gold_chunk_ids"] == []
            assert case["expected_citations"] == []

    def test_vietnamese_encoding(self, cases):
        import re

        for case in cases:
            for field in ("question", "ground_truth"):
                value = case[field]

                assert value.strip(), (
                    f"{case['id']}: {field} is empty"
                )

                assert not re.search(
                    r"\?{2,}|[A-Za-zÀ-ỹ]\?[A-Za-zÀ-ỹ]|\?[A-Za-zÀ-ỹ]\?",
                    value
                ), (
                    f"{case['id']}: Possible encoding error in {field}"
                )        
      


