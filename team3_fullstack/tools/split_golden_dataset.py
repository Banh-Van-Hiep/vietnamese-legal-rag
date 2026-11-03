"""Split the externally reviewed 150-record Golden set into 90 Dev / 60 Test.

Standard-library-only Team 3 tool. It never edits source records, generates legal
answers, validates legal applicability, or claims that a dataset is frozen.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys
import unicodedata

TOTAL = 150
DEV_SIZE = 90
DEFAULT_SEED = 20261029
STATUSES = ("answered", "insufficient_context")
TEXT_FIELDS = ("id", "question", "expected_status", "ground_truth", "citation", "category", "author")
FILENAMES = ("golden_dataset_v1.dev.json", "golden_dataset_v1.test.json", "golden_dataset_v1.split.json")


class SplitError(ValueError):
    """Invalid input or unsafe output operation; no release should be produced."""


def normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def validate_records(records: object) -> None:
    if not isinstance(records, list) or len(records) != TOTAL:
        count = len(records) if isinstance(records, list) else "not an array"
        raise SplitError(f"Expected exactly {TOTAL} records; received {count}.")
    ids, questions = set(), set()
    for index, row in enumerate(records, 1):
        label = f"Record {index}"
        if not isinstance(row, dict):
            raise SplitError(f"{label}: expected an object.")
        for key in TEXT_FIELDS:
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise SplitError(f"{label}: {key} must be a nonempty string.")
            if not unicodedata.is_normalized("NFC", row[key]):
                raise SplitError(f"{label}: {key} must be NFC; the source is not auto-corrected.")
        for field, seen in (("id", ids), ("question", questions)):
            value = normalized(row[field])
            if value in seen:
                raise SplitError(f"{label}: duplicate normalized {field}.")
            seen.add(value)
        status, chunks = row["expected_status"], row.get("gold_chunk_ids")
        if status not in STATUSES:
            raise SplitError(f"{label}: invalid expected_status.")
        if not isinstance(chunks, list) or any(not isinstance(x, str) or not x.strip() for x in chunks):
            raise SplitError(f"{label}: gold_chunk_ids must be a list of nonempty strings.")
        if len(chunks) != len(set(chunks)):
            raise SplitError(f"{label}: duplicate chunk IDs.")
        if bool(chunks) != (status == "answered"):
            raise SplitError(f"{label}: chunk IDs disagree with expected_status.")


def counts(records: list[dict]) -> dict[str, int]:
    found = Counter(row["expected_status"] for row in records)
    return {status: found[status] for status in STATUSES}


def _check_partition(source: list[dict], dev: list[dict], test: list[dict]) -> None:
    if len(dev) != DEV_SIZE or len(test) != TOTAL - DEV_SIZE:
        raise SplitError("Internal partition size mismatch.")
    original = {row["id"]: row for row in source}
    dev_ids, test_ids = {row["id"] for row in dev}, {row["id"] for row in test}
    if dev_ids & test_ids or dev_ids | test_ids != set(original):
        raise SplitError("Internal partition contains missing or overlapping IDs.")
    if any(row != original.get(row["id"]) for row in dev + test):
        raise SplitError("Internal partition changed a source record.")


def split_records(records: list[dict], seed: int = DEFAULT_SEED) -> tuple[list[dict], list[dict]]:
    validate_records(records)
    if type(seed) is not int:
        raise SplitError("Seed must be an integer.")
    distribution = counts(records)
    allocation = {s: distribution[s] * DEV_SIZE // TOTAL for s in STATUSES}
    remaining = DEV_SIZE - sum(allocation.values())
    order = sorted(STATUSES, key=lambda s: (-(distribution[s] * DEV_SIZE % TOTAL), s))
    for status in order[:remaining]:
        allocation[status] += 1
    rng = random.Random(seed)
    dev, test = [], []
    for status in STATUSES:
        group = sorted((row for row in records if row["expected_status"] == status), key=lambda row: row["id"])
        rng.shuffle(group)
        boundary = allocation[status]
        dev.extend(group[:boundary])
        test.extend(group[boundary:])
    rng.shuffle(dev)
    rng.shuffle(test)
    _check_partition(records, dev, test)
    return dev, test


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise SplitError("Duplicate JSON object key in source.")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise SplitError("Non-finite JSON number in source.")


def write_split(input_path: Path, output_dir: Path, seed: int = DEFAULT_SEED) -> dict:
    source_bytes = input_path.read_bytes()
    records = json.loads(source_bytes.decode("utf-8-sig"), object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    dev, test = split_records(records, seed)
    dev_bytes, test_bytes = _json_bytes(dev), _json_bytes(test)
    digest = lambda value: hashlib.sha256(value).hexdigest()
    distribution = counts(records)
    warnings = []
    if any(distribution[s] == 0 for s in STATUSES):
        warnings.append("Input does not contain both statuses; upstream review owns the dataset mix.")
    if any(distribution[s] == 1 for s in STATUSES):
        warnings.append("A singleton stratum cannot be present in both splits without duplication.")
    report = {
        "format_version": 1,
        "status": "split_only",
        "input": {"file": input_path.name, "sha256": digest(source_bytes), "count": TOTAL, "status_counts": distribution},
        "split": {"seed": seed, "stratify_by": "expected_status", "algorithm": "largest_remainder_then_seeded_shuffle"},
        "outputs": {
            "dev": {"file": FILENAMES[0], "sha256": digest(dev_bytes), "count": len(dev), "status_counts": counts(dev)},
            "test": {"file": FILENAMES[1], "sha256": digest(test_bytes), "count": len(test), "status_counts": counts(test)},
        },
        "warnings": warnings,
        "review_and_freeze": "Not asserted by this tool; input review belongs to the contributing teams.",
    }
    payloads = (dev_bytes, test_bytes, _json_bytes(report))
    targets = [output_dir / name for name in FILENAMES]
    if any(target.exists() for target in targets):
        raise SplitError("Output already exists; choose a new output directory. No files were overwritten.")
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for target, payload in zip(targets, payloads):
            with target.open("xb") as handle:
                created.append(target)
                handle.write(payload)
    except BaseException:
        for target in reversed(created):
            target.unlink()
        raise
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="150 records provided by Team 1 and reviewed by Team 2")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args(argv)
    try:
        report = write_split(args.input, args.output_dir, args.seed)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"Split rejected: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
