"""Stage 0 acquisition: pull primary filings from EDGAR so intake has something to check.

This is deterministic retrieval from the regulator, not research. It resolves a
ticker to a CIK, reads the submissions index, picks the filings the intake
checklist asks for, and writes them under the run's sources/ with a manifest
recording where each one came from. The preprocessor still only ever reads files
on disk, so its "no web search" rule is untouched.

Two rules the caller cannot opt out of: nothing filed after the run's as_of_date
is downloaded, and every request carries a declared contact in the User-Agent
because SEC fair-access requires one.
"""
import json
import time
import urllib.error
import urllib.request

TICKER_INDEX = 'https://www.sec.gov/files/company_tickers.json'
SUBMISSIONS = 'https://data.sec.gov/submissions/CIK{cik:010d}.json'
ARCHIVE = 'https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}'
REQUEST_SPACING_SECONDS = 0.15   # SEC asks for no more than 10 requests a second


class FetchError(RuntimeError):
    """Raised with a message meant for the operator, not a stack trace."""


def _open(url, user_agent, timeout=30):
    request = urllib.request.Request(url, headers={
        'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate', 'Host': url.split('/')[2]})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _read(url, user_agent, opener=None):
    """Every retrieval failure reaches the caller as FetchError, whoever opened it."""
    try:
        payload = (opener or _open)(url, user_agent)
    except urllib.error.HTTPError as error:
        raise FetchError(f'{url} -> HTTP {error.code}') from error
    except FetchError:
        raise
    except Exception as error:                       # blocked egress, DNS, TLS, timeout
        raise FetchError(f'{url} -> {type(error).__name__}: {error}') from error
    time.sleep(REQUEST_SPACING_SECONDS)
    return payload


def _get_json(url, user_agent, opener=None):
    raw = _read(url, user_agent, opener)
    try:
        return json.loads(raw)
    except ValueError as error:
        raise FetchError(f'{url} -> response was not JSON ({error})') from error


def resolve_cik(ticker, user_agent, opener=None):
    index = _get_json(TICKER_INDEX, user_agent, opener)
    rows = index.values() if isinstance(index, dict) else index
    for row in rows:
        if str(row.get('ticker', '')).upper() == ticker.upper():
            return int(row['cik_str']), row.get('title')
    raise FetchError(f'{ticker} is not in the EDGAR ticker index; pass --cik explicitly')


def recent_filings(cik, user_agent, opener=None):
    """Flatten the submissions index into rows, newest first."""
    data = _get_json(SUBMISSIONS.format(cik=cik), user_agent, opener)
    recent = data.get('filings', {}).get('recent', {})
    keys = ('form', 'filingDate', 'accessionNumber', 'primaryDocument', 'reportDate', 'primaryDocDescription')
    columns = {key: recent.get(key) or [] for key in keys}
    count = len(columns['form'])
    rows = [{key: (columns[key][i] if i < len(columns[key]) else None) for key in keys} for i in range(count)]
    rows.sort(key=lambda r: r['filingDate'] or '', reverse=True)
    return rows, data.get('name')


def plan(rows, policy, as_of_date):
    """Which filings to download, per intake requirement, respecting the cutoff."""
    eligible = [r for r in rows if (r['filingDate'] or '') <= as_of_date]
    excluded = len(rows) - len(eligible)
    wanted, seen = [], set()
    for requirement in policy['requirements']:
        forms = requirement.get('edgar_forms') or []
        if not forms:
            continue
        needed = int(requirement.get('min_count', 1))
        picked = [r for r in eligible if r['form'] in forms][:needed]
        for row in picked:
            key = row['accessionNumber']
            if key in seen:
                continue
            seen.add(key)
            wanted.append({**row, 'requirement': requirement['id'], 'importance': requirement['importance']})
        if len(picked) < needed:
            wanted.append({'requirement': requirement['id'], 'importance': requirement['importance'],
                           'form': '/'.join(forms), 'shortfall': needed - len(picked),
                           'accessionNumber': None})
    return {'download': [w for w in wanted if w.get('accessionNumber')],
            'shortfalls': [w for w in wanted if not w.get('accessionNumber')],
            'excluded_post_cutoff': excluded, 'eligible_filings': len(eligible)}


def document_url(cik, row):
    return ARCHIVE.format(cik=cik, accession=(row['accessionNumber'] or '').replace('-', ''),
                          document=row['primaryDocument'])


def download(cik, rows, destination, user_agent, opener=None):
    """Save each filing's primary document. Returns manifest entries."""
    destination.mkdir(parents=True, exist_ok=True)
    saved = []
    for row in rows:
        url = document_url(cik, row)
        name = f"{row['form'].replace('/', '-')}_{row['filingDate']}_{row['accessionNumber']}.htm"
        payload = _read(url, user_agent, opener)
        (destination / name).write_bytes(payload)
        saved.append({'file': name, 'form': row['form'], 'filing_date': row['filingDate'],
                      'report_date': row.get('reportDate'), 'accession': row['accessionNumber'],
                      'requirement': row.get('requirement'), 'source_url': url,
                      'bytes': len(payload)})
    return saved
