"""Run the configured real Hybrid/BGE/LLM pipeline once, without FastAPI."""
import argparse
import json

from .runtime import build_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    args = parser.parse_args()
    runtime = build_runtime()
    try:
        print(json.dumps(runtime.pipeline.query(args.question, []), ensure_ascii=False, indent=2))
    finally:
        runtime.close()


if __name__ == "__main__":
    main()
