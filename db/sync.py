"""Load the file artifacts into the database, idempotently.

Running `db sync` twice must leave the same database as running it once. Every
loader is therefore keyed on something stable: a regulator identity, an
accession number, a content hash of a fact, a run's `aggregate_sha256`.

Two kinds of row live here and they are governed differently.

**Decisions are appended.** A harness run, a screen run and a deep dive are
records of what was concluded at a point in time. Re-aggregating a run inserts
a new `harness_run` row and moves `is_current`; the old row stays, because a
table that updated in place would erase the fact that a number changed.

**Computations are replaced.** A `screening_metric` row is the output of a
formula over a pack. Recomputing it with a corrected definition should change
it — that is the point of having the definition in config — so these are
upserted on `(ticker, as_of_date, metric)`.

Monitoring splits along the same line. A watch item is derived from a report,
so it is upserted; an observation is a record of what somebody saw, so it is
inserted once and never touched again.

Nothing here writes back to a file. The artifacts remain the source of truth
and this layer only ever reads them.
"""
import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import select, update

from .models import (DeepDive, Filing, FinancialFact, HarnessRun, Issuer, Job, MarketSnapshot,
                     MonitoringObservation, MonitoringWatchItem, ScreenRun, ScreeningMetric,
                     Security, SyncLog)

ROOT = Path(__file__).resolve().parents[1]


def _date(value) -> Optional[date]:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _number(value) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


# The metric column is NUMERIC(38,10), so a float round-trips through the
# database slightly changed. Comparing the in-memory value against the stored
# one without accounting for that marks every row as updated on every sync,
# forever. Quantising to the column's own scale before comparing and storing
# makes a re-sync genuinely idempotent.
METRIC_SCALE = 10


def _quantize(value: Optional[float], places: int = METRIC_SCALE) -> Optional[float]:
    return None if value is None else round(float(value), places)


def _changed(existing, fields: dict) -> bool:
    for key, value in fields.items():
        current = getattr(existing, key)
        if isinstance(value, float) or isinstance(current, float):
            if current is None or value is None:
                if current is not value:
                    return True
            elif abs(float(current) - float(value)) > 1e-9 * max(1.0, abs(float(value))):
                return True
        elif current != value:
            return True
    return False


def content_hash(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                     default=str).encode('utf-8')).hexdigest()


class Counts(dict):
    """inserted / updated / skipped, with a readable sum."""

    def __init__(self, **kwargs):
        super().__init__(inserted=0, updated=0, skipped=0, **kwargs)

    def bump(self, key: str, amount: int = 1) -> None:
        self[key] = self.get(key, 0) + amount

    @property
    def touched(self) -> int:
        return self['inserted'] + self['updated']


def _log(session, kind: str, source: Optional[str], counts: Counts, detail=None) -> None:
    session.add(SyncLog(kind=kind, source=source, inserted=counts['inserted'],
                        updated=counts['updated'], skipped=counts['skipped'],
                        detail=detail, started_at=datetime.now(timezone.utc),
                        finished_at=datetime.now(timezone.utc)))


# ------------------------------------------------------------------- entities
def upsert_issuer(session, row: dict) -> Issuer:
    """Get or create by regulator identity. Never duplicates an issuer."""
    regulator = row.get('regulator')
    regulator_id = str(row.get('regulator_issuer_id') or '').strip()
    existing = session.scalar(select(Issuer).where(
        Issuer.regulator == regulator, Issuer.regulator_issuer_id == regulator_id))
    if existing is not None:
        return existing
    month = (row.get('extra') or {}).get('accounting_month')
    issuer = Issuer(
        jurisdiction=row.get('jurisdiction'), regulator=regulator,
        regulator_issuer_id=regulator_id, legal_name=row.get('legal_name') or regulator_id,
        industry=row.get('industry'), sector=row.get('sector'),
        fiscal_year_end_month=int(month) if str(month or '').isdigit() else None,
        extra=row.get('extra'))
    session.add(issuer)
    session.flush()
    return issuer


