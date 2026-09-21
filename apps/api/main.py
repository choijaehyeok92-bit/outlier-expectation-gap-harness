"""Read-mostly API over the harness, the screener and the deep dive.

Three boundaries are worth naming, because they are what this service is for.

It never computes a harness result. `/api/runs` and `/api/companies` read what
the harness already wrote and hand it over unchanged; nothing in this process
recomputes a score, an archetype, a veto status or a valuation.

It never lets a model reach the data layer. `/api/screen/parse` turns text into
a ScreeningSpec and stops there. Execution happens in the deterministic
compiler, over an allowlisted field registry, and a condition the parser could
not resolve comes back in `unresolved_conditions` instead of quietly vanishing.

It never returns a secret. Provider keys are read inside the provider classes
from the environment; no route accepts one and no response echoes one.

The stages that Phase 3 and beyond will add — SEC/DART ingestion, the metric
warehouse, batch triage and full-harness orchestration — answer 501 with what
is missing rather than pretending.
"""
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.api.models import (DeepDivePlanRequest, DeepDiveRunRequest,  # noqa: E402
                             ParseRequest, ScreenRunRequest)
from packages.llm import LLMError, resolve_provider  # noqa: E402
from packages.reporting import render_markdown, render_screen_markdown  # noqa: E402
from packages.research import deep_plan, deep_run  # noqa: E402
from packages.research import store as deep_store  # noqa: E402
from packages.screening import compiler, nl, runs_index  # noqa: E402
from packages.screening import rows as row_source  # noqa: E402
from packages.screening import spec as spec_module  # noqa: E402
from packages.screening import store as screen_store  # noqa: E402
from packages.screening.fields import Registry  # noqa: E402

app = FastAPI(title='Outlier Expectation Gap — Research Platform',
              version='0.1.0',
              description='US/KR screening, harness results and evidence-linked deep-dive research.')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get(
        'WEB_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',') if o.strip()],
    allow_methods=['GET', 'POST'],
    allow_headers=['*'])

PHASE_NOTE = ('This stage is not implemented yet. See docs/WEB_PLATFORM_ARCHITECTURE.md '
              'for the phase that introduces it.')


def _fx(rates, as_of_date):
    return {code.upper(): {'per_usd': float(value), 'source': 'client-supplied', 'as_of_date': as_of_date}
            for code, value in (rates or {}).items()}


def _rows(as_of_date=None, fx_rates=None):
    """Harness runs merged with the screening warehouse, when it has been built."""
    return row_source.load_rows(as_of_date, fx_rates=fx_rates)


@app.get('/api/health')
def health():
    from packages.screening.fields import Registry
    return {'status': 'ok', 'backends': sorted(Registry().active_backends()),
            'runs': len(runs_index.run_ids()),
            'llm_provider_default': os.environ.get('HARNESS_LLM_PROVIDER', 'fixture')}


@app.get('/api/universe')
def universe():
    rows = runs_index.load_rows()
    return {**runs_index.universe_summary(rows),
            'companies': sorted({(row['ticker'], row.get('company_name'), row['jurisdiction'])
                                 for row in rows})}


@app.get('/api/universe/securities')
def universe_securities(market: str | None = None, investable_only: bool = True,
                        limit: int = Query(200, ge=1, le=5000)):
    """The listed US/KR universe built by `harness.py universe sync`.

    This is the regulator-derived universe, not the completed-run corpus that
    `/api/universe` summarises. Rows excluded as ETFs, warrants, SPAC shells or
    off-market listings stay in the file with the reason, so the answer to
    "why is this missing" does not require a re-sync.
    """
    try:
        from data_adapters import universe as universe_store
    except Exception as error:
        raise HTTPException(501, f'data adapters are not installed: {error}') from error
    payload = universe_store.load()
    if payload is None:
        raise HTTPException(404, 'no universe file yet; run '
                                 '`python harness.py universe sync --markets US,KR`')
    rows = universe_store.investable(payload) if investable_only else payload['securities']
    if market:
        currency = 'KRW' if market.upper() == 'KR' else 'USD'
        rows = [row for row in rows if row.get('currency') == currency]
    return {'synced_at_utc': payload['synced_at_utc'], 'as_of_date': payload.get('as_of_date'),
            'summary': payload['summary'], 'markets': payload.get('markets', {}),
            'count': len(rows), 'securities': rows[:limit]}


@app.get('/api/warehouse')
def warehouse_summary(as_of_date: str | None = None):
    """The deterministic metric warehouse: what it covers and what it could not compute."""
    from packages.screening import warehouse as warehouse_store
    payload = warehouse_store.load(as_of_date)
    if payload is None:
        raise HTTPException(404, 'the screening warehouse has not been built; run '
                                 '`python harness.py screen build --as-of <DATE> --from-runs`')
    return {k: v for k, v in payload.items() if k != 'rows'}


@app.get('/api/warehouse/{ticker}')
def warehouse_company(ticker: str, as_of_date: str | None = None):
    """One company's metrics with the provenance behind every number."""
    from packages.screening import warehouse as warehouse_store
    payload = warehouse_store.load(as_of_date)
    if payload is None:
        raise HTTPException(404, 'the screening warehouse has not been built')
    row = next((r for r in payload['rows'] if r['ticker'].upper() == ticker.upper()), None)
    if row is None:
        raise HTTPException(404, f'{ticker}: not in the warehouse at {payload["as_of_date"]}')
    return row


@app.get('/api/screen/fields')
def screen_fields(available_only: bool = False):
    rows = Registry().describe()
    return [row for row in rows if row['available']] if available_only else rows


