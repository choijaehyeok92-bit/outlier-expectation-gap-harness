"""Batch runner for the universe: planner-driven, one ticker at a time per worker.

For each ticker the loop is the RUNBOOK's, never a hard-coded stage order:

    plan -> execute the agents plan requests -> validate -> aggregate -> digest -> plan

until the planner says stop_early / stop_complete, an input is missing (BLOCKED),
something fails (FAILED), or the operator's stop boundary is reached (paused,
QUEUED). Stages of one ticker are strictly sequential; only different tickers run
in parallel, each in its own `runs/<RUN_ID>/` and under its own lock file.

The harness never calls a model, so agent output comes from executors:

* staged   — `.harness_inputs/<RUN_ID>/reports/<AID>.json` (the CI workflows' convention),
             plus staged company_context.json / sources / financial pack for Stage 0
* macro    — the global macro cache, exactly as `init` reuses it, when every
             component is fresh for the run's as-of date
* command  — optional `--agent-cmd` template, e.g. a model CLI that reads {prompt}
             and writes {output}

When none can supply a report the prompt is written (`runs/<RUN>/<AID>_prompt.md`)
and the ticker is BLOCKED with `awaiting`. Nothing is fabricated, no gate is
bypassed, a stale freeze is never re-frozen, and final_verdict.json is only ever
written by `harness.py aggregate`.

Every mutating step is a `python harness.py ...` subprocess in the repository
root, so each ticker's commands and output are isolated and logged separately.
"""
from __future__ import annotations

import concurrent.futures
import dataclasses
import json
import os
import shlex
import shutil
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from . import universe as U
from .universe_reports import write_dashboards
from .universe_store import (LockBusy, RunReader, Store, atomic_dump_json, file_lock, sha256_of,
                             sync_ticker_from_run, utcnow)

_GIT_LOCK = threading.Lock()


@dataclasses.dataclass
class Options:
    stop_after: str | None = None
    eligible_only: bool = False
    only_started: bool = False
    include_failed: bool = False
    include_funds: bool = False
    tickers: tuple = ()
    workers: int = 1
    dry_run: bool = False
    agent_cmd: str | None = None
    user_agent: str | None = None
    dart_key: str | None = None
    provider: str | None = None
    model: str | None = None
    reasoning_effort: str | None = None
    git_mode: str = 'none'
    report: bool = True
    agent_timeout: float = 3600
    command_timeout: float = 900
    max_cycles: int = 40
    limit: int | None = None


class StepFailed(Exception):
    def __init__(self, stage, command, returncode, stderr, retryable, summary):
        super().__init__(summary)
        self.stage, self.command, self.returncode = stage, command, returncode
        self.stderr, self.retryable, self.summary = stderr, retryable, summary


class Blocked(Exception):
    def __init__(self, stage, reason, awaiting=()):
        super().__init__(reason)
        self.stage, self.reason, self.awaiting = stage, reason, list(awaiting)


def _tail(text, limit=4000):
    text = text or ''
    return text if len(text) <= limit else '…' + text[-limit:]


# ------------------------------------------------------------------------------ logging

class TickerLog:
    """runlogs/universe/<date>/<TICKER>.json (structured, appended per batch) + <TICKER>.log (raw)."""

    def __init__(self, directory, ticker, batch_id):
        self.dir = Path(directory)
        self.ticker = ticker
        self.entry = {'batch_id': batch_id, 'ticker': ticker, 'started_at': utcnow(), 'finished_at': None,
                      'stages': [], 'outcome': None}
        self.raw = self.dir/f'{ticker}.log'
        self.dir.mkdir(parents=True, exist_ok=True)

    def stage(self, name, status, **extra):
        self.entry['stages'].append({'stage': name, 'status': status, 'at': utcnow(), **extra})

    def command(self, args, returncode, seconds, stdout, stderr):
        with open(self.raw, 'a', encoding='utf-8') as handle:
            handle.write(f"\n$ harness.py {' '.join(args)}   [rc={returncode}, {seconds:.1f}s, {utcnow()}]\n")
            if stdout:
                handle.write(stdout if stdout.endswith('\n') else stdout + '\n')
            if stderr:
                handle.write('[stderr]\n' + (stderr if stderr.endswith('\n') else stderr + '\n'))
        self.entry.setdefault('commands', []).append({'command': ' '.join(args), 'returncode': returncode,
                                                      'seconds': round(seconds, 2)})

    def note(self, text):
        with open(self.raw, 'a', encoding='utf-8') as handle:
            handle.write(f'# {utcnow()} {text}\n')

    def finish(self, outcome):
        self.entry['finished_at'] = utcnow()
        self.entry['outcome'] = outcome
        path = self.dir/f'{self.ticker}.json'
        with file_lock(path.with_suffix('.json.lock'), timeout=30):
            existing = json.loads(path.read_text(encoding='utf-8')) if path.exists() else \
                {'ticker': self.ticker, 'invocations': []}
            existing['invocations'].append(self.entry)
            atomic_dump_json(path, existing)


# ------------------------------------------------------------------------------ harness commands

