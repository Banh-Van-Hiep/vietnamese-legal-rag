"""Offline public SSE payload checks; no API, provider, or model calls."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
MAX_ID = 9_007_199_254_740_991
META_KEYS = ("conversationId", "clientRequestId", "userMessageId", "assistantMessageId", "createdAt")


def fail(message):
    raise ValueError(message)


def check_payload(schema, kind, value):
    """Check a normalized payload; never fix or trim an invalid value."""
    target = schema["query_uri"] if kind == "ChatRequest" else schema["stream_uri"] + f"#/$defs/{kind}"
    selected = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$ref": target}
    Draft202012Validator(selected, registry=schema["registry"], format_checker=FormatChecker()).validate(value)
    check_strings(value)
    # JSON Schema integer also accepts the mathematical value 1.0. The public
    # decoder requires an integer JSON token; do not silently accept a float ID.
    id_keys = ("conversationId",) if kind == "ChatRequest" else ()
    if kind in ("Meta", "Complete"):
        id_keys = ("conversationId", "userMessageId", "assistantMessageId")
    for key in id_keys:
        if value.get(key) is not None and type(value[key]) is not int:
            fail("public IDs must be integer JSON tokens")
    if kind in ("Meta", "Complete"):
        if value["userMessageId"] == value["assistantMessageId"]:
            fail("userMessageId and assistantMessageId must differ")
    if kind == "PublicCitation":
        check_source(value["sourceUrl"])
    if kind == "Complete":
        citations = value["citations"]
        mentions = list(dict.fromkeys(re.findall(r"\[C([0-9]+)\]", value["answer"])))
        expected = [str(i) for i in range(1, len(citations) + 1)]
        if mentions != expected:
            fail("answer markers must match C1..Cn in first-mention order")
        if {c["citationId"] for c in citations} != {f"C{i}" for i in expected}:
            fail("citation labels must be unique C1..Cn")
        if len({c["chunkId"] for c in citations}) != len(citations):
            fail("duplicate citation chunkId")
        for citation in citations:
            check_source(citation["sourceUrl"])


def check_strings(value):
    if isinstance(value, str) and unicodedata.normalize("NFC", value) != value:
        fail("text must use NFC")
    if isinstance(value, dict):
        for item in value.values():
            check_strings(item)
    elif isinstance(value, list):
        for item in value:
            check_strings(item)


def check_source(source):
    url = urlsplit(source)
    if url.scheme.lower() != "https" or not url.hostname:
        fail("sourceUrl must be HTTPS with a host")


def check_wire(schema, wire):
    """Check the four payloads exported by the existing Java HTTP test."""
    kinds = {"ChatRequest", "Meta", "Delta", "Complete"}
    if not isinstance(wire, dict) or set(wire) != kinds:
        fail("wire export must contain ChatRequest, Meta, Delta and Complete")
    for kind in sorted(kinds):
        check_payload(schema, kind, wire[kind])
    if any(wire["Meta"][key] != wire["Complete"][key] for key in META_KEYS):
        fail("meta/complete identity or timestamp binding mismatch")
    if wire["ChatRequest"]["clientRequestId"] != wire["Meta"]["clientRequestId"]:
        fail("request/meta clientRequestId mismatch")
    conv = wire["ChatRequest"].get("conversationId")
    if conv is not None and conv != wire["Meta"]["conversationId"]:
        fail("request/meta conversationId mismatch")
    # This file is a payload export, not a raw SSE transcript. Ordering, heartbeat
    # timing, delta budget, terminal count and network handling remain HTTP/FE tests.


def cases(schema, examples):
    rows = []

    def run(name, accepted, callback):
        message = None
        try:
            callback()
            actual = "ACCEPT"
        except (ValueError, ValidationError) as error:
            actual, message = "REJECT", str(error).splitlines()[0]
        expected = "ACCEPT" if accepted else "REJECT"
        rows.append(dict(name=name, expected=expected, actual=actual,
                         result="PASS" if actual == expected else "FAIL", detail=message))

    def payload(name, kind, value, accepted=True):
        run(name, accepted, lambda: check_payload(schema, kind, value))

    def changed(name, kind, key, value):
        item = deepcopy(examples[kind])
        item[key] = value
        payload(name, kind, item, False)

    for kind in ("ChatRequest", "Meta", "Delta", "Complete", "ErrorResponse"):
        payload(f"valid-{kind}", kind, examples[kind])
    payload("valid-insufficient", "Complete", examples["InsufficientComplete"])
    payload("valid-citation", "PublicCitation", examples["Complete"]["citations"][0])
    for name, conv in (("null", None), ("min", 1), ("max", MAX_ID)):
        item = {**examples["ChatRequest"], "conversationId": conv}
        payload(f"valid-conversation-{name}", "ChatRequest", item)
    for size in (1, 2000):
        payload(f"valid-question-{size}-codepoints", "ChatRequest",
                {**examples["ChatRequest"], "question": "😀" * size})
    payload("valid-empty-delta", "Delta", {"text": ""})
    bundle = {kind: examples[kind] for kind in ("ChatRequest", "Meta", "Delta", "Complete")}
    run("valid-wire-binding", True, lambda: check_wire(schema, bundle))
    for value in (0, -1, MAX_ID + 1, "101", 1.5, 1.0, True):
        changed(f"bad-conversation-{value!r}", "ChatRequest", "conversationId", value)
    for value in ("", "   ", "😀" * 2001, None, 123):
        changed(f"bad-question-type-or-length-{type(value).__name__}-{len(str(value))}",
                "ChatRequest", "question", value)
    changed("bad-question-NFD", "ChatRequest", "question", unicodedata.normalize("NFD", "Điều luật"))
    for name, value in (("version", "44444444-4444-1444-8444-444444444444"),
                        ("variant", "44444444-4444-4444-7444-444444444444"), ("syntax", "invalid")):
        changed(f"bad-uuid-{name}", "ChatRequest", "clientRequestId", value)
    for extra in ("history", "scenario", "model", "client_request_id"):
        changed(f"bad-extra-{extra}", "ChatRequest", extra, [])
    missing = deepcopy(examples["ChatRequest"])
    del missing["clientRequestId"]
    payload("bad-missing-clientRequestId", "ChatRequest", missing, False)
    for kind in ("Meta", "Complete"):
        changed(f"bad-{kind}-unsafe-id", kind, "assistantMessageId", MAX_ID + 1)
        changed(f"bad-{kind}-same-message-id", kind, "assistantMessageId", examples[kind]["userMessageId"])
        changed(f"bad-{kind}-non-UTC", kind, "createdAt", "2026-10-29T00:00:00+07:00")
        changed(f"bad-{kind}-date", kind, "createdAt", "2026-99-99T00:00:00Z")
    changed("bad-complete-extra", "Complete", "debug", {})
    changed("bad-complete-status", "Complete", "status", "out_of_scope")
    changed("bad-complete-empty-citations", "Complete", "citations", [])
    changed("bad-complete-too-many-citations", "Complete", "citations", examples["Complete"]["citations"] * 11)
    changed("bad-answer-too-long", "Complete", "answer", "😀" * 12001)
    changed("bad-answer-missing-marker", "Complete", "answer", "Nội dung mock không có marker.")
    changed("bad-answer-wrong-marker", "Complete", "answer", "Mock [C2].")
    two = deepcopy(examples["Complete"])
    two["citations"].append({**two["citations"][0], "citationId": "C2", "chunkId": "mock_v1__dieu-2__k1__0"})
    two["answer"] = "Mock [C1] và [C2]."
    payload("valid-two-citations", "Complete", two)
    for name, key, value in (("duplicate-chunk", "chunkId", two["citations"][0]["chunkId"]),
                             ("duplicate-label", "citationId", "C1")):
        bad = deepcopy(two)
        bad["citations"][1][key] = value
        payload(f"bad-citation-{name}", "Complete", bad, False)
    two["answer"] = "Mock [C2] trước [C1]."
    payload("bad-marker-first-mention-order", "Complete", two, False)
    for key in ("answer", "createdAt", "citations"):
        missing = deepcopy(examples["Complete"])
        del missing[key]
        payload(f"bad-complete-missing-{key}", "Complete", missing, False)
    for key, value in (("citationId", "C0"), ("documentId", "MOCK_v1"), ("articleId", "Điều 1"),
                       ("sourceUrl", "http://example.com/law"), ("sourceUrl", "https:///law"),
                       ("clause", ""), ("point", 1)):
        item = {**examples["Complete"]["citations"][0], key: value}
        payload(f"bad-citation-{key}-{value}", "PublicCitation", item, False)
    missing = deepcopy(examples["Complete"]["citations"][0])
    del missing["point"]
    payload("bad-citation-missing-nullable-key", "PublicCitation", missing, False)
    insufficient = deepcopy(examples["InsufficientComplete"])
    insufficient["answer"] = "Mock [C1]."
    payload("bad-insufficient-marker", "Complete", insufficient, False)
    insufficient["citations"] = examples["Complete"]["citations"]
    payload("bad-insufficient-citation", "Complete", insufficient, False)
    item = deepcopy(examples["ErrorResponse"])
    item["error"]["retryable"] = "true"
    payload("bad-error-retryable", "ErrorResponse", item, False)
    item = deepcopy(examples["ErrorResponse"])
    item["error"]["stackTrace"] = "mock"
    payload("bad-error-extra", "ErrorResponse", item, False)
    changed("bad-delta-type", "Delta", "text", 1)
    changed("bad-delta-too-long", "Delta", "text", "x" * 12001)
    for key in META_KEYS:
        wrong = deepcopy(bundle)
        wrong["Complete"][key] = {"conversationId": 102, "clientRequestId": "55555555-5555-4555-8555-555555555555",
                                  "userMessageId": 301, "assistantMessageId": 302,
                                  "createdAt": "2026-10-29T00:00:01Z"}[key]
        run(f"bad-binding-{key}", False, lambda wrong=wrong: check_wire(schema, wrong))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wire-file", type=Path, help="JSON payload export from StreamApiTests")
    parser.add_argument("--report-file", type=Path, help="optional local JSON evidence")
    args = parser.parse_args(argv)
    try:
        paths = [HERE / "query_request.schema.json", HERE / "chat_stream.schema.json"]
        documents = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
        for document in documents:
            Draft202012Validator.check_schema(document)
        registry = Registry().with_resources(
            (p.resolve().as_uri(), Resource.from_contents(document))
            for p, document in zip(paths, documents)
        )
        schema = {"query_uri": paths[0].resolve().as_uri(),
                  "stream_uri": paths[1].resolve().as_uri(), "registry": registry}
        examples = json.loads((HERE / "public_examples.json").read_text(encoding="utf-8"))
        rows = cases(schema, examples)
        wire_result = None
        if args.wire_file:
            check_wire(schema, json.loads(args.wire_file.read_text(encoding="utf-8")))
            wire_result = {"payloads": 4, "binding": "PASS"}
        report = {"schema_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  "total": len(rows), "passed": sum(r["result"] == "PASS" for r in rows),
                  "positive": sum(r["expected"] == "ACCEPT" for r in rows),
                  "negative": sum(r["expected"] == "REJECT" for r in rows),
                  "wire": wire_result, "cases": rows}
        if args.report_file:
            args.report_file.parent.mkdir(parents=True, exist_ok=True)
            args.report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k != "cases"}))
        for row in rows:
            if row["result"] == "FAIL":
                print(f"FAIL {row['name']}: expected {row['expected']}, actual {row['actual']}")
        return 0 if report["passed"] == report["total"] else 1
    except (OSError, ValueError, SchemaError, ValidationError) as error:
        print(f"ERROR: {error.__class__.__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
