"""T3-15 pure validation/reporting; importing this module does not patch networking."""
from __future__ import annotations

import codecs
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unicodedata
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

PHASES = ('backend_init', 'ai_service', 'db_persist', 'stream_finish')
PUBLIC_ERRORS = {'INVALID_REQUEST', 'CONVERSATION_NOT_FOUND', 'DOCUMENT_NOT_FOUND', 'ARTICLE_NOT_FOUND',
                 'REQUEST_NOT_FOUND', 'REQUEST_IN_PROGRESS', 'CONVERSATION_BUSY', 'REQUEST_ID_CONFLICT',
                 'UPSTREAM_INVALID_RESPONSE', 'UPSTREAM_CONTRACT_ERROR', 'SERVICE_UNAVAILABLE',
                 'PERSISTENCE_UNAVAILABLE', 'PROCESSING_INTERRUPTED', 'UPSTREAM_TIMEOUT', 'INTERNAL_ERROR'}


class BenchmarkError(Exception):
    """Only constant codes cross into reports; response text can contain private data."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise BenchmarkError('DUPLICATE_JSON_KEY')
        value[key] = item
    return value


def strict_json(text):
    def invalid(_):
        raise BenchmarkError('NON_FINITE_JSON')
    try:
        return json.loads(text, object_pairs_hook=_unique, parse_constant=invalid)
    except (ValueError, TypeError) as exc:
        raise BenchmarkError('INVALID_JSON') from exc


def read_json(path):
    try:
        return strict_json(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError) as exc:
        raise BenchmarkError('INPUT_UNREADABLE') from exc


def digest(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError as exc:
        raise BenchmarkError('INPUT_UNREADABLE') from exc


def origin(value):
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/')):
            raise ValueError()
        host = parsed.hostname.lower()
        if ':' in host:
            host = '[' + host + ']'
        port = parsed.port
        suffix = '' if port is None or (parsed.scheme, port) in {('http', 80), ('https', 443)} else ':' + str(port)
        return parsed.scheme + '://' + host + suffix
    except (TypeError, ValueError) as exc:
        raise BenchmarkError('INVALID_ORIGIN') from exc


def load_dataset(path):
    rows = read_json(path)
    if not isinstance(rows, list) or not rows:
        raise BenchmarkError('EMPTY_DATASET')
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise BenchmarkError('INVALID_DATASET')
        for key in ('id', 'question'):
            value = row.get(key)
            if not isinstance(value, str) or not value.strip() or unicodedata.normalize('NFC', value) != value:
                raise BenchmarkError('INVALID_DATASET')
        if len(row['question']) > 2000 or row.get('split') == 'test':
            raise BenchmarkError('INVALID_DATASET')
        normalized = ' '.join(row['id'].casefold().split())
        if normalized in ids:
            raise BenchmarkError('DUPLICATE_SAMPLE_ID')
        ids.add(normalized)
    return rows


def validate_dev(path, rows, proof):
    try:
        if (proof['format_version'] != 1 or proof['status'] != 'split_only'
                or proof['input']['count'] != 150 or proof['outputs']['dev']['count'] != 90
                or proof['outputs']['test']['count'] != 60 or len(rows) != 90
                or proof['outputs']['dev']['sha256'] != digest(path)):
            raise BenchmarkError('INVALID_DEV_PROVENANCE')
        for row in rows:
            for key in ('ground_truth', 'citation', 'category', 'author'):
                value = row[key]
                if not isinstance(value, str) or not value.strip() or unicodedata.normalize('NFC', value) != value:
                    raise BenchmarkError('INVALID_DEV_DATASET')
            status = row['expected_status']; chunks = row['gold_chunk_ids']
            if (status not in ('answered', 'insufficient_context') or not isinstance(chunks, list)
                    or any(not isinstance(c, str) or not c.strip() or unicodedata.normalize('NFC', c) != c for c in chunks)
                    or len(chunks) != len(set(chunks))
                    or bool(chunks) != (status == 'answered') or row.get('split') == 'test'):
                raise BenchmarkError('INVALID_DEV_DATASET')
        counts = Counter(r['expected_status'] for r in rows)
        expected = {k: counts[k] for k in ('answered', 'insufficient_context')}
        if (proof['outputs']['dev']['status_counts'] != expected
                or any(type(v) is not int for v in proof['outputs']['dev']['status_counts'].values())):
            raise BenchmarkError('INVALID_DEV_PROVENANCE')
    except (KeyError, TypeError) as exc:
        raise BenchmarkError('INVALID_DEV_PROVENANCE') from exc


class PublicContract:
    def __init__(self, root):
        folder = Path(root) / 'contracts/v0.1'
        spec = importlib.util.spec_from_file_location('latency_public_contract', folder / 'validate_public_contract.py')
        self.helpers = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.helpers)
        paths = [folder/'query_request.schema.json', folder/'chat_stream.schema.json']
        registry = Registry().with_resources((p.resolve().as_uri(), Resource.from_contents(read_json(p))) for p in paths)
        self.schema = {'query_uri':paths[0].resolve().as_uri(), 'stream_uri':paths[1].resolve().as_uri(), 'registry':registry}
        article = read_json(folder/'internal_article.schema.json')
        names = {'document_id':'documentId','document_title':'documentTitle','article_id':'articleId','source_url':'sourceUrl'}
        article['properties'] = {names.get(k,k):v for k,v in article['properties'].items()}
        article['required'] = [names.get(k,k) for k in article['required']]
        self.article_validator = Draft202012Validator(article, format_checker=FormatChecker())

    def validate(self, kind, value):
        try:
            self.helpers.check_payload(self.schema, kind, value)
        except Exception as exc:
            raise BenchmarkError('INVALID_PUBLIC_RESPONSE') from exc

    def article(self, value, document_id, article_id):
        try:
            self.article_validator.validate(value)
            self.helpers.check_strings(value)
            self.helpers.check_source(value['sourceUrl'])
            if value['documentId'] != document_id or value['articleId'] != article_id:
                raise ValueError()
        except Exception as exc:
            raise BenchmarkError('INVALID_ARTICLE_RESPONSE') from exc


def read_sse(chunks, request, contract):
    decoder = codecs.getincrementaldecoder('utf-8')('strict')
    buffer = ''; event = ''; data = []; meta = None; deltas = []; delta_size = 0; size = 0
    try:
        for chunk in chunks:
            size += len(chunk)
            if size > 2_000_000:
                raise BenchmarkError('RESPONSE_TOO_LARGE')
            buffer += decoder.decode(chunk)
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.removesuffix('\r')
                if line.startswith(':'):
                    continue
                if line:
                    key, _, value = line.partition(':')
                    value = value[1:] if value.startswith(' ') else value
                    if key == 'event': event = value
                    elif key == 'data': data.append(value)
                    continue
                if not data:
                    event = ''; continue
                value = strict_json('\n'.join(data)); data = []
                kind, event = event, ''
                if kind == 'error':
                    contract.validate('ErrorResponse', value)
                    code = value['error']['code']
                    raise BenchmarkError(code if code in PUBLIC_ERRORS else 'UNRECOGNIZED_PUBLIC_ERROR')
                if kind == 'meta' and meta is None:
                    contract.validate('Meta', value)
                    if (value['clientRequestId'] != request['clientRequestId']
                            or request.get('conversationId') not in (None, value['conversationId'])):
                        raise BenchmarkError('INVALID_STREAM')
                    meta = value
                elif kind == 'delta' and meta is not None:
                    contract.validate('Delta', value)
                    delta_size += len(value['text'])
                    if delta_size > 12000: raise BenchmarkError('INVALID_STREAM')
                    deltas.append(value['text'])
                elif kind == 'complete' and meta is not None:
                    contract.validate('Complete', value)
                    if (any(value[k] != meta[k] for k in contract.helpers.META_KEYS)
                            or (value['status'] == 'answered' and ''.join(deltas) != value['answer'])
                            or (value['status'] == 'insufficient_context' and deltas)):
                        raise BenchmarkError('INVALID_STREAM')
                    return value
                else:
                    raise BenchmarkError('INVALID_STREAM')
        decoder.decode(b'', final=True)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise BenchmarkError('INVALID_STREAM') from exc
    raise BenchmarkError('TRUNCATED_STREAM')


def distribution(values):
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in values):
        raise BenchmarkError('INVALID_DURATION')
    ordered = sorted(values)
    result = {'samples':len(ordered), 'min':ordered[0]/1000 if ordered else None,
              'max':ordered[-1]/1000 if ordered else None}
    result.update({name:ordered[math.ceil(len(ordered)*p)-1]/1000 if ordered else None
                   for name,p in [('p50',.5),('p90',.9),('p95',.95),('p99',.99)]})
    return result


def _duration(v):
    return type(v) in (int, float) and math.isfinite(v) and v >= 0


def load_timings(path, traces):
    if path is None or not Path(path).exists(): return {}
    found = {}
    try:
        with Path(path).open('rb') as stream:
            stream.seek(0, 2); length = stream.tell(); stream.seek(max(0, length-64*1024*1024))
            lines = stream.read().decode('utf-8', errors='replace').splitlines()
        for line in lines:
            if 'CHAT_LATENCY ' not in line: continue
            raw = line.split('CHAT_LATENCY ', 1)[1]
            try: row = strict_json(raw)
            except BenchmarkError: continue
            if not isinstance(row, dict) or not isinstance(row.get('trace_id'), str) or row['trace_id'] not in traces: continue
            trace = row['trace_id']
            if trace in found:
                found[trace] = {'error':'DUPLICATE_TIMING'}; continue
            phases = row.get('phases_ms')
            if (row.get('kind') != 'chat' or not isinstance(phases, dict)
                    or set(phases) != set(PHASES) or not _duration(row.get('total_ms'))
                    or any(v is not None and not _duration(v) for v in phases.values())
                    or sum(v for v in phases.values() if v is not None) > row['total_ms'] + .001):
                found[trace] = {'error':'INVALID_TIMING'}; continue
            try: upstream = origin(row.get('upstream_origin'))
            except BenchmarkError:
                found[trace] = {'error':'INVALID_TIMING'}; continue
            found[trace] = {'trace_id':trace, 'client_request_id':row.get('client_request_id'),
                            'outcome':row.get('outcome'), 'upstream_origin':upstream,
                            'phases_ms':phases, 'total_ms':row['total_ms'],
                            'transport_connected':row.get('transport_connected') is True}
    except OSError:
        return {}
    return found


def write_report(path, report):
    path = Path(path)
    try:
        payload = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    except (TypeError, ValueError) as exc:
        raise BenchmarkError('INVALID_REPORT') from exc
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            try: stream.write(payload)
            except BaseException:
                stream.close(); path.unlink(missing_ok=True); raise
    except OSError as exc:
        raise BenchmarkError('OUTPUT_UNAVAILABLE') from exc
