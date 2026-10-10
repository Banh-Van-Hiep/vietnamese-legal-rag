"""Run a local mock demo: python -m team2_rag."""

import argparse
import json

from .service import query


def main() -> None:
    parser = argparse.ArgumentParser(description="Team 2 RAG mock demo (no LLM API)")
    parser.add_argument("--question", default="Câu hỏi dùng để kiểm thử")
    parser.add_argument("--scenario", choices=["answered", "insufficient_context"], default="answered")
    args = parser.parse_args()
    print(json.dumps(query(args.question, [], scenario=args.scenario), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
