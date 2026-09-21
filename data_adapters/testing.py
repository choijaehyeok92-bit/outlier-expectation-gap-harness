"""Offline transports for the adapters.

A provider that can only be exercised against a live regulator is a provider
that never gets tested. Both adapters take `transport=`, and these serve
recorded payloads from disk instead, so the whole ingestion path — resolution,
period arithmetic, account mapping, consolidation choice, pack assembly — runs
in a unit test with no network and no API key.

`RecordingTransport` wraps a real transport and writes what came back, which is
how a fixture directory gets refreshed once someone has credentials and egress.
"""
import json
import re
import urllib.parse
from pathlib import Path


class FixtureMissing(RuntimeError):
    pass


def fixture_key(url: str) -> str:
    """A stable filename for a URL: endpoint plus the query that identifies it.

    Secrets never reach a filename — `crtfc_key` is dropped before the key is
    built, so a recorded fixture cannot leak an API key into the repository.
    """
    parsed = urllib.parse.urlparse(url)
    # The whole path, not just its last segment: EDGAR serves
    # `submissions/CIK0000789019.json` and `api/xbrl/companyfacts/CIK0000789019.json`,
    # which share a filename and are entirely different documents.
    endpoint = parsed.path.strip('/').replace('/', '__') or 'root'
    params = urllib.parse.parse_qs(parsed.query)
    params.pop('crtfc_key', None)
    parts = [endpoint]
    for name in sorted(params):
        value = ','.join(params[name])
        parts.append(f'{name}={value}')
    key = '__'.join(parts)
    return re.sub(r'[^A-Za-z0-9._=,\-]+', '_', key)[:180]


class FixtureTransport:
    """Serve recorded payloads. Unknown requests fail loudly rather than empty."""

    offline = True

    def __init__(self, root, extra=None, default=None):
        self.root = Path(root)
        self.extra = dict(extra or {})
        self.default = default
        self.calls: list = []

    def __call__(self, url: str, headers: dict) -> bytes:
        key = fixture_key(url)
        self.calls.append(key)
        if key in self.extra:
            payload = self.extra[key]
            return payload if isinstance(payload, bytes) else \
                json.dumps(payload, ensure_ascii=False).encode('utf-8')
        for suffix in ('.json', '.xml', '.zip', '.bin'):
            candidate = self.root / f'{key}{suffix}'
            if candidate.exists():
                return candidate.read_bytes()
        if self.default is not None:
            return self.default if isinstance(self.default, bytes) else \
                json.dumps(self.default, ensure_ascii=False).encode('utf-8')
        raise FixtureMissing(f'no fixture for {key} (from {url})')


class RecordingTransport:
    """Pass through to a real transport and save each response for replay."""

    def __init__(self, root, inner=None):
        from .http import urllib_transport
        self.root = Path(root)
        self.inner = inner or urllib_transport

    def __call__(self, url: str, headers: dict) -> bytes:
        payload = self.inner(url, headers)
        self.root.mkdir(parents=True, exist_ok=True)
        suffix = '.json' if payload[:1] in (b'{', b'[') else (
            '.zip' if payload[:2] == b'PK' else ('.xml' if payload[:1] == b'<' else '.bin'))
        (self.root / f'{fixture_key(url)}{suffix}').write_bytes(payload)
        return payload