class Harness:
    """`python harness.py ...` in the repository root, logged per ticker."""

    def __init__(self, root, log, timeout):
        self.root, self.log, self.timeout = Path(root), log, timeout

    def run(self, *args, timeout=None, env=None):
        start = time.monotonic()
        env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', **(env or {})}
        try:
            done = subprocess.run([sys.executable, 'harness.py', *args], cwd=self.root, capture_output=True,
                                  text=True, encoding='utf-8', errors='replace', timeout=timeout or self.timeout,
                                  env=env)
            rc, out, err = done.returncode, done.stdout, done.stderr
        except subprocess.TimeoutExpired as error:
            rc, out, err = -9, error.stdout or '', f'timeout after {timeout or self.timeout}s'
            if isinstance(out, bytes):
                out = out.decode('utf-8', 'replace')
        self.log.command(args, rc, time.monotonic() - start, out, err)
        return rc, out, err

    def must(self, stage, *args, retryable=True, timeout=None, env=None):
        rc, out, err = self.run(*args, timeout=timeout, env=env)
        if rc != 0:
            raise StepFailed(stage, 'harness.py ' + ' '.join(args), rc, _tail(err or out), retryable,
                             f"`harness.py {' '.join(args)}` exited {rc}: {(err or out).strip().splitlines()[-1:] or ['']}"[:400])
        return out


# ------------------------------------------------------------------------------ executors

class Executors:
    """Supplies agent output. Order: staged input, macro cache (MO only), agent command."""

    def __init__(self, root, runtime, options, log, macro_lock_path):
        self.root, self.h, self.options, self.log = Path(root), runtime, options, log
        self.macro_lock_path = macro_lock_path

    def staged_dir(self, run_id, policy):
        return self.root/policy['paths']['staged_inputs_dir']/run_id

    def supply(self, row, run_id, aid, prompt_path, policy):
        run = self.h.run_dir(run_id)
        target = run/'reports'/f'{aid}.json'
        before = sha256_of(target) if target.exists() else None
        staged = self.staged_dir(run_id, policy)/'reports'/f'{aid}.json'
        if staged.exists():
            try:
                report = json.loads(staged.read_text(encoding='utf-8'))
            except ValueError as error:
                raise StepFailed(row['stage'], f'stage {staged}', None, str(error), False,
                                 f'{staged.relative_to(self.root)} is not valid JSON')
            problem = self._identity_problem(report, run_id, row)
            if problem:
                raise StepFailed(row['stage'], f'stage {staged}', None, problem, False,
                                 f'{staged.relative_to(self.root)}: {problem}')
            if report.get('analysis_status') == 'complete' and sha256_of(staged) != before:
                shutil.copyfile(staged, target)
                if aid == 'IC':
                    one_page = self.staged_dir(run_id, policy)/'one_page_investment_record.md'
                    if one_page.exists():
                        shutil.copyfile(one_page, run/'one_page_investment_record.md')
                return 'produced', f'staged {staged.relative_to(self.root).as_posix()}'
        if aid == 'MO':
            produced = self._from_macro_cache(row, run_id, target, before)
            if produced:
                return 'produced', produced
        if self.options.agent_cmd:
            return self._command(row, run_id, aid, prompt_path, target, before)
        return 'awaiting', f'no staged report at {staged.relative_to(self.root).as_posix()}'

    @staticmethod
    def _identity_problem(report, run_id, row):
        declared = str(report.get('ticker') or '').upper()
        if declared not in {run_id.upper(), row['ticker'].upper()}:
            return f'report is for {declared or "no ticker"}, not {run_id}'
        if report.get('as_of_date') and report.get('as_of_date') != row['as_of_date']:
            return f"report as_of_date {report.get('as_of_date')} != run {row['as_of_date']}"
        return None

    def _from_macro_cache(self, row, run_id, target, before):
        """The same reuse `init` performs, applied when MO is requested later in the run."""
        agent = next(a for a in self.h.MANIFEST if a['agent_id'] == 'MO')
        with file_lock(self.macro_lock_path, timeout=120):
            cached = self.h.macro_cache_source(row['as_of_date'])
        if len(cached) != len(self.h.OVERLAY_POLICY['component_ttl_hours']):
            return None
        report = self.h.cached_macro_report(agent, run_id, row['as_of_date'], cached)
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if before and target.exists() and target.read_text(encoding='utf-8') == text:
            return None
        self.h.dump_json(target, report)
        return 'global macro cache (fresh components; company transmission recomputed)'

    def _command(self, row, run_id, aid, prompt_path, output, before):
        values = {'ticker': row['ticker'], 'run_id': run_id, 'agent': aid, 'prompt': str(prompt_path),
                  'output': str(output), 'root': str(self.root), 'as_of': row['as_of_date']}
        try:
            argv = [token.format(**values) for token in shlex.split(self.options.agent_cmd)]
        except (KeyError, ValueError) as error:
            raise StepFailed(row['stage'], self.options.agent_cmd, None, str(error), False,
                             f'--agent-cmd template error: {error}')
        env = {**os.environ, **{f'HARNESS_{k.upper()}': v for k, v in values.items()}}
        output.parent.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        try:
            done = subprocess.run(argv, cwd=self.root, capture_output=True, text=True, encoding='utf-8',
                                  errors='replace', timeout=self.options.agent_timeout, env=env)
            rc, out, err = done.returncode, done.stdout, done.stderr
        except subprocess.TimeoutExpired:
            rc, out, err = -9, '', f'agent command timed out after {self.options.agent_timeout}s'
        except OSError as error:
            rc, out, err = -1, '', f'{type(error).__name__}: {error}'
        self.log.command(['[agent-cmd]', aid, *argv], rc, time.monotonic() - start, _tail(out), _tail(err))
        if rc != 0:
            raise StepFailed(row['stage'], ' '.join(argv), rc, _tail(err or out), True,
                             f'agent command for {aid} exited {rc}')
        if not output.exists() or (before and sha256_of(output) == before):
            raise StepFailed(row['stage'], ' '.join(argv), rc, _tail(err or out), True,
                             f'agent command for {aid} did not write {output.name}')
        return 'produced', 'agent command'