def sync_universe(session, payload: dict) -> Counts:
    """Issuers and securities from `harness.py universe sync` output."""
    counts = Counts()
    issuers: dict = {}
    for row in payload.get('securities') or []:
        issuer_key = row.get('issuer_key') or ''
        regulator, _, regulator_id = issuer_key.partition(':')
        issuer = None
        if regulator and regulator_id:
            if issuer_key not in issuers:
                issuers[issuer_key] = upsert_issuer(session, {
                    'jurisdiction': 'KR' if regulator == 'DART' else 'US',
                    'regulator': regulator, 'regulator_issuer_id': regulator_id,
                    'legal_name': row.get('name') or regulator_id})
            issuer = issuers[issuer_key]

        ticker, exchange = row.get('ticker'), row.get('exchange')
        if not ticker or not exchange:
            counts.bump('skipped')
            continue
        existing = session.scalar(select(Security).where(
            Security.exchange == exchange, Security.ticker == ticker))
        fields = {'issuer_id': issuer.issuer_id if issuer else None,
                  'currency': row.get('currency') or 'USD',
                  'security_type': row.get('security_type') or 'common',
                  'name': row.get('name'), 'active': bool(row.get('active', True)),
                  'excluded_reason': row.get('excluded_reason'),
                  'requires_review': bool(row.get('requires_review'))}
        if existing is None:
            session.add(Security(ticker=ticker, exchange=exchange, **fields))
            counts.bump('inserted')
        elif _changed(existing, fields):
            for key, value in fields.items():
                setattr(existing, key, value)
            counts.bump('updated')
        else:
            counts.bump('skipped')
    _log(session, 'universe', payload.get('synced_at_utc'), counts,
         {'markets': list((payload.get('markets') or {}).keys())})
    return counts


# --------------------------------------------------------------------- facts
def fact_key(issuer_key: str, fact: dict) -> str:
    """A content hash, so re-syncing a pack does not duplicate its corpus."""
    return content_hash([issuer_key, fact.get('metric'), fact.get('metric_detail'),
                         fact.get('statement'), fact.get('period_kind'),
                         fact.get('period_start'), fact.get('period_end'),
                         fact.get('fiscal_year'), fact.get('fiscal_quarter'),
                         fact.get('segment'), fact.get('value_reported'),
                         fact.get('scale_multiplier'), fact.get('currency'),
                         fact.get('source_document'), fact.get('filing_date')])


ACCESSION_MAX = 64


def filing_accession(source_document: Optional[str]) -> Optional[str]:
    """A bounded, stable key for a document.

    The adapters name documents `{form}_{date}_{accession}`, so the trailing
    token is the real accession. Packs written by hand carry human filenames
    instead — "AVGO (Broadcom Inc.) Annual Report to Security Holders (ARS)
    2026-03-02.docx" — which are neither bounded nor an identifier. Those get a
    content-derived key, which is stable across syncs and fits the column.
    """
    name = str(source_document or '').strip()
    if not name:
        return None
    stem = name.rsplit('.', 1)[0]
    tail = stem.rsplit('_', 1)[-1]
    if tail and tail != stem and len(tail) <= ACCESSION_MAX:
        return tail
    if len(stem) <= ACCESSION_MAX:
        return stem
    return 'doc-' + content_hash([name])[:32]


def sync_pack(session, pack: dict, issuer_row: Optional[dict] = None,
              ticker: Optional[str] = None) -> Counts:
    """Filings and facts from one Stage 0 pack."""
    counts = Counts()
    ticker = (ticker or pack.get('ticker') or '').upper()
    ingestion = pack.get('ingestion') or {}
    basis = pack.get('consolidation_basis') or ingestion.get('consolidation_basis')
    issuer = upsert_issuer(session, issuer_row) if issuer_row else None
    issuer_key = issuer.issuer_key if issuer else f'TICKER:{ticker}'
    pack_sha = content_hash(pack)

    filings: dict = {}
    for document in pack.get('documents') or []:
        name = document.get('source_document')
        accession = filing_accession(name)
        if not accession:
            continue
        regulator = ingestion.get('regulator') or ('DART' if (pack.get('reporting_currency')
                                                              == 'KRW') else 'SEC')
        existing = session.scalar(select(Filing).where(
            Filing.regulator == regulator, Filing.accession == accession))
        if existing is None:
            existing = Filing(
                issuer_id=issuer.issuer_id if issuer else None, regulator=regulator,
                form_type=document.get('document_type') or 'other', accession=accession,
                filing_date=_date(document.get('filing_date')),
                period_end=_date(document.get('period_end')),
                is_amendment=bool(document.get('is_amendment')), source_document=name)
            session.add(existing)
            session.flush()
            counts.bump('inserted')
        else:
            counts.bump('skipped')
        filings[name] = existing

    seen = set(session.scalars(select(FinancialFact.fact_key).where(
        FinancialFact.ticker == ticker)).all())
    for fact in pack.get('facts') or []:
        key = fact_key(issuer_key, fact)
        if key in seen:
            counts.bump('skipped')
            continue
        seen.add(key)
        filing = filings.get(fact.get('source_document'))
        period_kind = fact.get('period_kind')
        session.add(FinancialFact(
            fact_key=key, issuer_id=issuer.issuer_id if issuer else None,
            filing_id=filing.filing_id if filing else None, ticker=ticker,
            metric=fact.get('metric'), metric_detail=fact.get('metric_detail'),
            reported_label=fact.get('reported_label'), statement=fact.get('statement') or 'other',
            value=_number(fact.get('value_reported')),
            unit_kind=fact.get('unit_kind') or 'currency', currency=fact.get('currency'),
            scale_multiplier=float(fact.get('scale_multiplier') or 1.0),
            period_start=_date(fact.get('period_start')), period_end=_date(fact.get('period_end')),
            period_kind=period_kind, fiscal_year=fact.get('fiscal_year'),
            fiscal_quarter=fact.get('fiscal_quarter') if period_kind != 'fy' else None,
            segment=fact.get('segment'), filing_date=_date(fact.get('filing_date')),
            source_document=fact.get('source_document'), source_locator=fact.get('source_locator'),
            consolidation_basis=basis, gaap_status=fact.get('gaap_status'),
            confidence=_number(fact.get('confidence')),
            requires_review=bool(fact.get('requires_review')),
            review_reason=fact.get('review_reason'),
            is_amended=bool(fact.get('is_amended')), is_restated=bool(fact.get('is_restated')),
            pack_sha256=pack_sha))
        counts.bump('inserted')
    _log(session, 'pack', ticker, counts, {'pack_sha256': pack_sha, 'basis': basis})
    return counts


