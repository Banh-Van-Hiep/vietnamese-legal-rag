"""Check public schema against actual wire payloads exported by StreamApiTests."""
import argparse
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

parser = argparse.ArgumentParser()
parser.add_argument("--examples", type=Path, default=Path(
    "team3_fullstack/backend/target/vlra41-contract-examples.json"))
args = parser.parse_args()
schema = json.loads(Path(__file__).with_name("chat-v2.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
examples = json.loads(args.examples.read_text(encoding="utf-8"))
for name in ("ChatRequest", "Meta", "Delta", "Complete"):
    Draft202012Validator({"$ref": "#/$defs/" + name, "$defs": schema["$defs"]},
                        format_checker=FormatChecker()).validate(examples[name])
    print(f"{name}: PASS")
validator = Draft202012Validator({"$ref": "#/$defs/ChatRequest", "$defs": schema["$defs"]},
                                format_checker=FormatChecker())
for invalid in (dict(examples["ChatRequest"], conversationId="1"),
                dict(examples["ChatRequest"], history=[]),
                dict(examples["ChatRequest"], clientRequestId="44444444-4444-1444-8444-444444444444")):
    assert not validator.is_valid(invalid), "Invalid request accepted by schema"
print("Negative examples: 3 PASS")