# ------------------------------------------------------------------------------ one ticker

class TickerJob:
    def __init__(self, runner, ticker):
        self.runner = runner
        self.store, self.reader, self.options = runner.store, runner.reader, runner.options
        self.h = runner.reader.h
        self.policy = self.store.policy
        self.ticker = ticker
        self.log = TickerLog(runner.log_dir, ticker, runner.batch_id)
        self.harness = Harness(self.store.root, self.log, self.options.command_timeout)
        self.executors = Executors(self.store.root, self.h, self.options, self.log, runner.macro_lock_path)
        self.row = None

    def set_row(self, **fields):
        self.row = self.store.update_row(self.ticker, lambda r: r.update(fields))

    def process(self):
        try:
            lock = self.store.ticker_lock(self.ticker)
            lock.__enter__()
        except LockBusy:
            self.log.note('skipped: another runner holds this ticker')
            return {'ticker': self.ticker, 'outcome': 'skipped_locked'}
        outcome = {'ticker': self.ticker}
        try:
            self.row = self.store.load()['tickers'][self.ticker]
            self.set_row(run_status='RUNNING', started=True, attempts=(self.row.get('attempts') or 0) + 1,
                         last_error=None)
            result = self._advance()
            outcome.update(result)
            row, _, _ = sync_ticker_from_run(self.store, self.reader, self.ticker, runner_owned=True)
            if result['outcome'] == 'blocked':
                self.set_row(run_status='BLOCKED', stage=result.get('stage') or row['stage'],
                             blocked_reason=result['reason'], awaiting=result.get('awaiting', []))
            elif result['outcome'] == 'paused':
                self.set_row(run_status='QUEUED', stage=result.get('stage') or row['stage'],
                             blocked_reason=None, awaiting=[])
        except StepFailed as error:
            outcome.update(outcome='failed', stage=error.stage, reason=error.summary)
            self._record_failure(error.stage, error.command, 'StepFailed', error.stderr, error.retryable, error.summary)
        except Exception as error:  # isolate: one ticker's defect never stops the batch
            summary = f'{type(error).__name__}: {error}'
            outcome.update(outcome='failed', stage=(self.row or {}).get('stage'), reason=summary)
            self._record_failure((self.row or {}).get('stage'), None, type(error).__name__,
                                 _tail(traceback.format_exc()), True, summary)
        except KeyboardInterrupt:
            self.set_row(run_status='QUEUED', blocked_reason='interrupted by operator')
            raise
        finally:
            lock.__exit__(None, None, None)
            self.log.finish(outcome)
        self.runner.after_ticker(self.ticker, outcome)
        return outcome

    def _record_failure(self, stage, command, kind, stderr, retryable, summary):
        with_sync = None
        try:
            with_sync, _, _ = sync_ticker_from_run(self.store, self.reader, self.ticker, runner_owned=True)
        except Exception:
            pass
        self.set_row(run_status='FAILED', stage=stage or (with_sync or self.row or {}).get('stage') or 'stage0',
                     last_error={'command': command, 'stage': stage, 'exception_type': kind, 'stderr': stderr,
                                 'retryable': retryable, 'timestamp': utcnow(), 'summary': summary})
        self.log.stage(stage or 'unknown', 'FAILED', error=summary, retryable=retryable)

    # ---------------------------------------------------------------- the loop
    def _advance(self):
        statuses = self.policy['statuses']
        lead = tuple(self.policy['runner'].get('lead_agents') or ())
        run_id = self.row['run_id'] or self.ticker
        seen = set()
        for _ in range(self.options.max_cycles):
            art = self.reader.artifacts(run_id)
            inspection = self.reader.inspect(run_id) if art['exists'] and art['freeze'].get('frozen') else None
            action = U.determine_next_universe_action(art, inspection, statuses, self.options.stop_after, lead)
            self.set_row(stage=action['stage'])
            kind = action['kind']
            if kind == 'complete':
                self.log.stage('complete', 'EARLY_EXIT' if action.get('early_exit') else 'COMPLETE')
                self._report(run_id, art)
                return {'outcome': 'complete', 'stage': 'complete', 'early_exit': action.get('early_exit')}
            if kind == 'blocked':
                self.log.stage(action['stage'], 'BLOCKED', reason=action['reason'])
                return {'outcome': 'blocked', 'stage': action['stage'], 'reason': action['reason']}
            if kind == 'pause':
                self.log.stage(action['stage'], 'PAUSED', reason=action['reason'])
                return {'outcome': 'paused', 'stage': action['stage'], 'reason': action['reason']}
            if kind == 'init':
                with file_lock(self.runner.macro_lock_path, timeout=120):
                    self.harness.must('stage0', 'init', run_id, '--as-of', self.row['as_of_date'])
                self.log.stage('stage0', 'PASS', step='init')
                continue
            if kind == 'stage0':
                try:
                    self._stage0(run_id)
                except Blocked as blocked:
                    self.log.stage('stage0', 'BLOCKED', reason=blocked.reason)
                    return {'outcome': 'blocked', 'stage': 'stage0', 'reason': blocked.reason,
                            'awaiting': blocked.awaiting}
                continue
            signature = (kind, action['stage'], tuple(action.get('agents') or ()),
                         tuple(sorted((art.get('report_status') or {}).items())), tuple(sorted(art['hashes'].items())))
            if signature in seen:
                reason = (f"no progress: the planner still requests {action.get('agents') or action['stage']} "
                          f"after they were supplied; a revised report is needed (for example a re-analysis "
                          f"that records geo_events_reviewed or an owner veto assessment)")
                self.log.stage(action['stage'], 'BLOCKED', reason=reason)
                return {'outcome': 'blocked', 'stage': action['stage'], 'reason': reason,
                        'awaiting': list(action.get('agents') or ())}
            seen.add(signature)
            if kind == 'finalize':
                self._cycle(run_id, action['stage'])
                continue
            awaiting = self._agents(run_id, action)
            if awaiting:
                where = ', '.join(f'runs/{run_id}/{a}_prompt.md' for a in awaiting)
                why = ('structural geopolitical re-analysis requested by the planner; '
                       if action.get('planner_stage') == 'fundamental_reanalysis' else '')
                reason = (f"{why}awaiting agent output for {', '.join(awaiting)} "
                          f"(prompts: {where}; stage reports in .harness_inputs/{run_id}/reports/ or pass --agent-cmd)")
                return {'outcome': 'blocked', 'stage': action['stage'], 'reason': reason, 'awaiting': awaiting}
        reason = f'stopped after {self.options.max_cycles} planner cycles without reaching a stop signal'
        return {'outcome': 'blocked', 'stage': self.row.get('stage'), 'reason': reason}

    def _cycle(self, run_id, stage):
        """aggregate -> digest (the plan is re-read at the top of the loop)."""
        self.harness.must(stage, 'aggregate', run_id, retryable=False)
        self.harness.must(stage, 'digest', run_id, retryable=False)
        self.log.stage(stage, 'PASS', step='aggregate+digest')

    def _agents(self, run_id, action):
        stage = action['stage']
        produced, awaiting = [], []
        for aid in action['agents']:
            prompt = self.h.run_dir(run_id)/f'{aid}_prompt.md'
            self.harness.must(stage, 'prompt', run_id, aid, '--out', str(prompt), retryable=False)
            status, detail = self.executors.supply(self.row, run_id, aid, prompt, self.policy)
            if status == 'awaiting':
                awaiting.append(aid)
                self.log.stage(stage, 'AWAITING', agent=aid, detail=detail)
                continue
            rc, out, err = self.harness.run('validate', run_id, aid)
            if rc != 0:
                raise StepFailed(stage, f'harness.py validate {run_id} {aid}', rc, _tail(out + err), False,
                                 f'{aid} report failed validation: {out.strip()[:300]}')
            produced.append(aid)
            self.log.stage(stage, 'PASS', agent=aid, source=detail)
            if aid == 'MO':
                self._cache_macro(run_id)
        if produced:
            self._cycle(run_id, stage)
        return awaiting

    def _cache_macro(self, run_id):
        with file_lock(self.runner.macro_lock_path, timeout=120):
            rc, out, err = self.harness.run('cache-macro', run_id)
        self.log.stage('macro', 'CACHED' if rc == 0 else 'NOT_CACHED', detail=(out or err).strip()[:200])

    def _report(self, run_id, art):
        if not self.options.report:
            return
        if not (art['freeze'].get('config_current') and art['freeze'].get('inputs_current')):
            self.log.stage('report', 'SKIPPED', reason='recorded verdict from an older freeze; use `report --existing-run`')
            return
        rc, out, err = self.harness.run('report', run_id)
        self.log.stage('report', 'PASS' if rc == 0 else 'FAILED', detail=(out or err).strip()[-300:])

    # ---------------------------------------------------------------- Stage 0
    def _stage0(self, run_id):
        run = self.h.run_dir(run_id)
        staged = self.executors.staged_dir(run_id, self.policy)
        context_path = run/'company_context.json'
        context = json.loads(context_path.read_text(encoding='utf-8'))
        locked = ('current_price', 'net_cash_per_share')
        if any(context.get(k) is None for k in locked):
            staged_ctx = staged/'company_context.json'
            if not staged_ctx.exists():
                raise Blocked('stage0', f"company_context.json needs {', '.join(locked)} (and sources) before freeze; "
                                        f"stage it at .harness_inputs/{run_id}/company_context.json or edit "
                                        f"runs/{run_id}/company_context.json", ['company_context'])
            candidate = json.loads(staged_ctx.read_text(encoding='utf-8'))
            if str(candidate.get('ticker') or '').upper() != run_id.upper() or candidate.get('as_of_date') != self.row['as_of_date']:
                raise Blocked('stage0', f"staged company_context.json is for {candidate.get('ticker')} / "
                                        f"{candidate.get('as_of_date')}, not {run_id} / {self.row['as_of_date']}",
                              ['company_context'])
            shutil.copyfile(staged_ctx, context_path)
            self.log.stage('stage0', 'PASS', step='company_context', source='staged')
        if (staged/'sources').is_dir():
            copied = 0
            for source in sorted(p for p in (staged/'sources').rglob('*') if p.is_file()):
                dest = run/'sources'/source.relative_to(staged/'sources')
                if not dest.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, dest)
                    copied += 1
            if copied:
                self.log.stage('stage0', 'PASS', step='sources', copied=copied, source='staged')
        pack = run/self.h.FINANCIAL_PACK
        if not pack.exists() and not (run/'sources'/'fetch_manifest.json').exists():
            self._fetch(run_id)
        if not pack.exists():
            prompt = run/'FP_prompt.md'
            self.harness.must('stage0', 'prompt', run_id, 'FP', '--out', str(prompt), retryable=False)
            if not self.options.agent_cmd:
                raise Blocked('stage0', f'financial pack missing: FP prompt written to runs/{run_id}/FP_prompt.md; '
                                        f'stage the pack at .harness_inputs/{run_id}/sources/financials/'
                                        f'normalized_financials.json or pass --agent-cmd', ['FP'])
            self.executors._command(self.row, run_id, 'FP', prompt, pack, None)
            self.log.stage('stage0', 'PASS', step='FP', source='agent command')
        rc, out, err = self.harness.run('intake', run_id)
        if rc != 0:
            gaps = [l.strip() for l in out.splitlines() if l.strip().startswith('- ')][:6]
            raise Blocked('stage0', 'Stage 0 required documents missing: ' + ('; '.join(gaps) or out.strip()[-300:]),
                          ['FP'])
        rc, out, err = self.harness.run('validate-pack', run_id)
        if rc != 0:
            problems = [l.strip() for l in out.splitlines() if l.strip().startswith('- ')][:6]
            raise Blocked('stage0', 'financial pack failed validation: ' + ('; '.join(problems) or (err or out).strip()[-300:]),
                          ['FP'])
        args = ['freeze', run_id]
        for flag, value in (('--provider', self.options.provider), ('--model', self.options.model),
                            ('--reasoning-effort', self.options.reasoning_effort)):
            if value:
                args += [flag, value]
        rc, out, err = self.harness.run(*args)
        if rc != 0:
            raise Blocked('stage0', 'freeze refused: ' + (err or out).strip()[-400:], ['company_context'])
        self.log.stage('stage0', 'PASS', step='freeze')

    def _fetch(self, run_id):
        """Stage 0 retrieval. Credentials travel in the environment only, never as logged arguments."""
        from .fetch_dart import stock_code_of
        if stock_code_of(run_id):
            key = self.options.dart_key or os.environ.get('OPENDART_API_KEY')
            if not key:
                self.log.stage('stage0', 'SKIPPED', step='fetch', reason='KRX code: no OPENDART_API_KEY')
                return
            self.harness.must('stage0', 'fetch', run_id, retryable=True, env={'OPENDART_API_KEY': key})
            self.log.stage('stage0', 'PASS', step='fetch', source='OpenDART')
            return
        ua = self.options.user_agent or os.environ.get('SEC_USER_AGENT')
        if not ua:
            self.log.stage('stage0', 'SKIPPED', step='fetch', reason='no --user-agent / SEC_USER_AGENT')
            return
        args = ['fetch', run_id]
        if run_id != self.ticker:
            cik = self._known_cik()
            if cik:
                args += ['--cik', str(cik)]
        self.harness.must('stage0', *args, retryable=True, env={'SEC_USER_AGENT': ua})
        self.log.stage('stage0', 'PASS', step='fetch', source='SEC EDGAR')

    def _known_cik(self):
        """A dated run id cannot be resolved by EDGAR; reuse the CIK recorded by the ticker's own run."""
        manifest = self.h.run_dir(self.ticker)/'sources'/'fetch_manifest.json'
        if manifest.exists():
            return json.loads(manifest.read_text(encoding='utf-8')).get('cik')
        return None