# ----------------------------------------------------------------- run index
def sync_runs(session, rows: Iterable[dict], runs_dir=None) -> Counts:
    """Index completed harness runs. Append-only; `is_current` moves."""
    counts = Counts()
    base = Path(runs_dir or ROOT / 'runs')
    for row in rows:
        digest = row.get('result_sha256')
        run_id = row.get('run_id')
        if not digest or not run_id:
            counts.bump('skipped')
            continue
        existing = session.scalar(select(HarnessRun).where(
            HarnessRun.run_id == run_id, HarnessRun.aggregate_sha256 == digest))
        if existing is not None:
            counts.bump('skipped')
            continue
        # A new version of a run does not overwrite the old one; it supersedes it.
        session.execute(update(HarnessRun).where(HarnessRun.run_id == run_id)
                        .values(is_current=False))
        domain_scores = row.get('domain_scores') or {}
        session.add(HarnessRun(
            run_id=run_id, ticker=(row.get('ticker') or run_id).upper(),
            company_name=row.get('company_name'), jurisdiction=row.get('jurisdiction'),
            exchange=row.get('exchange'), currency=row.get('currency'),
            as_of_date=_date(row.get('as_of_date')),
            stage='complete' if row.get('full_harness_complete') else (
                'triage' if row.get('triage_complete') else 'partial'),
            core_score=_number(row.get('core_score')),
            ex_valuation_score=_number(row.get('ex_valuation_score')),
            coverage_weight=_number(row.get('coverage_weight')),
            classification=row.get('classification'), archetype=row.get('archetype'),
            hard_veto_status=row.get('hard_veto_status'), ic_state=row.get('ic_state'),
            position_range=row.get('position_range'),
            price_to_base_value=_number(row.get('price_to_base_value')),
            market_cap_usd=_number(row.get('market_cap_usd')),
            current_price=_number(row.get('current_price')),
            net_cash_per_share=_number(row.get('net_cash_per_share')),
            dilution_watch_status=row.get('dilution_watch_status'),
            early_exit=bool(row.get('early_exit')),
            full_harness_complete=bool(row.get('full_harness_complete')),
            triage_complete=bool(row.get('triage_complete')),
            domain_scores=domain_scores, axis_scores=row.get('axis_scores') or {},
            strategy_version=row.get('strategy_version'),
            decision_policy_version=row.get('decision_policy_version'),
            input_snapshot_sha256=row.get('input_snapshot_sha256'),
            aggregate_sha256=digest, frozen=bool(row.get('frozen')),
            artifact_uri=str((base / run_id / (row.get('result_source') or 'aggregate.json'))
                             .relative_to(ROOT)) if base == ROOT / 'runs'
                         else str(base / run_id / (row.get('result_source') or 'aggregate.json')),
            is_current=True))
        counts.bump('inserted')
    _log(session, 'runs', str(base), counts)
    return counts


