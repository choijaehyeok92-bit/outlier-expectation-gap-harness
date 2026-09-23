"""Universe storage: atomic JSON, cross-process locks, history and read-only run sync.

`runs/<RUN_ID>/` stays the authority for every number. This module reads those
artifacts (never writes them) and maintains the universe index next to them:

    universe/universe.json      index, one row per ticker (authoritative for lifecycle only)
    universe/universe.csv       derived export, rewritten on every save
    universe/queue.json         derived processing order and pending work, rewritten on every save
    universe/history/<T>.jsonl  append-only change log of decision fields per synced snapshot
    universe/snapshots/<D>.json copy of the index at the end of a batch or on request
    universe/locks/<T>.lock     one runner per ticker at a time (OS advisory lock)

Writes go through a temp file and os.replace so a reader never sees a partial
file, and the index is only modified inside `transaction()`, which holds a
lock file for the whole read-modify-write.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import socket
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from . import universe as U

SCHEMA_VERSION = '1.0'
_THREAD_LOCK = threading.RLock()


def utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_policy(root):
    return json.loads((Path(root)/'config/universe.json').read_text(encoding='utf-8'))


def atomic_write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f'.{path.name}.{os.getpid()}.{threading.get_ident()}.tmp')
    with open(tmp, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def atomic_dump_json(path, obj):
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def sha256_of(path):
    data = Path(path).read_bytes().replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


try:  # OS-level advisory locks: released by the kernel when the holder exits, so no staleness guessing.
    import fcntl
except ImportError:  # Windows
    fcntl = None
    import msvcrt


class LockBusy(RuntimeError):
    pass


def _try_lock(fd):
    try:
        if fcntl:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        return True
    except OSError:
        return False


def _unlock(fd):
    if fcntl:
        fcntl.flock(fd, fcntl.LOCK_UN)
    else:
        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)


@contextlib.contextmanager
def file_lock(path, timeout=30.0, poll=0.05, owner=None):
    """Exclusive advisory lock on `path` (flock / msvcrt). Waits up to `timeout`, then LockBusy.

    The lock file is never deleted: removing lock files is what makes lock-file
    schemes racy. Another open of the same file, even from this process or thread,
    conflicts, so one lock serializes threads and processes alike.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        deadline = time.monotonic() + timeout
        while not _try_lock(fd):
            if time.monotonic() >= deadline:
                raise LockBusy(f'lock busy: {path}')
            time.sleep(poll)
        info = {'pid': os.getpid(), 'host': socket.gethostname(), 'acquired_at': utcnow(), 'owner': owner}
        try:  # diagnostics only
            os.ftruncate(fd, 0)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, json.dumps(info).encode('utf-8'))
        except OSError:
            pass
        try:
            yield info
        finally:
            _unlock(fd)
    finally:
        os.close(fd)


def lock_is_held(path):
    path = Path(path)
    if not path.exists():
        return False
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        if _try_lock(fd):
            _unlock(fd)
            return False
        return True
    finally:
        os.close(fd)


class Store:
    def __init__(self, root, policy=None):
        self.root = Path(root)
        self.policy = policy or load_policy(self.root)
        self.dir = self.root/self.policy['paths']['universe_dir']
        self.path = self.dir/'universe.json'
        self._depth = 0

    # ---------------------------------------------------------------- index
    def empty(self):
        return {'schema_version': SCHEMA_VERSION, 'updated_at': None, 'tickers': {}}

    def load(self):
        if not self.path.exists():
            return self.empty()
        data = json.loads(self.path.read_text(encoding='utf-8'))
        data.setdefault('tickers', {})
        for ticker, row in data['tickers'].items():
            for key, default in U.ROW_DEFAULTS.items():
                row.setdefault(key, json.loads(json.dumps(default)))
        return data

    def save(self, universe):
        universe['schema_version'] = SCHEMA_VERSION
        universe['updated_at'] = utcnow()
        universe['tickers'] = {k: universe['tickers'][k] for k in sorted(universe['tickers'])}
        atomic_dump_json(self.path, universe)
        rows = self.ordered(universe)
        atomic_write_text(self.dir/'universe.csv', U.to_csv(rows))
        atomic_dump_json(self.dir/'queue.json', {
            'derived_from': 'universe/universe.json', 'updated_at': universe['updated_at'],
            'order': [r['ticker'] for r in rows],
            'pending': [r['ticker'] for r in rows if r['run_status'] in ('QUEUED', 'RUNNING')],
            'blocked': [r['ticker'] for r in rows if r['run_status'] == 'BLOCKED'],
            'failed': [r['ticker'] for r in rows if r['run_status'] == 'FAILED'],
            'complete': [r['ticker'] for r in rows if r['run_status'] == 'COMPLETE']})

    @staticmethod
    def ordered(universe):
        return sorted(universe['tickers'].values(), key=lambda r: (r.get('queue_seq') or 0, r['ticker']))

    @contextlib.contextmanager
    def transaction(self):
        """Read-modify-write of the index under one lock. Nested use shares the outer lock."""
        with _THREAD_LOCK:
            if self._depth:
                self._depth += 1
                try:
                    yield self._current
                finally:
                    self._depth -= 1
                return
            with file_lock(self.dir/'.universe.lock', timeout=120):
                self._current = self.load()
                self._depth = 1
                try:
                    yield self._current
                    self.save(self._current)
                finally:
                    self._depth = 0
                    self._current = None

    def update_row(self, ticker, fn):
        with self.transaction() as universe:
            row = universe['tickers'].get(ticker)
            if row is None:
                raise KeyError(ticker)
            fn(row)
            row['last_updated'] = utcnow()
            return json.loads(json.dumps(row))

    # ---------------------------------------------------------------- history / snapshots
    def append_history(self, ticker, record):
        path = self.dir/'history'/f'{ticker}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        with file_lock(path.with_suffix('.lock'), timeout=30):
            with open(path, 'a', encoding='utf-8', newline='\n') as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')

    def history(self, ticker):
        path = self.dir/'history'/f'{ticker}.jsonl'
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

    def write_snapshot(self, label=None):
        universe = self.load()
        name = label or datetime.now(timezone.utc).strftime('%Y-%m-%d')
        dest = self.dir/'snapshots'/f'{name}.json'
        atomic_dump_json(dest, universe)
        return dest

    def ticker_lock(self, ticker, timeout=0.0):
        return file_lock(self.dir/'locks'/f'{ticker}.lock', timeout=timeout, owner=ticker)

    def lock_held(self, ticker):
        return lock_is_held(self.dir/'locks'/f'{ticker}.lock')