# ------------------------------------------------------------------------------ the batch

class BatchRunner:
    def __init__(self, store, reader, options):
        self.store, self.reader, self.options = store, reader, options
        started = datetime.now(timezone.utc)
        self.batch_id = started.strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}'
        self.log_dir = store.root/store.policy['paths']['logs_dir']/started.strftime('%Y-%m-%d')
        self.macro_lock_path = store.root/store.policy['paths']['macro_cache_dir']/'.universe-macro.lock'
        self.outcomes = []
        self.touched_runs = set()

    # ---------------------------------------------------------------- selection
    def select(self):
        universe = self.store.load()
        rows = Store.ordered(universe)
        wanted = set(self.options.tickers or ())
        chosen, skipped = [], []
        for row in rows:
            ticker = row['ticker']
            if wanted and ticker not in wanted:
                continue
            reason = self._skip_reason(row)
            if reason:
                skipped.append((ticker, reason))
            else:
                chosen.append(ticker)
        if self.options.limit:
            chosen = chosen[:self.options.limit]
        return chosen, skipped

    def _skip_reason(self, row):
        status = row.get('run_status')
        if status == 'COMPLETE':
            return 'complete'
        if status == 'FAILED' and not self.options.include_failed:
            return 'failed (use `universe retry`)'
        if row.get('security_type') in ('etf', 'fund') and not self.options.include_funds:
            return f"{row.get('security_type')}"
        if not row.get('as_of_date'):
            return 'no as_of_date'
        if status == 'RUNNING' and self.store.lock_held(row['ticker']):
            return 'running elsewhere'
        if self.options.only_started and not row.get('started'):
            return 'not started (continue resumes started tickers)'
        if self.options.eligible_only:
            art = self.reader.artifacts(row.get('run_id') or row['ticker'])
            inspection = self.reader.inspect(row.get('run_id') or row['ticker']) \
                if art['exists'] and art['freeze'].get('frozen') else None
            if not U.eligible_for_full_run(row, inspection):
                return 'not eligible (triage incomplete or no reachable archetype)'
        return None

    # ---------------------------------------------------------------- dry run
    def dry_run(self):
        """What would happen, without writing anything (no sync, no logs, no commands)."""
        universe = self.store.load()
        rows = Store.ordered(universe)
        chosen, skipped = self.select()
        statuses, lead = self.store.policy['statuses'], tuple(self.store.policy['runner'].get('lead_agents') or ())
        counts = {'tickers': len(rows), 'need_stage0': 0, 'already_triaged': 0, 'eligible_for_full_core': 0,
                  'complete': 0, 'early_exit': 0, 'blocked': 0, 'failed': 0, 'funds': 0}
        plan = []
        for row in rows:
            run_id = row.get('run_id') or row['ticker']
            art = self.reader.artifacts(run_id)
            inspection = self.reader.inspect(run_id) if art['exists'] and art['freeze'].get('frozen') else None
            action = U.determine_next_universe_action(art, inspection, statuses, self.options.stop_after, lead)
            if row.get('security_type') in ('etf', 'fund'):
                counts['funds'] += 1
            elif action['kind'] in ('init', 'stage0'):
                counts['need_stage0'] += 1
            if action['kind'] == 'complete':
                counts['complete'] += 1
                counts['early_exit'] += bool(action.get('early_exit'))
            elif inspection and inspection.get('triage_complete'):
                counts['already_triaged'] += 1
                counts['eligible_for_full_core'] += bool(U.eligible_for_full_run(row, inspection))
            counts['blocked'] += action['kind'] == 'blocked' or row.get('run_status') == 'BLOCKED'
            counts['failed'] += row.get('run_status') == 'FAILED'
            if row['ticker'] in chosen:
                plan.append({'ticker': row['ticker'], 'run_id': run_id, 'next': action['kind'], 'stage': action['stage'],
                             'agents': action.get('agents'), 'reason': action.get('reason')})
        return {'counts': counts, 'would_process': plan, 'skipped': skipped, 'options': self._options_record()}

    def _options_record(self):
        record = dataclasses.asdict(self.options)
        record['tickers'] = list(record['tickers'])
        for secret in ('user_agent', 'dart_key'):
            if record.get(secret):
                record[secret] = '(set)'
        return record

    # ---------------------------------------------------------------- run
    def run(self):
        chosen, skipped = self.select()
        started = utcnow()
        workers = max(1, min(int(self.options.workers or 1), int(self.store.policy['runner'].get('max_workers', 8))))
        if workers == 1:
            for ticker in chosen:
                self.outcomes.append(TickerJob(self, ticker).process())
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(TickerJob(self, t).process): t for t in chosen}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        self.outcomes.append(future.result())
                    except Exception as error:  # process() already isolates; this is a last resort
                        self.outcomes.append({'ticker': futures[future], 'outcome': 'failed', 'reason': repr(error)})
        self._macro_second_pass()
        summary = {'batch_id': self.batch_id, 'started_at': started, 'finished_at': utcnow(),
                   'options': self._options_record(), 'selected': chosen,
                   'skipped': [{'ticker': t, 'reason': r} for t, r in skipped],
                   'outcomes': sorted(self.outcomes, key=lambda o: o['ticker'])}
        counts = {}
        for o in self.outcomes:
            counts[o.get('outcome')] = counts.get(o.get('outcome'), 0) + 1
        summary['counts'] = counts
        self._write_batch_log(summary)
        self.store.write_snapshot()
        summary['dashboards'] = write_dashboards(self.store)
        if self.options.git_mode == 'batch':
            self._git_commit(f"universe: complete batch {self.batch_id[:8]}", self._git_paths(self.touched_runs))
        return summary

    def _macro_second_pass(self):
        """Parallel tickers can ask for MO before a sibling has cached fresh global components.
        Those that waited only for MO get one more pass once the cache is complete for their date."""
        rows = self.store.load()['tickers']
        h = self.reader.h
        needed = len(h.OVERLAY_POLICY['component_ttl_hours'])
        again = [o['ticker'] for o in self.outcomes
                 if o.get('outcome') == 'blocked' and o.get('awaiting') == ['MO']
                 and len(h.macro_cache_source(rows[o['ticker']]['as_of_date'])) == needed]
        for ticker in again:
            self.outcomes = [o for o in self.outcomes if o['ticker'] != ticker]
            self.outcomes.append(TickerJob(self, ticker).process())

    def _write_batch_log(self, summary):
        path = self.log_dir/'universe-run.json'
        with file_lock(path.with_suffix('.json.lock'), timeout=30):
            existing = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'batches': []}
            existing['batches'].append(summary)
            atomic_dump_json(path, existing)

    def after_ticker(self, ticker, outcome):
        row = self.store.load()['tickers'].get(ticker) or {}
        self.touched_runs.add(row.get('run_id') or ticker)
        if self.options.git_mode == 'per-ticker':
            self._git_commit(f"universe: {ticker} {outcome.get('outcome')} {row.get('stage')} {row.get('as_of_date')}",
                             self._git_paths({row.get('run_id') or ticker}))

    # ---------------------------------------------------------------- git
    def _git_paths(self, run_ids):
        root = self.store.root
        paths = [p for p in [*(f'runs/{r}' for r in sorted(run_ids)), self.store.policy['paths']['universe_dir'],
                             self.store.policy['paths']['logs_dir'], self.store.policy['paths']['reports_dir'],
                             self.store.policy['paths']['macro_cache_dir']] if self._has_files(root/p)]
        return paths

    @staticmethod
    def _has_files(path):
        return path.is_file() or (path.is_dir() and any(p.is_file() for p in path.rglob('*')))

    def _git_commit(self, message, paths):
        if not paths:
            return
        with _GIT_LOCK:
            root = self.store.root
            try:
                subprocess.run(['git', 'add', '--', *paths], cwd=root, check=True, capture_output=True, text=True)
                staged = subprocess.run(['git', 'diff', '--cached', '--quiet', '--', *paths], cwd=root)
                if staged.returncode == 0:
                    return
                subprocess.run(['git', 'commit', '-m', message, '--', *paths], cwd=root, check=True,
                               capture_output=True, text=True)
            except (OSError, subprocess.CalledProcessError) as error:
                detail = getattr(error, 'stderr', '') or str(error)
                print(f'git ({self.options.git_mode}) skipped: {detail.strip()[:300]}', file=sys.stderr)


