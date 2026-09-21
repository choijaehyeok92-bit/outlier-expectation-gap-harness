"""Read side: the database answering the questions the files answered.

The contract is that a screen gets the same row shape whether it came from
`runs/` or from Postgres, so the deterministic compiler needs no knowledge of
where a row was stored. `merged_rows` therefore hands its output through the
same `merge_row` the file path uses, rather than reimplementing the precedence
rule and slowly drifting from it.

Reads are point-in-time. A run or a metric dated after the cutoff is not
returned, here as everywhere else.
"""
from typing import Optional

from sqlalchemy import func, select

from .models import (DeepDive, Filing, FinancialFact, HarnessRun, Issuer, Job, MarketSnapshot,
                     ScreenRun, ScreeningMetric, Security, SyncLog)


def _iso(value) -> Optional[str]:
    return value.isoformat() if hasattr(value, 'isoformat') else (value or None)


def harness_run_rows(session, as_of_date: Optional[str] = None,
                     current_only: bool = True) -> list:
    """Indexed runs in the shape `packages.screening.runs_index` produces."""
    query = select(HarnessRun)
    if current_only:
        query = query.where(HarnessRun.is_current.is_(True))
    rows = []
    for run in session.scalars(query).all():
        as_of = _iso(run.as_of_date)
        if as_of_date and (as_of or '') > as_of_date:
            continue
        rows.append({
            'run_id': run.run_id, 'ticker': run.ticker, 'company_name': run.company_name,
            'jurisdiction': run.jurisdiction, 'exchange': run.exchange, 'currency': run.currency,
            'as_of_date': as_of, 'market_cap_usd': run.market_cap_usd,
            'current_price': run.current_price, 'net_cash_per_share': run.net_cash_per_share,
            'core_score': run.core_score, 'ex_valuation_score': run.ex_valuation_score,
            'coverage_weight': run.coverage_weight, 'classification': run.classification,
            'archetype': run.archetype, 'hard_veto_status': run.hard_veto_status,
            'ic_state': run.ic_state, 'position_range': run.position_range,
            'price_to_base_value': run.price_to_base_value,
            'dilution_watch_status': run.dilution_watch_status,
            'domain_scores': run.domain_scores or {}, 'axis_scores': run.axis_scores or {},
            'early_exit': run.early_exit, 'triage_complete': run.triage_complete,
            'full_harness_complete': run.full_harness_complete,
            'strategy_version': run.strategy_version,
            'decision_policy_version': run.decision_policy_version,
            'input_snapshot_sha256': run.input_snapshot_sha256, 'frozen': run.frozen,
            'result_sha256': run.aggregate_sha256, 'artifact_uri': run.artifact_uri,
        })
    return rows


def warehouse_rows(session, as_of_date: Optional[str] = None) -> list:
    """Screening metrics, one flat row per company, latest date at or before the cutoff."""
    query = select(ScreeningMetric)
    metrics = session.scalars(query).all()
    latest: dict = {}
    for row in metrics:
        as_of = _iso(row.as_of_date)
        if as_of_date and (as_of or '') > as_of_date:
            continue
        current = latest.get(row.ticker)
        if current is None or (as_of or '') >= current['as_of_date']:
            if current is None or (as_of or '') > current['as_of_date']:
                latest[row.ticker] = {'ticker': row.ticker, 'as_of_date': as_of or '',
                                      'currency': row.currency,
                                      'warehouse_unavailable': [],
                                      'warehouse_requires_review': []}
            entry = latest[row.ticker]
            entry['currency'] = entry.get('currency') or row.currency
            if row.value is not None:
                entry[row.metric] = row.value
            else:
                entry['warehouse_unavailable'].append(row.metric)
            if row.requires_review:
                entry['warehouse_requires_review'].append(row.metric)
    for entry in latest.values():
        entry['warehouse_unavailable'].sort()
        entry['warehouse_requires_review'].sort()
    return list(latest.values())


def merged_rows(session, as_of_date: Optional[str] = None,
                fx_rates: Optional[dict] = None) -> list:
    """The screening compiler's input, assembled from the database.

    Same precedence as the file path, by construction: it calls the same
    function rather than restating the rule.
    """
    from packages.screening.rows import merge_row

    harness = {}
    for row in sorted(harness_run_rows(session, as_of_date),
                      key=lambda r: r.get('as_of_date') or ''):
        harness[(row.get('ticker') or '').upper()] = row
    metrics = {(row.get('ticker') or '').upper(): row
               for row in warehouse_rows(session, as_of_date)}
    return [merge_row(harness.get(ticker), metrics.get(ticker), fx_rates)
            for ticker in sorted(set(harness) | set(metrics))]


def company(session, ticker: str) -> dict:
    """Everything the database knows about one company."""
    upper = ticker.upper()
    runs = [row for row in harness_run_rows(session, current_only=False)
            if row['ticker'] == upper]
    runs.sort(key=lambda r: (r.get('as_of_date') or '', r.get('result_sha256') or ''), reverse=True)
    security = session.scalar(select(Security).where(Security.ticker == upper))
    metrics = [row for row in warehouse_rows(session) if row['ticker'] == upper]
    dives = session.scalars(select(DeepDive).where(DeepDive.ticker == upper)).all()
    facts = session.scalar(select(func.count()).select_from(FinancialFact)
                           .where(FinancialFact.ticker == upper)) or 0
    return {
        'ticker': upper,
        'security': {'exchange': security.exchange, 'currency': security.currency,
                     'security_type': security.security_type, 'name': security.name,
                     'excluded_reason': security.excluded_reason} if security else None,
        'harness_runs': runs,
        'screening_metrics': metrics[0] if metrics else None,
        'financial_facts': facts,
        'deep_dives': [{'deep_dive_id': d.deep_dive_id, 'as_of_date': _iso(d.as_of_date),
                        'red_team_overall': d.red_team_overall,
                        'agreement_with_harness': d.agreement_with_harness} for d in dives],
    }


def status(session) -> dict:
    """Row counts plus the last sync of each kind, for `db status`."""
    tables = {'issuer': Issuer, 'security': Security, 'filing': Filing,
              'financial_fact': FinancialFact, 'market_snapshot': MarketSnapshot,
              'screening_metric': ScreeningMetric, 'harness_run': HarnessRun,
              'screen_run': ScreenRun, 'deep_dive': DeepDive, 'job': Job, 'sync_log': SyncLog}
    counts = {name: session.scalar(select(func.count()).select_from(model)) or 0
              for name, model in tables.items()}
    recent = session.scalars(select(SyncLog).order_by(SyncLog.sync_id.desc()).limit(8)).all()
    return {
        'rows': counts,
        'current_harness_runs': session.scalar(
            select(func.count()).select_from(HarnessRun)
            .where(HarnessRun.is_current.is_(True))) or 0,
        'superseded_harness_runs': session.scalar(
            select(func.count()).select_from(HarnessRun)
            .where(HarnessRun.is_current.is_(False))) or 0,
        'metrics_unavailable': session.scalar(
            select(func.count()).select_from(ScreeningMetric)
            .where(ScreeningMetric.value.is_(None))) or 0,
        'recent_syncs': [{'kind': row.kind, 'source': row.source, 'inserted': row.inserted,
                          'updated': row.updated, 'skipped': row.skipped,
                          'finished_at': row.finished_at.isoformat() if row.finished_at else None}
                         for row in recent],
    }
