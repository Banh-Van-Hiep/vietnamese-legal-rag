"""Offline checks for Week 1 documentation fixtures; no RAG/model/API calls."""
import copy
import json
import math
import re
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import ValidationError
    from referencing import Registry, Resource
except ImportError as exc:
    raise SystemExit("Dev check requires jsonschema: python -m pip install jsonschema==4.25.1") from exc

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/team2_rag"
CONTRACT = ROOT / "contracts/v0.1"
REGISTRY = Registry()
for path in list(CONTRACT.glob("*.json")) + list((DOCS / "schemas").glob("*.json")):
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    REGISTRY = REGISTRY.with_resource(path.as_uri(), Resource.from_contents(schema))


def validate(value, path):
    Draft202012Validator(
        {"$ref": path.as_uri()}, registry=REGISTRY, format_checker=FormatChecker()
    ).validate(value)


def fixture(name):
    return json.loads((DOCS / "examples" / name).read_text(encoding="utf-8"))


def check_retrieval(value):
    validate(value, CONTRACT / "retrieval_output.schema.json")
    rows = value["results"]
    if [row["rank"] for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("Ranks must be consecutive from 1")
    if len({row["chunk_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate chunk_id")
    if any(not math.isfinite(row["score"]) for row in rows):
        raise ValueError("Non-finite score")


def check_response(value, context):
    validate(value, CONTRACT / "rag_response.schema.json")
    citations = value["citations"]
    ids = [citation["citation_id"] for citation in citations]
    chunks = [citation["chunk_id"] for citation in citations]
    # Detect malformed C-markers too, not only schema-permitted C1..C10.
    markers = set(re.findall(r"\[(C[^\]\s]*)\]", value["answer"]))
    if len(set(ids)) != len(ids) or len(set(chunks)) != len(chunks):
        raise ValueError("Duplicate citation ID or chunk")
    if markers != set(ids):
        raise ValueError("Marker/citation mismatch")
    rows = {row["chunk_id"]: row for row in context}
    for citation in citations:
        source = rows.get(citation["chunk_id"])
        if source is None:
            raise ValueError("Citation outside packed context")
        if any(source[key] != val for key, val in citation.items() if key != "citation_id"):
            raise ValueError("Citation metadata does not match source")


cases = [
    ("query_request.json", "query_request.schema.json", "request.schema.json"),
    ("retrieval_output.json", "retrieval_output.schema.json", "retrieval_output.schema.json"),
    ("rag_answered.json", "rag_response.schema.json", "rag_response.schema.json"),
    ("rag_insufficient.json", "rag_response.schema.json", "rag_response.schema.json"),
    ("error_response.json", "error_response.schema.json", "error_response.schema.json"),
]
for name, canonical, alias in cases:
    value = fixture(name)
    validate(value, CONTRACT / canonical)
    validate(value, DOCS / "schemas" / alias)

retrieval = fixture("retrieval_output.json")
answered = fixture("rag_answered.json")
insufficient = fixture("rag_insufficient.json")
check_retrieval(retrieval)
check_response(answered, retrieval["results"])
check_response(insufficient, [])
validate(answered["citations"][0], DOCS / "schemas/citation.schema.json")


def reject(check, original, mutate):
    value = copy.deepcopy(original)
    mutate(value)
    try:
        check(value)
    except (ValidationError, ValueError):
        return
    raise AssertionError("Invalid fixture was accepted")


request = fixture("query_request.json")
request_check = lambda value: validate(value, CONTRACT / "query_request.schema.json")
response_check = lambda value: check_response(value, retrieval["results"])
reject(request_check, request, lambda v: v.pop("client_request_id"))
reject(request_check, request, lambda v: v.update(client_request_id="not-a-uuid"))
reject(request_check, request, lambda v: v.update(question="   "))
reject(request_check, request, lambda v: v.update(history=[]))
reject(check_retrieval, retrieval, lambda v: v["results"][0].pop("point"))
reject(check_retrieval, retrieval, lambda v: v["results"][0].update(rank=2))
reject(check_retrieval, retrieval, lambda v: v["results"].append(copy.deepcopy(v["results"][0])))
reject(check_retrieval, retrieval, lambda v: v["results"][0].update(score=float("inf")))
reject(check_retrieval, retrieval, lambda v: v["results"][0].update(retrieval_method="rrf"))
reject(response_check, answered, lambda v: v.update(citations=[]))
reject(response_check, answered, lambda v: v.update(status="out_of_scope"))
reject(response_check, answered, lambda v: v.update(answer="Mock [C2]."))
reject(response_check, answered, lambda v: v.update(answer="Mock [C11]."))
reject(response_check, answered, lambda v: v["citations"][0].update(chunk_id="unknown"))
reject(response_check, answered, lambda v: v["citations"][0].update(article="Điều khác"))
reject(response_check, answered, lambda v: v["citations"].append(copy.deepcopy(v["citations"][0])))
reject(response_check, insufficient, lambda v: v.update(answer="Mock [C1]."))

print("OK: schema metaschemas; 5 fixtures against canonical + aliases; citation alias")
print("OK: retrieval/provenance checks; 17 invalid cases rejected")
print("Design checks only: no legal accuracy, model, integration or performance claim")