# ------------------------------------------------------------------------------ CLI

def _options(args, **overrides):
    policy = overrides.pop('policy')
    runner = policy['runner']
    stop = 'triage' if getattr(args, 'triage_only', False) else getattr(args, 'stage', None)
    if stop and stop not in policy['statuses']['stages']:
        raise SystemExit(f"--stage must be one of {', '.join(policy['statuses']['stages'])}")
    workers = getattr(args, 'workers', None) or runner.get('default_workers', 1)
    if workers < 1 or workers > runner.get('max_workers', 8):
        raise SystemExit(f"--workers must be between 1 and {runner.get('max_workers', 8)}")
    git_mode = getattr(args, 'git', None) or runner.get('default_git_mode', 'none')
    return Options(stop_after=stop, eligible_only=getattr(args, 'eligible_only', False),
                   include_failed=getattr(args, 'include_failed', False),
                   include_funds=getattr(args, 'include_funds', False),
                   tickers=tuple(overrides.pop('tickers', ()) or ()), workers=workers,
                   dry_run=getattr(args, 'dry_run', False), agent_cmd=getattr(args, 'agent_cmd', None),
                   user_agent=getattr(args, 'user_agent', None), dart_key=getattr(args, 'dart_key', None),
                   provider=getattr(args, 'provider', None),
                   model=getattr(args, 'model', None), reasoning_effort=getattr(args, 'reasoning_effort', None),
                   git_mode=git_mode, report=not getattr(args, 'no_report', False),
                   agent_timeout=getattr(args, 'agent_timeout', None) or runner.get('agent_timeout_seconds', 3600),
                   command_timeout=runner.get('command_timeout_seconds', 900),
                   max_cycles=runner.get('max_cycles_per_ticker', 40), limit=getattr(args, 'limit', None),
                   **overrides)


