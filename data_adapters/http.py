"""Shared HTTP transport for the adapters.

Three things live here so no individual adapter has to remember them:

1. **Rate limits are the regulator's rule, not a suggestion.** SEC fair access
   asks for no more than ten requests a second and a contact in the User-Agent;
   OpenDART meters by key. Spacing is enforced per host.
2. **Failures reach the caller as one exception type** with a message meant for
   an operator, not a stack trace — the same contract `harness_core/fetch.py`
   already uses.
3. **The transport is injectable.** Every provider takes `transport=` and the
   tests pass a recorded one, so the whole pipeline runs offline and
   deterministically. A provider that could only be exercised against a live
   regulator would never be tested at all.
"""
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from typing import Callable, Optional

Transport = Callable[[str, dict], bytes]


class TransportError(RuntimeError):
    """A retrieval failure phrased for the operator."""


class RateLimiter:
    """Minimum spacing between requests, per host."""

    def __init__(self, spacing_seconds: float = 0.15, sleep=time.sleep):
        self.spacing = float(spacing_seconds)
        self._sleep = sleep
        self._last: dict = {}

    def wait(self, host: str) -> None:
        if self.spacing <= 0:
            return
        previous = self._last.get(host)
        now = time.monotonic()
        if previous is not None:
            remaining = self.spacing - (now - previous)
            if remaining > 0:
                self._sleep(remaining)
                now = time.monotonic()
        self._last[host] = now


def _decode(payload: bytes, encoding: str) -> bytes:
    encoding = (encoding or '').lower()
    if encoding == 'gzip':
        return gzip.decompress(payload)
    if encoding == 'deflate':
        return zlib.decompress(payload)
    return payload


def urllib_transport(url: str, headers: dict, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            header_bag = getattr(response, 'headers', None)
            return _decode(raw, (header_bag.get('Content-Encoding') if header_bag else '') or '')
    except urllib.error.HTTPError as error:
        raise TransportError(f'{url} -> HTTP {error.code}') from error
    except Exception as error:                   # blocked egress, DNS, TLS, timeout
        raise TransportError(f'{url} -> {type(error).__name__}: {error}') from error


class HttpClient:
    """A small client the adapters share. `transport` is what tests replace."""

    def __init__(self, user_agent: str, transport: Optional[Transport] = None,
                 spacing_seconds: float = 0.15, extra_headers: Optional[dict] = None):
        self.user_agent = user_agent
        self.transport = transport or urllib_transport
        self.limiter = RateLimiter(spacing_seconds)
        self.extra_headers = dict(extra_headers or {})

    def build_url(self, url: str, params: Optional[dict] = None) -> str:
        if not params:
            return url
        clean = {k: v for k, v in params.items() if v is not None}
        separator = '&' if '?' in url else '?'
        return f'{url}{separator}{urllib.parse.urlencode(clean)}'

    def get(self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> bytes:
        target = self.build_url(url, params)
        # Spacing exists to be polite to a remote host. A transport that marks
        # itself offline is reading a local file and has nobody to be polite to.
        if not getattr(self.transport, 'offline', False):
            self.limiter.wait(urllib.parse.urlparse(target).netloc)
        merged = {'User-Agent': self.user_agent, 'Accept-Encoding': 'identity',
                  **self.extra_headers, **(headers or {})}
        try:
            return self.transport(target, merged)
        except TransportError:
            raise
        except Exception as error:
            # An injected transport may raise anything; callers are promised one type.
            raise TransportError(f'{target} -> {type(error).__name__}: {error}') from error

    def get_json(self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None):
        raw = self.get(url, params, headers)
        try:
            return json.loads(raw)
        except ValueError as error:
            raise TransportError(f'{self.build_url(url, params)} -> response was not JSON ({error})') from error