# -------------------------------------------------------------------- run artifacts (read-only)

class RunReader:
    """Read-only access to `runs/<RUN_ID>/` through the harness runtime (so ROOT patches apply)."""

    def __init__(self, runtime):
        self.h = runtime
        self._config_hashes = None

    def config_hashes(self):
        if self._config_hashes is None:
            self._config_hashes = self.h.config_hashes()
        return self._config_hashes

    def relative(self, path):
        return Path(path).relative_to(self.h.ROOT).as_posix()

    def run_as_of(self, run_id):
        try:
            path = self.h.run_dir(run_id)/'company_context.json'
        except ValueError:
            return None
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding='utf-8')).get('as_of_date')
        except ValueError:
            return None

    def artifacts(self, run_id):
        run = self.h.run_dir(run_id)
        art = {'run_id': run_id, 'run_path': self.relative(run), 'exists': run.exists(), 'paths': {}, 'hashes': {},
               'manifest': None, 'context': None, 'final': None, 'aggregate': None, 'ic_report': None,
               'deep_report': None, 'report_status': {}, 'freeze': {}, 'read_errors': []}
        if not run.exists():
            return art
        files = {'final_verdict': run/'final_verdict.json', 'aggregate': run/'aggregate.json',
                 'ic': run/'reports'/'IC.json', 'manifest': run/'run_manifest.json',
                 'company_context': run/'company_context.json', 'digest': run/'digest.md',
                 'one_page': run/'one_page_investment_record.md', 'deep_report': run/'deep_report.json',
                 'deep_report_md': run/'deep_report.md'}
        keys = {'final_verdict': 'final', 'aggregate': 'aggregate', 'ic': 'ic_report', 'manifest': 'manifest',
                'company_context': 'context', 'deep_report': 'deep_report'}
        for name, path in files.items():
            if not path.exists():
                continue
            art['paths'][name] = self.relative(path)
            if name in ('final_verdict', 'aggregate', 'ic', 'deep_report'):
                art['hashes'][name] = sha256_of(path)
            if name in keys:
                try:
                    art[keys[name]] = json.loads(path.read_text(encoding='utf-8'))
                except ValueError as error:
                    art['read_errors'].append(f'{art["paths"][name]}: {error}')
        reports = run/'reports'
        if reports.exists():
            for path in sorted(reports.glob('*.json')):
                try:
                    art['report_status'][path.stem] = json.loads(path.read_text(encoding='utf-8')).get('analysis_status')
                except ValueError:
                    art['report_status'][path.stem] = 'unreadable'
        manifest = art['manifest'] or {}
        frozen = bool(manifest.get('frozen'))
        inputs = manifest.get('input_files')
        art['freeze'] = {
            'frozen': frozen,
            'inputs_current': bool(frozen and inputs and self.h.snapshot_hashes(run) == inputs),
            'config_current': bool(frozen and manifest.get('config_files') and manifest.get('config_files') == self.config_hashes()),
            'harness_commit': manifest.get('harness_commit'),
            'reconstructed': bool(manifest.get('reconstructed')),
        }
        return art

    def inspect(self, run_id):
        """Planner view of an in-progress run. Pure computation over files; writes nothing."""
        try:
            reports = self.h.load_reports(run_id)
            result = self.h.compute_aggregate(run_id, reports)
            step = self.h.plan(run_id, reports, result)
        except SystemExit as error:
            return {'plan': None, 'reachable': None, 'error': str(error)}
        except Exception as error:  # a legacy or damaged run must not stop the batch
            return {'plan': None, 'reachable': None, 'error': f'{type(error).__name__}: {error}'}
        return {'plan': step, 'reachable': result.get('reachable_archetypes_raw'),
                'triage_complete': self.h.triage_complete(reports), 'early_exit': result.get('early_exit'),
                'mechanical_state': result.get('mechanical_pre_ic_state'), 'error': None}