# ------------------------------------------------------------------ computed
def sync_warehouse(session, payload: dict) -> Counts:
    """Screening metrics. Upserted, because a metric is a computation."""
    counts = Counts()
    as_of = _date(payload.get('as_of_date'))
    for row in payload.get('rows') or []:
        ticker = (row.get('ticker') or '').upper()
        if not ticker:
            counts.bump('skipped')
            continue
        security = session.scalar(select(Security).where(Security.ticker == ticker))
        provenance = row.get('provenance') or {}
        for metric, value in (row.get('metrics') or {}).items():
            detail = provenance.get(metric) or {}
            existing = session.scalar(select(ScreeningMetric).where(
                ScreeningMetric.ticker == ticker, ScreeningMetric.as_of_date == as_of,
                ScreeningMetric.metric == metric))
            fields = {
                'security_id': security.security_id if security else None,
                'value': _quantize(_number(value)), 'currency': row.get('currency'),
                'method': detail.get('method'),
                # A NULL value with a reason is a recorded refusal, which is a
                # different fact from the metric never having been attempted.
                'unavailable_reason': detail.get('reason') if value is None else None,
                'requires_review': bool(detail.get('requires_review')),
                'provenance': detail,
                'inputs_sha256': content_hash(detail.get('inputs') or [])}
            if existing is None:
                session.add(ScreeningMetric(ticker=ticker, as_of_date=as_of, metric=metric,
                                            **fields))
                counts.bump('inserted')
            elif _changed(existing, fields):
                for key, value_ in fields.items():
                    setattr(existing, key, value_)
                counts.bump('updated')
            else:
                counts.bump('skipped')
    _log(session, 'warehouse', payload.get('as_of_date'), counts,
         {'companies': payload.get('companies')})
    return counts


def sync_market_snapshots(session, snapshots: Iterable[dict]) -> Counts:
    counts = Counts()
    for row in snapshots:
        ticker = (row.get('ticker') or '').upper()
        as_of = _date(row.get('as_of_date'))
        source = row.get('source') or 'unknown'
        if not ticker or as_of is None:
            counts.bump('skipped')
            continue
        security = session.scalar(select(Security).where(Security.ticker == ticker))
        existing = session.scalar(select(MarketSnapshot).where(
            MarketSnapshot.ticker == ticker, MarketSnapshot.as_of_date == as_of,
            MarketSnapshot.source == source))
        if existing is not None:
            counts.bump('skipped')
            continue
        session.add(MarketSnapshot(
            security_id=security.security_id if security else None, ticker=ticker,
            as_of_date=as_of, close=_number(row.get('close')),
            market_cap=_number(row.get('market_cap')),
            shares_outstanding=_number(row.get('shares_outstanding')),
            currency=row.get('currency'), source=source))
        counts.bump('inserted')
    _log(session, 'market', None, counts)
    return counts


# ------------------------------------------------------------------ outcomes
def sync_screen_runs(session, records: Iterable[dict]) -> Counts:
    """Screens are written once; an existing id is left untouched."""
    counts = Counts()
    for record in records:
        run_id = record.get('screen_run_id')
        if not run_id or session.get(ScreenRun, run_id) is not None:
            counts.bump('skipped')
            continue
        summary = record.get('summary') or {}
        session.add(ScreenRun(
            screen_run_id=run_id, as_of_date=_date(record.get('as_of_date')),
            spec_id=(record.get('spec') or {}).get('spec_id'), backend=record.get('backend'),
            query_text=((record.get('spec') or {}).get('source') or {}).get('text'),
            matched_count=summary.get('matched_count'), considered=summary.get('considered'),
            spec=record.get('spec'), summary=summary, results=record.get('results'),
            content_sha256=record.get('content_sha256'),
            code_commit_sha=(record.get('provenance') or {}).get('code_commit_sha')))
        counts.bump('inserted')
    _log(session, 'screen_runs', None, counts)
    return counts


def sync_deep_dives(session, reports: Iterable[dict]) -> Counts:
    counts = Counts()
    for report in reports:
        metadata = report.get('metadata') or {}
        deep_dive_id = metadata.get('deep_dive_id')
        if not deep_dive_id or session.get(DeepDive, deep_dive_id) is not None:
            counts.bump('skipped')
            continue
        session.add(DeepDive(
            deep_dive_id=deep_dive_id, run_id=(metadata.get('harness_run') or {}).get('run_id'),
            ticker=(metadata.get('ticker') or '').upper(),
            company_name=metadata.get('company_name'), jurisdiction=metadata.get('jurisdiction'),
            as_of_date=_date(metadata.get('as_of_date')),
            route=((report.get('final_synthesis') or {}).get('agreement_with_harness')),
            red_team_overall=(report.get('red_team') or {}).get('overall'),
            agreement_with_harness=(report.get('final_synthesis') or {})
                                   .get('agreement_with_harness'),
            report=report,
            provider_metadata=(metadata.get('provenance') or {}).get('stages'),
            content_sha256=content_hash(report)))
        counts.bump('inserted')
    _log(session, 'deep_dives', None, counts)
    return counts