def _context():
    from . import runtime
    return Store(runtime.ROOT), RunReader(runtime)


def _normalized(store, names):
    out = []
    universe = store.load()
    for raw in names or ():
        ticker, _, reason = U.normalize_ticker(raw, store.policy['import'])
        if reason or ticker not in universe['tickers']:
            raise SystemExit(f'{raw}: not in the universe')
        out.append(ticker)
    return out


def execute(args, only_started=False, tickers=None, include_failed=None):
    store, reader = _context()
    options = _options(args, policy=store.policy, only_started=only_started,
                       tickers=tickers if tickers is not None else _normalized(store, getattr(args, 'tickers', None)))
    if include_failed is not None:
        options.include_failed = include_failed
    runner = BatchRunner(store, reader, options)
    if options.dry_run:
        _print_dry_run(runner.dry_run())
        return
    summary = runner.run()
    _print_summary(summary, store)


def _print_dry_run(result):
    c = result['counts']
    print(f"{c['tickers']} tickers")
    print(f"{c['need_stage0']} need Stage 0")
    print(f"{c['already_triaged']} already triaged")
    print(f"{c['eligible_for_full_core']} eligible for full core")
    print(f"{c['complete']} complete ({c['early_exit']} early exit)")
    print(f"{c['blocked']} blocked, {c['failed']} failed, {c['funds']} ETF/fund")
    print('\nwould process:' if result['would_process'] else '\nnothing to process')
    for item in result['would_process']:
        extra = f" {item['agents']}" if item.get('agents') else ''
        why = f" — {item['reason']}" if item.get('reason') else ''
        print(f"  {item['ticker']:<8} next={item['next']:<9} stage={item['stage']}{extra}{why}")
    for ticker, reason in result['skipped']:
        print(f'  skip {ticker}: {reason}')
    print('\ndry run: no files were written and no commands were executed')