def domain_agent_map(runtime):
    return {a['domain']: a['agent_id'] for a in runtime.MANIFEST}


def needs_inspection(art):
    final = art.get('final') or {}
    if not art.get('exists') or not (art.get('freeze') or {}).get('frozen'):
        return False
    if final.get('early_exit'):
        return False
    ic_done = (art.get('ic_report') or {}).get('analysis_status') == 'complete'
    return not (ic_done and final.get('ic_verdict'))


def _prepare(reader, row, ticker, inspect):
    """Read-only work for one row, done outside the index lock."""
    run_id = row.get('run_id') or ticker
    art = reader.artifacts(run_id)
    inspection = reader.inspect(run_id) if inspect and needs_inspection(art) else None
    return run_id, art, inspection


def _apply(store, reader, universe, ticker, run_id, art, inspection, now, runner_owned):
    row = universe['tickers'].get(ticker)
    if row is None:
        raise KeyError(ticker)
    if (row.get('run_id') or ticker) != run_id:
        raise RuntimeError(f'{ticker}: run id changed during sync ({run_id} -> {row.get("run_id")})')
    statuses = store.policy['statuses']
    summary = U.summarize_run(art, domain_agent_map(reader.h), reader.h.STATE_POLICY)
    state = U.derive_run_state(art, inspection, statuses['planner_stage_map'],
                               statuses['triage_lead_stage']['agent'])
    if inspection and inspection.get('reachable') is not None and not summary.get('verdict_source'):
        summary['reachable_archetypes'] = inspection['reachable']
    fields = store.policy['history_fields']
    # Changes are measured against the last recorded snapshot, so a new as-of run
    # (whose row was reset on import) still shows what moved since the previous date.
    recorded = [e for e in store.history(ticker) if e.get('snapshot') and not e.get('event')] \
        if summary.get('verdict_source') else []
    before = recorded[-1]['snapshot'] if recorded else None
    if (not runner_owned and row.get('run_status') == 'RUNNING' and state['run_status'] != 'COMPLETE'
            and store.lock_held(ticker)):
        state = {**state, 'run_status': 'RUNNING'}
    U.apply_sync(row, summary, state, now)
    row['run_id'] = run_id
    after = {k: row.get(k) for k in fields}
    changes = U.history_changes(before, after, fields)
    if summary.get('verdict_source') and changes:
        store.append_history(ticker, {'ticker': ticker, 'recorded_at': now, 'run_id': run_id,
                                      'verdict_source': summary['verdict_source'],
                                      'source_hashes': summary['source_hashes'],
                                      'snapshot': after, 'changes': changes})
    return json.loads(json.dumps(row))


def sync_ticker_from_run(store, reader, ticker, now=None, inspect=True, runner_owned=False):
    """Refresh one row from its run artifacts; append a history record when tracked fields change.

    Returns (row, art, inspection). Never writes inside runs/. `runner_owned` is set by
    the runner that holds this ticker's lock and wants the real derived status.
    """
    now = now or utcnow()
    current = store.load()['tickers'].get(ticker)
    if current is None:
        raise KeyError(ticker)
    # Reading and planning happen outside the index lock so parallel workers do not serialize on it.
    run_id, art, inspection = _prepare(reader, current, ticker, inspect)
    with store.transaction() as universe:
        row = _apply(store, reader, universe, ticker, run_id, art, inspection, now, runner_owned)
    return row, art, inspection


def sync_many(store, reader, tickers=None, now=None, inspect=True):
    """Refresh many rows with one index read and one write. Returns the refreshed rows in order."""
    now = now or utcnow()
    snapshot = store.load()['tickers']
    names = [t for t in (tickers or list(snapshot)) if t in snapshot]
    prepared = {t: _prepare(reader, snapshot[t], t, inspect) for t in names}
    rows = []
    with store.transaction() as universe:
        for ticker in names:
            if ticker not in universe['tickers']:
                continue      # removed concurrently
            run_id, art, inspection = prepared[ticker]
            if (universe['tickers'][ticker].get('run_id') or ticker) != run_id:
                continue      # re-imported for another as-of meanwhile; the next sync picks it up
            rows.append(_apply(store, reader, universe, ticker, run_id, art, inspection, now, False))
    return rows
