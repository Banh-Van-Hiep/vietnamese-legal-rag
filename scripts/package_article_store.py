from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / 'data' / 'doanh-nghiep' / 'processed' / 'articles.jsonl'
MANIFEST = ARTICLES.with_name('articles.manifest.json')
SCHEMA = ROOT / 'contracts' / 'v0.1' / 'internal_article.schema.json'
EXPECTED_ARTICLES = 635
EXPECTED_DOCUMENTS = 8


def examine_store() -> dict:
    if not ARTICLES.is_file():
        raise FileNotFoundError(f'Missing Article Store: {ARTICLES}')
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    validator = Draft202012Validator(schema)
    docs: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    count = 0

    with ARTICLES.open('r', encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                raise ValueError(f'Blank article at line {lineno}')
            try:
                article = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSON at line {lineno}: {exc}') from exc
            problems = list(validator.iter_errors(article))
            if problems:
                raise ValueError(f'Invalid contract at line {lineno}: {problems[0].message}')
            if not all(article[k].strip() for k in schema['required']):
                raise ValueError(f'Empty required string at line {lineno}')
            pair = (article['document_id'], article['article_id'])
            if pair in pairs:
                raise ValueError(f'Duplicate (document_id, article_id): {pair}')
            pairs.add(pair)
            docs.add(article['document_id'])
            count += 1

    if count != EXPECTED_ARTICLES or len(docs) != EXPECTED_DOCUMENTS:
        raise ValueError(f'Expected 635 articles / 8 documents; found {count} / {len(docs)}')

    digest = hashlib.sha256(ARTICLES.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return {
        'file': 'articles.jsonl',
        'schema': 'contracts/v0.1/internal_article.schema.json',
        'article_count': count,
        'document_count': len(docs),
        'sha256': digest,
    }


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write', action='store_true', help='Write/update manifest from actual store')
    group.add_argument('--check', action='store_true', help='Check manifest against actual store')
    parser.add_argument('--snapshot-date', help='ISO YYYY-MM-DD for --write (default: today)')
    args = parser.parse_args()

    actual = examine_store()
    if args.write:
        snapshot = args.snapshot_date or date.today().isoformat()
        date.fromisoformat(snapshot)
        actual['snapshot_date'] = snapshot
        MANIFEST.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(f'WROTE {MANIFEST} | articles={actual["article_count"]} sha256={actual["sha256"]}')
        return 0

    if not MANIFEST.is_file():
        raise FileNotFoundError(f'Missing manifest: {MANIFEST}; run --write')
    saved = json.loads(MANIFEST.read_text(encoding='utf-8'))
    for key, value in actual.items():
        if saved.get(key) != value:
            raise ValueError(f'Manifest mismatch in {key}: recorded={saved.get(key)!r}, current={value!r}')
    date.fromisoformat(saved['snapshot_date'])
    if set(saved) != set(actual) | {'snapshot_date'}:
        raise ValueError(f'Unexpected manifest fields: {set(saved) - (set(actual) | {"snapshot_date"})}')
    print(f'PASS | {actual["article_count"]} articles, {actual["document_count"]} docs, SHA256 verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