def _print_summary(summary, store):
    counts = ', '.join(f'{k} {v}' for k, v in sorted(summary['counts'].items())) or 'nothing to do'
    print(f"batch {summary['batch_id']}: {len(summary['selected'])} selected — {counts}")
    rows = store.load()['tickers']
    for o in summary['outcomes']:
        row = rows.get(o['ticker'], {})
        detail = o.get('reason') or ''
        print(f"  {o['ticker']:<8} {U.display_status(row) or o.get('outcome'):<10} {row.get('stage') or '':<22} {detail}"[:220])
    for item in summary['skipped']:
        print(f"  skip {item['ticker']}: {item['reason']}")


def cmd_run(args):
    execute(args)


def cmd_continue(args):
    execute(args, only_started=True)


def cmd_retry(args):
    store, _ = _context()
    tickers = _normalized(store, args.tickers)
    for ticker in tickers:
        if store.lock_held(ticker):
            raise SystemExit(f'{ticker}: a runner holds this ticker')
        store.update_row(ticker, lambda r: r.update(run_status='QUEUED', last_error=None, blocked_reason=None))
    execute(args, tickers=tickers, include_failed=True)


def _runner_flags(p, stage_choices):
    p.add_argument('--stage', choices=stage_choices, help='stop after this stage (planner still decides the work)')
    p.add_argument('--triage-only', action='store_true', help='Stage 0, EV, AS/DI/FS and the early-exit decision only')
    p.add_argument('--eligible-only', action='store_true', help='only tickers with a reachable archetype after triage')
    p.add_argument('--workers', type=int, help='parallel tickers (stages of one ticker are always sequential)')
    p.add_argument('--dry-run', action='store_true', help='show the plan; write nothing, run nothing')
    p.add_argument('--agent-cmd', help='command template producing one agent report: {prompt} {output} {agent} {run_id} {ticker} {as_of} {root}')
    p.add_argument('--agent-timeout', type=float)
    p.add_argument('--user-agent', help='SEC EDGAR contact for Stage 0 fetch (or SEC_USER_AGENT)')
    p.add_argument('--dart-key', help='OpenDART key for KRX tickers (or OPENDART_API_KEY); never logged')
    p.add_argument('--provider'); p.add_argument('--model'); p.add_argument('--reasoning-effort')
    p.add_argument('--git', choices=['none', 'per-ticker', 'batch'], help='commit mode (default none; never pushes)')
    p.add_argument('--no-report', action='store_true', help='skip `report` after a ticker completes')
    p.add_argument('--include-failed', action='store_true'); p.add_argument('--include-funds', action='store_true')
    p.add_argument('--limit', type=int)


def register(us, stage_choices):
    for name, func, text in (('run', cmd_run, 'advance queued/blocked tickers through the planner'),
                             ('continue', cmd_continue, 'resume tickers that have already started')):
        p = us.add_parser(name, help=text)
        p.add_argument('tickers', nargs='*')
        _runner_flags(p, stage_choices)
        p.set_defaults(func=func)
    p = us.add_parser('retry', help='re-queue FAILED tickers and run them')
    p.add_argument('tickers', nargs='+')
    _runner_flags(p, stage_choices)
    p.set_defaults(func=cmd_retry)
