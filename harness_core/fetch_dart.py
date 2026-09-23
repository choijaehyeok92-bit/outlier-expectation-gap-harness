"""Stage 0 acquisition for Korean issuers: primary filings from OpenDART (금융감독원 전자공시).

The DART counterpart of fetch.py, under the same two rules: nothing received
after the run's as_of_date is downloaded, and nothing is invented — a missing
filing is a shortfall, not a guess. It resolves a KRX stock code to a DART
corp_code, lists filings in a window ending at the cutoff, picks the ones the
intake checklist asks for (`dart_reports` in config/intake.json) and saves the
original documents under sources/ with Korean report names in the file name, so
intake's existing `source_regex` rules recognize them.

The API key is a credential: it is read from the caller (flag or OPENDART_API_KEY)
and never written to disk — every URL recorded in the manifest has it removed.
"""
import io
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta

from .fetch import FetchError

API = 'https://opendart.fss.or.kr/api/'
REQUEST_SPACING_SECONDS = 0.1
LOOKBACK_YEARS = 4
TAG = re.compile(r'^\s*(\[[^\]]*\]\s*)+')           # [기재정정], [첨부추가] ...
PERIOD = re.compile(r'\((\d{4}\.\d{2})\)')


def stock_code_of(run_id):
    """KRX six-digit code from a run id such as 000660, 000660.KS or 000660-2026-09-22."""
    match = re.match(r'^(\d{6})(?:\.(?:KS|KQ))?(?:$|-)', str(run_id).upper())
    return match.group(1) if match else None


def redact(url):
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if k != 'crtfc_key']
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def _open(url, timeout=60):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'harness-stage0'}),
                                timeout=timeout) as response:
        return response.read()


def _read(endpoint, params, key, opener=None):
    url = API + endpoint + '?' + urllib.parse.urlencode({'crtfc_key': key, **params})
    try:
        payload = (opener or _open)(url)
    except urllib.error.HTTPError as error:
        raise FetchError(f'{redact(url)} -> HTTP {error.code}') from error
    except FetchError:
        raise
    except Exception as error:                       # blocked egress, DNS, TLS, timeout
        raise FetchError(f'{redact(url)} -> {type(error).__name__}: {error}') from error
    time.sleep(REQUEST_SPACING_SECONDS)
    return payload, redact(url)


def _api_error(payload):
    """DART answers errors as a small JSON/XML body with a status code instead of HTTP errors."""
    head = payload[:400].decode('utf-8', 'replace')
    match = re.search(r'"?status"?\s*[:>]\s*"?(\d{3})', head)
    message = re.search(r'"?message"?\s*[:>]\s*"?([^"<]+)', head)
    if match and match.group(1) != '000':
        return f"DART status {match.group(1)}: {message.group(1).strip() if message else ''}"
    return None


def resolve_corp_code(stock_code, key, opener=None):
    payload, _ = _read('corpCode.xml', {}, key, opener)
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile:
        raise FetchError(_api_error(payload) or 'corpCode.xml was not a zip archive')
    root = ET.fromstring(archive.read(archive.namelist()[0]))
    for row in root.iter('list'):
        if (row.findtext('stock_code') or '').strip() == stock_code:
            return row.findtext('corp_code').strip(), (row.findtext('corp_name') or '').strip()
    raise FetchError(f'{stock_code} is not a listed company in the DART corp code index')


def list_filings(corp_code, as_of_date, key, opener=None, years=LOOKBACK_YEARS):
    """Every filing received in [as_of - years, as_of], newest first."""
    end = date.fromisoformat(as_of_date)
    start = end - timedelta(days=365 * years + 1)
    rows, page = [], 1
    while True:
        payload, _ = _read('list.json', {'corp_code': corp_code, 'bgn_de': start.strftime('%Y%m%d'),
                                         'end_de': end.strftime('%Y%m%d'), 'page_no': page, 'page_count': 100},
                           key, opener)
        data = json.loads(payload)
        if data.get('status') == '013':              # no filings in the window
            break
        if data.get('status') != '000':
            raise FetchError(f"DART list.json status {data.get('status')}: {data.get('message')}")
        rows += data.get('list') or []
        if page >= int(data.get('total_page') or 1):
            break
        page += 1
    for row in rows:
        received = row.get('rcept_dt') or ''
        row['filing_date'] = f'{received[:4]}-{received[4:6]}-{received[6:8]}' if len(received) == 8 else None
        row['report_base'] = TAG.sub('', row.get('report_nm') or '').strip()
        period = PERIOD.search(row['report_base'])
        row['period'] = period.group(1) if period else None
    rows.sort(key=lambda r: (r['filing_date'] or '', r.get('rcept_no') or ''), reverse=True)
    return rows


def plan(rows, policy, as_of_date):
    """Filings to download per requirement. An amended report replaces the original of the same period."""
    eligible = [r for r in rows if r.get('filing_date') and r['filing_date'] <= as_of_date]
    excluded = len(rows) - len(eligible)
    wanted, seen = [], set()
    for requirement in policy['requirements']:
        names = requirement.get('dart_reports') or []
        if not names:
            continue
        needed = int(requirement.get('min_count', 1))
        picked, periods = [], set()
        for row in eligible:
            if not any(row['report_base'].startswith(n) for n in names):
                continue
            period_key = (row['report_base'].split('(')[0].strip(), row.get('period')) if row.get('period') else row['rcept_no']
            if period_key in periods:
                continue                              # newest filing of a period wins (amendments are newer)
            periods.add(period_key)
            picked.append(row)
            if len(picked) == needed:
                break
        for row in picked:
            if row['rcept_no'] in seen:
                continue
            seen.add(row['rcept_no'])
            wanted.append({**row, 'requirement': requirement['id'], 'importance': requirement['importance']})
        if len(picked) < needed:
            wanted.append({'requirement': requirement['id'], 'importance': requirement['importance'],
                           'form': '/'.join(names), 'shortfall': needed - len(picked), 'rcept_no': None})
    return {'download': [w for w in wanted if w.get('rcept_no')],
            'shortfalls': [w for w in wanted if not w.get('rcept_no')],
            'excluded_post_cutoff': excluded, 'eligible_filings': len(eligible)}


def _safe(text):
    return re.sub(r'[^\w.()\-가-힣ㆍ]+', '_', text).strip('_')[:60]


def download(rows, destination, key, opener=None):
    """Save each filing's original documents (document.xml is a zip). Returns manifest entries."""
    destination.mkdir(parents=True, exist_ok=True)
    saved = []
    for row in rows:
        payload, url = _read('document.xml', {'rcept_no': row['rcept_no']}, key, opener)
        try:
            archive = zipfile.ZipFile(io.BytesIO(payload))
        except zipfile.BadZipFile:
            raise FetchError(_api_error(payload) or f"document.xml for {row['rcept_no']} was not a zip archive")
        base = f"{_safe(row['report_base'])}_{row['filing_date']}_{row['rcept_no']}"
        for index, member in enumerate(sorted(archive.namelist())):
            data = archive.read(member)
            suffix = member.rsplit('.', 1)[-1].lower() if '.' in member else 'xml'
            name = f'{base}.{suffix}' if index == 0 else f'{base}_{index}.{suffix}'
            (destination / name).write_bytes(data)
            saved.append({'file': name, 'form': row['report_base'], 'filing_date': row['filing_date'],
                          'period': row.get('period'), 'rcept_no': row['rcept_no'], 'archive_member': member,
                          'requirement': row.get('requirement'), 'source_url': url, 'bytes': len(data)})
    return saved