def sync_watchlist(session, watchlist: dict) -> Counts:
    """Watch items are derived from reports, so they are upserted, not appended."""
    counts = Counts()
    for item in watchlist.get('items') or []:
        thresholds = item.get('thresholds') or {}
        fields = {
            'ticker': (item.get('ticker') or '').upper(), 'run_id': item.get('run_id'),
            'kind': item['kind'], 'name': item['name'],
            'source_kind': item['source_kind'], 'source_ref': item.get('source_ref'),
            'as_of_date': _date(item.get('as_of_date')), 'cadence': item.get('cadence'),
            'direction_required': item.get('direction_required'),
            'warning_threshold': _text(thresholds.get('warning')),
            'thesis_break_threshold': _text(thresholds.get('thesis_break')),
            'comparison': item.get('comparison'),
            'machine_checkable': bool(item.get('machine_checkable')),
            'not_machine_checkable_reason': item.get('not_machine_checkable_reason'),
        }
        existing = session.get(MonitoringWatchItem, item['watch_id'])
        if existing is None:
            session.add(MonitoringWatchItem(watch_id=item['watch_id'], **fields))
            counts.bump('inserted')
        elif _changed(existing, fields):
            for key, value in fields.items():
                setattr(existing, key, value)
            counts.bump('updated')
        else:
            counts.bump('skipped')
    _log(session, 'monitoring_watchlist', watchlist.get('ticker'), counts)
    return counts


def sync_observations(session, rows: Iterable[dict]) -> Counts:
    """Append-only: an observation already present is left exactly as it is."""
    counts = Counts()
    ticker = None
    for row in rows:
        observation_id = row.get('observation_id')
        ticker = ticker or row.get('ticker')
        if not observation_id or session.get(MonitoringObservation, observation_id) is not None:
            counts.bump('skipped')
            continue
        value = row.get('value')
        number, unit = _observed_scale(value, row.get('unit'))
        session.add(MonitoringObservation(
            observation_id=observation_id, ticker=(row.get('ticker') or '').upper(),
            watch_id=row['watch_id'],
            value_text=None if value is None else str(value),
            value_number=number, unit=unit,
            triggered=row.get('triggered'), period=row.get('period'),
            as_of_date=_date(row.get('as_of_date')), source=row.get('source') or '',
            source_type=row.get('source_type') or 'other',
            fact_or_estimate=row.get('fact_or_estimate') or 'fact',
            note=row.get('note'), supersedes=row.get('supersedes'),
            pre_analysis=bool(row.get('pre_analysis')),
            recorded_at_utc=row.get('recorded_at_utc')))
        counts.bump('inserted')
    _log(session, 'monitoring_observations', ticker, counts)
    return counts


def _text(value) -> Optional[str]:
    return None if value is None else str(value)


def _observed_scale(value, declared_unit) -> tuple:
    """`(number, unit)` exactly as written — never rescaled on a guess.

    The pair travels together and a NULL unit is meaningful: it says the
    recorder did not state a scale, which is the same thing the evaluator
    refuses to guess at. A query that reads `value_number` alone and ignores
    `unit` is reading half a fact.
    """
    if value is None or isinstance(value, bool):
        return None, declared_unit
    if isinstance(value, (int, float)):
        return float(value), declared_unit
    text = str(value)
    match = re.search(r'-?\d+(?:[.,]\d+)?', text)
    if not match:
        return None, declared_unit
    number = float(match.group(0).replace(',', ''))
    if declared_unit:
        return number, declared_unit
    if re.search(r'%\s*p|%p|퍼센트\s*포인트|\bpp\b', text, re.I):
        return number, 'percent_point'
    if re.search(r'%|퍼센트|percent|pct', text, re.I):
        return number, 'percent'
    return number, None


def enqueue(session, kind: str, payload: dict, idempotency_key: Optional[str] = None) -> Job:
    """Queue work. The same key twice returns the same job, never a duplicate."""
    key = idempotency_key or content_hash([kind, payload])
    existing = session.scalar(select(Job).where(Job.idempotency_key == key))
    if existing is not None:
        return existing
    job = Job(kind=kind, status='queued', idempotency_key=key, payload=payload)
    session.add(job)
    session.flush()
    return job
