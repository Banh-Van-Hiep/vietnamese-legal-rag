import hashlib
import json
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / 'data/doanh-nghiep/processed/articles.jsonl'
MANIFEST = ROOT / 'data/doanh-nghiep/processed/articles.manifest.json'
SCHEMA = ROOT / 'contracts/v0.1/internal_article.schema.json'


def test_manifest_matches_store():
    assert ARTICLES.is_file(), f'Missing {ARTICLES}'
    assert MANIFEST.is_file(), 'Run: python scripts/package_article_store.py --write'
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert manifest['file'] == 'articles.jsonl'
    assert manifest['schema'] == 'contracts/v0.1/internal_article.schema.json'
    assert manifest['sha256'] == hashlib.sha256(ARTICLES.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    date.fromisoformat(manifest['snapshot_date'])

    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    validator = Draft202012Validator(schema)
    keys = set()
    docs = set()
    count = 0
    with ARTICLES.open('r', encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            assert line.strip(), f'Blank article line {lineno}'
            record = json.loads(line)
            validator.validate(record)
            pair = (record['document_id'], record['article_id'])
            assert pair not in keys, f'Duplicate article key: {pair}'
            keys.add(pair)
            docs.add(record['document_id'])
            count += 1

    assert manifest['article_count'] == count == 635
    assert manifest['document_count'] == len(docs) == 8
