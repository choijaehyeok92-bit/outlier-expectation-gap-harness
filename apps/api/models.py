"""Request and response models.

Pydantic lives at the edge only. Inside, the screening and research packages
use plain dictionaries validated against the same JSON Schemas the CLI uses, so
there is exactly one definition of a ScreeningSpec and one of a DeepDiveReport
and the API cannot drift away from them.

Secrets never appear here. Provider keys are read from the environment inside
the provider classes and no route echoes them back.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    text: str = Field(min_length=1, description='자연어 스크리닝 요청')
    as_of_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    provider: Literal['lexicon', 'fixture', 'anthropic', 'openai'] = 'lexicon'
    model: str | None = None
    fx_rates: dict[str, float] | None = Field(
        default=None,
        description='명시적 as-of 환율. USD 1단위당 해당 통화 수량. 서버는 환율을 조회하지 않는다.')


class ScreenRunRequest(BaseModel):
    spec: dict[str, Any] | None = None
    text: str | None = None
    as_of_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    provider: Literal['lexicon', 'fixture', 'anthropic', 'openai'] = 'lexicon'
    model: str | None = None
    fx_rates: dict[str, float] | None = None
    persist: bool = True


class TriageRequest(BaseModel):
    """Stage 3 over the top candidates.

    `provider` defaults to the offline placeholder, which analyses nothing. A
    real model is an explicit choice because it spends money and produces
    reports a person will read as research.
    """
    screen_run_id: str | None = None
    as_of_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    top: int | None = Field(default=None, ge=1, le=200)
    provider: Literal['placeholder', 'anthropic', 'openai'] = 'placeholder'
    model: str | None = None
    dry_run: bool = True
    force: bool = False
    persist: bool = True


class FullHarnessRequest(BaseModel):
    """Stage 4: the whole workflow, over named runs or over a screen's top rows.

    Same defaults as triage and for the same reason: a dry run, and the offline
    placeholder. This stage spends more than triage does — every agent in the
    manifest, per company — so starting it is an explicit act.
    """
    run_ids: list[str] | None = Field(default=None, max_length=25)
    screen_run_id: str | None = None
    as_of_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    top: int | None = Field(default=None, ge=1, le=50)
    max_rounds: int | None = Field(default=None, ge=1, le=40)
    provider: Literal['placeholder', 'anthropic', 'openai'] = 'placeholder'
    model: str | None = None
    dry_run: bool = True
    force: bool = False
    persist: bool = True


class ObservationRequest(BaseModel):
    """One observation, recorded against a declared watch item.

    `source` and `as_of_date` are required for the same reason every fact in
    this system carries them: a number nobody can trace is not evidence. The
    server refuses a date in the future rather than filtering it later.
    """
    ticker: str
    watch_id: str
    as_of_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    source: str = Field(min_length=1)
    source_type: Literal['filing', 'ir', 'industry', 'secondary', 'market', 'other']
    value: str | float | None = None
    unit: Literal['ratio', 'percent', 'percent_point', 'number'] | None = None
    triggered: bool | None = None
    period: str | None = None
    fact_or_estimate: Literal['fact', 'estimate', 'interpretation'] = 'fact'
    note: str | None = None
    supersedes: str | None = None


class LinkRequest(BaseModel):
    """Say that a watch item is measured by a warehouse metric.

    This is a person's judgement, not a lookup: linking "Microsoft Cloud gross
    margin" to the company-wide `gross_margin` would report a number that was
    never measured as passing a threshold it does not belong to. The server
    records whether the names matched exactly or the operator asserted it, and
    that travels into every observation made through the link.
    """
    ticker: str
    watch_id: str
    metric_id: str = Field(min_length=1, max_length=64)
    note: str | None = None
    linked_by: str = Field(default='operator', max_length=64)


class IngestRequest(BaseModel):
    ticker: str
    as_of_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')


class SymbolResolveRequest(BaseModel):
    """Reconcile pasted symbols against the regulator's own universe.

    Read-only. Symbols arriving from a spreadsheet, a screenshot or somebody's
    memory are unverified input, and the answer this returns is what makes them
    safe to act on: the company name beside each one. A mis-read character
    produces a real other company, and nothing downstream would look wrong.
    """
    symbols: list[str] = Field(min_length=1, max_length=2000)


class WarehouseBuildRequest(BaseModel):
    """Recompute the deterministic metric warehouse.

    No directory fields. The sources are the two places the rest of the
    pipeline already writes — `data/packs` and the completed runs, with closes
    from `data/market` — and a route that accepted a path would be a route that
    reads whatever path it is given.
    """
    as_of_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    include_packs: bool = True
    include_runs: bool = True


class CredentialRequest(BaseModel):
    """Set one credential from the settings page.

    This is the single route in the service that accepts a secret, and it is
    write-only: the value goes into .env and into this process's environment,
    and no route ever returns it. `name` is checked against the catalogue of
    variables the app actually reads, so a typo is a refusal rather than a line
    nothing will look at.

    An empty `value` clears the variable — the way to remove a key without
    editing a file by hand.
    """
    name: str = Field(min_length=1, max_length=64)
    value: str = Field(default='', max_length=4096)


class UniverseSyncRequest(BaseModel):
    """Rebuild the investable universe from SEC and DART.

    Credentials are read from the API process's environment, never from here:
    SEC wants a contact in its User-Agent and DART wants a key, and a route
    that accepted either would put it in a request body and an error message.

    `enrich_limit` is bounded because each enriched Korean issuer is one more
    metered DART request, and an unbounded number inside a request handler is
    a timeout with a half-written universe behind it.
    """
    markets: list[Literal['US', 'KR']] = Field(default_factory=lambda: ['US', 'KR'],
                                               min_length=1, max_length=2)
    as_of_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    enrich_limit: int = Field(default=0, ge=0, le=500)
    refresh_corp_codes: bool = False


class PackIngestRequest(BaseModel):
    """Build Stage 0 packs for a few named companies, synchronously.

    Capped at ten. Each company is several requests to a regulator that meters
    access; a handler walking five thousand listings would time out and leave a
    half-finished directory. Larger batches go to the `ingest_pack` job kind,
    which has a lease and a retry policy.
    """
    tickers: list[str] = Field(min_length=1, max_length=10)
    market: Literal['US', 'KR'] = 'US'
    as_of_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    force: bool = False


class MarketFetchRequest(BaseModel):
    """Fetch one US trading session's closes into `data/market/US/`.

    No credential field, by design. The vendor key is read from the API
    process's environment inside the provider; a route that accepted one would
    put it in a request body, a proxy log and this service's own error text.

    `scope` decides which listings get written. The default writes only the
    ones a Stage 0 pack exists for, because a price with no financials beside
    it cannot become a screenable row.
    """
    as_of_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    provider: str | None = Field(default=None, max_length=64)
    scope: Literal['packs', 'universe', 'all'] = 'packs'
    tickers: list[str] | None = Field(default=None, max_length=500)
    dry_run: bool = False


class JobRequest(BaseModel):
    """Queue one background job.

    `kind` is checked against `config/workers.json` rather than accepted as
    written, and the provider a job may use is the worker's decision, not this
    request's — a payload naming a paid model is refused when the worker runs
    it. Credentials never belong here: job payloads are stored and served back
    by this same API.
    """
    kind: str = Field(min_length=1, max_length=64)
    payload: dict = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=128)
    priority: int = Field(default=100, ge=0, le=1000)
    max_attempts: int | None = Field(default=None, ge=1, le=10)


class DeepDivePlanRequest(BaseModel):
    run_id: str
    user_requested: bool = False


class DeepDiveRunRequest(BaseModel):
    run_id: str
    provider: Literal['fixture', 'anthropic', 'openai'] = 'fixture'
    model: str | None = None
    user_requested: bool = False