@app.get('/api/runs')
def list_runs():
    return [{k: row[k] for k in ('run_id', 'ticker', 'company_name', 'jurisdiction', 'exchange',
                                 'currency', 'as_of_date', 'market_cap_usd', 'core_score',
                                 'ex_valuation_score', 'classification', 'archetype',
                                 'hard_veto_status', 'ic_state', 'position_range',
                                 'price_to_base_value', 'early_exit', 'full_harness_complete')}
            for row in sorted(_rows(), key=lambda r: -(r.get('core_score') or 0))]


@app.get('/api/runs/{run_id}')
def get_run(run_id: str):
    row = runs_index.load_row(run_id)
    if row is None:
        raise HTTPException(404, f'{run_id}: no readable harness run')
    return row


@app.get('/api/companies/{ticker}')
def get_company(ticker: str):
    rows = [row for row in _rows() if row['ticker'].upper() == ticker.upper()]
    if not rows:
        raise HTTPException(404, f'{ticker}: no harness run')
    rows.sort(key=lambda r: r['as_of_date'] or '', reverse=True)
    deep_dives = [row for row in deep_store.list_reports() if row['ticker'].upper() == ticker.upper()]
    return {'ticker': rows[0]['ticker'], 'company_name': rows[0].get('company_name'),
            'jurisdiction': rows[0]['jurisdiction'], 'currency': rows[0].get('currency'),
            'latest': rows[0], 'harness_history': rows, 'deep_dives': deep_dives}


@app.post('/api/screen/parse')
def screen_parse(request: ParseRequest):
    provider = (resolve_provider(request.provider, request.model)
                if request.provider != 'lexicon' else None)
    try:
        return nl.parse(request.text, request.as_of_date, provider=provider,
                        fx_rates=_fx(request.fx_rates, request.as_of_date))
    except (LLMError, spec_module.SpecError) as error:
        raise HTTPException(422, str(error)) from error


@app.post('/api/screen/run')
def screen_run(request: ScreenRunRequest):
    try:
        if request.spec is not None:
            spec = spec_module.normalise(request.spec)
        elif request.text:
            if not request.as_of_date:
                raise HTTPException(422, 'as_of_date is required when screening from text')
            provider = (resolve_provider(request.provider, request.model)
                        if request.provider != 'lexicon' else None)
            spec = nl.parse(request.text, request.as_of_date, provider=provider,
                            fx_rates=_fx(request.fx_rates, request.as_of_date))
        else:
            raise HTTPException(422, 'either spec or text is required')
    except (LLMError, spec_module.SpecError) as error:
        raise HTTPException(422, str(error)) from error

    rows = _rows(spec.get('as_of_date'), spec.get('fx_rates'))
    result = compiler.run(spec, rows)
    record = screen_store.build_record(spec, result, rows_sha256=screen_store.content_hash(
        [{k: v for k, v in row.items() if k != 'match_explain'} for row in rows]))
    record['backends'] = row_source.backend_summary(rows)
    if request.persist:
        screen_store.save(record)
    return record


@app.get('/api/screen/runs')
def screen_runs():
    return screen_store.list_runs()


@app.get('/api/screen/runs/{screen_run_id}')
def screen_run_detail(screen_run_id: str):
    record = screen_store.load(screen_run_id)
    if record is None:
        raise HTTPException(404, f'{screen_run_id}: no such screen run')
    return record


@app.get('/api/screen/runs/{screen_run_id}/markdown', response_class=PlainTextResponse)
def screen_run_markdown(screen_run_id: str):
    record = screen_store.load(screen_run_id)
    if record is None:
        raise HTTPException(404, f'{screen_run_id}: no such screen run')
    return render_screen_markdown(record)


@app.post('/api/harness/triage')
def harness_triage():
    raise HTTPException(501, f'Batch harness triage orchestration arrives in Phase 7. {PHASE_NOTE}')


@app.post('/api/harness/full')
def harness_full():
    raise HTTPException(501, f'Full harness orchestration arrives in Phase 8. {PHASE_NOTE}')


@app.get('/api/harness/runs/{run_id}')
def harness_run(run_id: str):
    return get_run(run_id)


@app.post('/api/deep-dive/plan')
def deep_dive_plan(request: DeepDivePlanRequest):
    try:
        return deep_plan.build(request.run_id, user_requested=request.user_requested)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error


@app.post('/api/deep-dive/run')
def deep_dive_run(request: DeepDiveRunRequest):
    fixtures = ROOT / 'packages' / 'research' / 'fixtures' / request.run_id
    provider_kwargs = {'root': fixtures} if request.provider == 'fixture' else {}
    try:
        provider = resolve_provider(request.provider, request.model, **provider_kwargs)
        report, plan, _path = deep_run.run(request.run_id, provider,
                                           user_requested=request.user_requested)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error
    except LLMError as error:
        raise HTTPException(422, str(error)) from error
    return {'deep_dive_id': report['metadata']['deep_dive_id'], 'plan': plan, 'report': report}


@app.get('/api/deep-dive')
def deep_dive_list():
    return deep_store.list_reports()


@app.get('/api/deep-dive/{deep_dive_id}')
def deep_dive_detail(deep_dive_id: str):
    report = deep_store.load(deep_dive_id)
    if report is None:
        raise HTTPException(404, f'{deep_dive_id}: no such deep dive')
    return {'report': report, 'plan': deep_store.load_plan(deep_dive_id)}


@app.get('/api/reports/{deep_dive_id}')
def report_detail(deep_dive_id: str, fmt: str = Query('json', pattern='^(json|markdown)$')):
    report = deep_store.load(deep_dive_id)
    if report is None:
        raise HTTPException(404, f'{deep_dive_id}: no such report')
    if fmt == 'markdown':
        return PlainTextResponse(render_markdown(report))
    return report
