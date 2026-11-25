"""VLRA-77: Re-run retrieval once to export complete raw top-20 results.

Run from the repository root:
    python scripts/vlra77_export_raw.py

This file does NOT modify team1_data/evaluation/core.py or existing evaluation files.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qdrant_client import QdrantClient  # noqa: E402

from scripts.eval_retrieval import validate_output  # noqa: E402
from team1_data.evaluation.core import (  # noqa: E402
    TOP_K,
    _Cache,
    build_retriever,
    canon_list,
    check_inputs,
    equivalence,
    rechunk,
    unit_of,
)
from team1_data.retrieval.common import DEFAULT_LEGAL_STATUS, load_chunks  # noqa: E402

TEST_SET = ROOT / 'team1_data/golden/test_set_v1.json'
CHUNKS = ROOT / 'data/doanh-nghiep/processed/chunks.jsonl'
CONFIG = ROOT / 'evaluation/retrieval/configs/vlra77_test.json'
RUN_DIR = ROOT / 'evaluation/retrieval/runs/vlra77'
OUTPUT = RUN_DIR / 'vlra77_raw_results.json'


def main() -> None:
    # Ensure this extra capture is associated with the ORIGINAL measured run.
    saved_run = json.loads((RUN_DIR / 'run.json').read_text(encoding='utf-8'))
    previous_file = RUN_DIR / 'hybrid_k60_aiteamvn_w0.5-1.json'
    previous = json.loads(previous_file.read_text(encoding='utf-8'))
    previous_rows = {c['id']: c for c in previous['cases']}
    configs = json.loads(CONFIG.read_text(encoding='utf-8'))
    if len(configs) != 1:
        raise ValueError('Expected exactly one config in vlra77_test.json')
    cfg = configs[0]
    if cfg != previous['config']:
        raise ValueError('Current config differs from the measured VLRA-77 config.')

    info = check_inputs(TEST_SET, CHUNKS)
    old_info = saved_run['inputs']
    for key in ('dev_set', 'corpus'):
        if info[key]['sha256'] != old_info[key]['sha256']:
            raise ValueError(f'{key} has changed since the original evaluation; raw results cannot be compared.')

    cases = json.loads(TEST_SET.read_text(encoding='utf-8'))
    base_chunks = [c for c in load_chunks(CHUNKS)
                   if c['legal_status'] in DEFAULT_LEGAL_STATUS]
    eq = equivalence(base_chunks)
    chunk_cfg = cfg.get('chunking', {})
    chunks = rechunk(base_chunks, chunk_cfg.get('size'), chunk_cfg.get('overlap', 0))
    corpus = {c['chunk_id']: c for c in chunks}

    # The original evaluation uses an in-memory Qdrant index, so it must be
    # rebuilt in this separate process. No production index is modified.
    client = QdrantClient(':memory:')
    try:
        retriever, _ = build_retriever(cfg, chunks, _Cache(), client)
        rows = []
        changed_top5 = []
        for pos, case in enumerate(cases, start=1):
            out = retriever.retrieve(case['question'], top_k=TOP_K)
            validate_output(out, case['question'], cfg['method'], corpus)
            raw = out['results']
            raw_ids = [r['chunk_id'] for r in raw]
            normalized_units = canon_list(raw_ids, lambda cid: eq.get(unit_of(cid), unit_of(cid)))
            previous_top5 = previous_rows[case['id']]['top5']
            same_top5 = normalized_units[:5] == previous_top5
            if not same_top5:
                changed_top5.append(case['id'])
            rows.append({
                'id': case['id'],
                'question': case['question'],
                'complexity': case.get('complexity'),
                'expected_status': case['expected_status'],
                'gold_chunk_ids': case['gold_chunk_ids'],
                'relevant_unit_groups': case.get('relevant_unit_groups', []),
                'top20_chunk_ids': raw_ids,
                'top5_raw_chunk_ids': raw_ids[:5],
                'source_metadata': [
                    {
                        'chunk_id': cid,
                        'legal_status': corpus[cid].get('legal_status'),
                        'issued_date': corpus[cid].get('issued_date'),
                        'effective_date': corpus[cid].get('effective_date'),
                    }
                    for cid in raw_ids
                ],
                'top5_normalized_units': normalized_units[:5],
                'top5_matches_original_run': same_top5,
                'raw_results': raw,
            })
            print(f'[{pos}/{len(cases)}] {case["id"]}', flush=True)
    finally:
        client.close()

    result = {
        'task': 'VLRA-77',
        'created_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'original_run_id': saved_run['run_id'],
        'original_run_head': saved_run.get('head'),
        'config': cfg,
        'test_set_sha256': info['dev_set']['sha256'],
        'corpus_sha256': info['corpus']['sha256'],
        'case_count': len(rows),
        'top5_changed_from_original_run': changed_top5,
        'note': 'Extra capture run using the same config and input hashes. Do not replace original metrics; top5 comparison flags any ranking drift.',
        'cases': rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    tmp.replace(OUTPUT)
    print(f'\nExported {len(rows)} cases to: {OUTPUT}')
    print(f'Changed normalized top-5 compared with original: {len(changed_top5)} cases')
    if changed_top5:
        print('IDs:', ', '.join(changed_top5))


if __name__ == '__main__':
    main()
