"""python -m team1_data.evaluation check | run --config <file.json> [--out DIR] [--run-id ID]"""

import argparse
import json
from pathlib import Path

from .core import CHUNKS, DEV_SET, ROOT, check_inputs, run


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("check", "run"):
        p = sub.add_parser(name)
        p.add_argument("--dev-set", type=Path, default=DEV_SET)
        p.add_argument("--chunks", type=Path, default=CHUNKS)
        if name == "run":
            p.add_argument("--config", type=Path, required=True, help="JSON: danh sách cấu hình")
            p.add_argument("--out", type=Path, default=ROOT / "evaluation/retrieval/runs")
            p.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.cmd == "check":
        print(json.dumps(check_inputs(args.dev_set, args.chunks), ensure_ascii=False, indent=1))
        return 0
    configs = json.loads(args.config.read_text(encoding="utf-8"))
    run_dir = run(configs, args.out, dev_set=args.dev_set, chunks_path=args.chunks, run_id=args.run_id)
    print((run_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"→ {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
