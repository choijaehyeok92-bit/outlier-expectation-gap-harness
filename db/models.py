"""Schema for the research platform.

Three properties shape it.

**The artifacts stay authoritative.** `harness_run` carries the aggregate's
SHA-256 and the path to it. The table exists so a screener can rank two hundred
runs without opening two hundred files, not so anyone can stop reading the
files. The same holds for `screen_run` and `deep_dive`.

**History is appended, never overwritten.** Re-aggregating a run produces a new
`harness_run` row keyed by a different `aggregate_sha256`, and the previous row
stays. Only `is_current` moves. A table that updated in place would quietly
erase the fact that a number changed, which is exactly the thing a reviewer
needs to see.

**NULL means unknown.** `screening_metric` holds a row for every metric that
was attempted, including the ones that could not be computed, with the reason
attached. A metric missing from the table was never attempted; a metric present
with a NULL value was attempted and refused. Those are different facts and the
schema keeps them different.
"""
from datetime import datetime, timezone

from sqlalchemy import (Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index,
                        Integer, String, Text, UniqueConstraint, func)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .types import (Identifier, JSONColumn, MetricValue, Money, Ratio, Score, Sha256,
                    Shares, ShortText)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())


# --------------------------------------------------------------------- entities
class Issuer(TimestampMixin, Base):
    """A filing entity. One row per regulator identity, not per listing."""
    __tablename__ = 'issuer'
    __table_args__ = (
        UniqueConstraint('regulator', 'regulator_issuer_id', name='uq_issuer_regulator_id'),
        CheckConstraint("jurisdiction IN ('US','KR')", name='ck_issuer_jurisdiction'),
        CheckConstraint("regulator IN ('SEC','DART')", name='ck_issuer_regulator'),
    )

    issuer_id: Mapped[int] = mapped_column(primary_key=True)
    jurisdiction: Mapped[str] = mapped_column(String(2), nullable=False)
    regulator: Mapped[str] = mapped_column(String(8), nullable=False)
    regulator_issuer_id: Mapped[str] = mapped_column(Identifier, nullable=False)
    legal_name: Mapped[str] = mapped_column(ShortText, nullable=False)
    industry: Mapped[str | None] = mapped_column(ShortText)
    sector: Mapped[str | None] = mapped_column(ShortText)
    fiscal_year_end_month: Mapped[int | None] = mapped_column(Integer)
    extra: Mapped[dict | None] = mapped_column(JSONColumn)

    securities: Mapped[list['Security']] = relationship(back_populates='issuer')

    @property
    def issuer_key(self) -> str:
        return f'{self.regulator}:{self.regulator_issuer_id}'


class Security(TimestampMixin, Base):
    """A listing. Exclusions are recorded here with their reason, not deleted."""
    __tablename__ = 'security'
    __table_args__ = (
        UniqueConstraint('exchange', 'ticker', name='uq_security_exchange_ticker'),
        Index('ix_security_ticker', 'ticker'),
    )

    security_id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int | None] = mapped_column(ForeignKey('issuer.issuer_id'))
    ticker: Mapped[str] = mapped_column(Identifier, nullable=False)
    exchange: Mapped[str] = mapped_column(Identifier, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    security_type: Mapped[str] = mapped_column(Identifier, nullable=False, default='common')
    name: Mapped[str | None] = mapped_column(ShortText)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # An ETF, a warrant or a KONEX listing stays in the table with the reason it
    # is out of scope, so "why is this not in my screen" needs no re-sync.
    excluded_reason: Mapped[str | None] = mapped_column(ShortText)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    issuer: Mapped[Issuer | None] = relationship(back_populates='securities')


class Filing(TimestampMixin, Base):
    """One regulatory submission. Amendments are rows of their own."""
    __tablename__ = 'filing'
    __table_args__ = (
        UniqueConstraint('regulator', 'accession', name='uq_filing_accession'),
        Index('ix_filing_issuer_date', 'issuer_id', 'filing_date'),
    )

    filing_id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int | None] = mapped_column(ForeignKey('issuer.issuer_id'))
    regulator: Mapped[str] = mapped_column(String(8), nullable=False)
    form_type: Mapped[str] = mapped_column(ShortText, nullable=False)
    reprt_code: Mapped[str | None] = mapped_column(String(8))
    accession: Mapped[str] = mapped_column(Identifier, nullable=False)
    filing_date: Mapped[str | None] = mapped_column(Date)
    period_end: Mapped[str | None] = mapped_column(Date)
    is_amendment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    title: Mapped[str | None] = mapped_column(Text)
    source_document: Mapped[str | None] = mapped_column(ShortText)
    raw_uri: Mapped[str | None] = mapped_column(Text)
    raw_sha256: Mapped[str | None] = mapped_column(Sha256)


class FinancialFact(TimestampMixin, Base):
    """One disclosed number, exactly as Stage 0 recorded it.

    `consolidation_basis` is on the row because a series that silently mixes
    연결 and 별도 reports a growth rate that did not happen, and no later stage
    can detect it. `fact_key` is a content hash, which is what makes a re-sync
    idempotent rather than duplicating the corpus.
    """
    __tablename__ = 'financial_fact'
    __table_args__ = (
        UniqueConstraint('fact_key', name='uq_fact_key'),
        CheckConstraint("period_kind IN ('instant','quarter','ytd','fy')",
                        name='ck_fact_period_kind'),
        CheckConstraint("period_kind <> 'fy' OR fiscal_quarter IS NULL",
                        name='ck_fact_fy_has_no_quarter'),
        CheckConstraint("period_kind <> 'quarter' OR fiscal_quarter IS NOT NULL",
                        name='ck_fact_quarter_has_quarter'),
        CheckConstraint("consolidation_basis IS NULL OR consolidation_basis IN ('CFS','OFS')",
                        name='ck_fact_consolidation'),
        Index('ix_fact_lookup', 'issuer_id', 'metric', 'period_kind', 'period_end',
              'consolidation_basis'),
    )

    fact_id: Mapped[int] = mapped_column(primary_key=True)
    fact_key: Mapped[str] = mapped_column(Sha256, nullable=False)
    issuer_id: Mapped[int | None] = mapped_column(ForeignKey('issuer.issuer_id'))
    filing_id: Mapped[int | None] = mapped_column(ForeignKey('filing.filing_id'))
    ticker: Mapped[str | None] = mapped_column(Identifier)
    metric: Mapped[str] = mapped_column(Identifier, nullable=False)
    metric_detail: Mapped[str | None] = mapped_column(ShortText)
    reported_label: Mapped[str | None] = mapped_column(ShortText)
    statement: Mapped[str] = mapped_column(Identifier, nullable=False)
    value: Mapped[float | None] = mapped_column(Money)
    unit_kind: Mapped[str] = mapped_column(Identifier, nullable=False, default='currency')
    currency: Mapped[str | None] = mapped_column(String(8))
    scale_multiplier: Mapped[float] = mapped_column(Money, nullable=False, default=1.0)
    period_start: Mapped[str | None] = mapped_column(Date)
    period_end: Mapped[str | None] = mapped_column(Date)
    period_kind: Mapped[str] = mapped_column(String(8), nullable=False)
    fiscal_year: Mapped[int | None] = mapped_column(Integer)
    fiscal_quarter: Mapped[int | None] = mapped_column(Integer)
    segment: Mapped[str | None] = mapped_column(ShortText)
    filing_date: Mapped[str | None] = mapped_column(Date)
    source_document: Mapped[str | None] = mapped_column(ShortText)
    source_locator: Mapped[str | None] = mapped_column(Text)
    consolidation_basis: Mapped[str | None] = mapped_column(String(3))
    gaap_status: Mapped[str | None] = mapped_column(Identifier)
    confidence: Mapped[float | None] = mapped_column(Ratio)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_reason: Mapped[str | None] = mapped_column(Text)
    is_amended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_restated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # A correction never overwrites what it corrected; it points at it.
    supersedes_fact_id: Mapped[int | None] = mapped_column(
        ForeignKey('financial_fact.fact_id'))
    pack_sha256: Mapped[str | None] = mapped_column(Sha256)


class MarketSnapshot(TimestampMixin, Base):
    """A price observation. Never sourced from a regulator."""
    __tablename__ = 'market_snapshot'
    __table_args__ = (
        UniqueConstraint('security_id', 'as_of_date', 'source', name='uq_snapshot_point'),
        Index('ix_snapshot_ticker_date', 'ticker', 'as_of_date'),
    )

    snapshot_id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int | None] = mapped_column(ForeignKey('security.security_id'))
    ticker: Mapped[str] = mapped_column(Identifier, nullable=False)
    as_of_date: Mapped[str] = mapped_column(Date, nullable=False)
    close: Mapped[float | None] = mapped_column(Money)
    market_cap: Mapped[float | None] = mapped_column(Money)
    shares_outstanding: Mapped[float | None] = mapped_column(Shares)
    currency: Mapped[str | None] = mapped_column(String(3))
    source: Mapped[str] = mapped_column(ShortText, nullable=False)


class ScreeningMetric(TimestampMixin, Base):
    """One computed metric, or one recorded refusal to compute it.

    A row with `value IS NULL` and an `unavailable_reason` is the record that
    the metric was attempted and could not be produced. That is a different
    fact from the metric being absent, and a screen reads them differently.
    """
    __tablename__ = 'screening_metric'
    __table_args__ = (
        UniqueConstraint('ticker', 'as_of_date', 'metric', name='uq_metric_point'),
        Index('ix_metric_lookup', 'metric', 'as_of_date', 'value'),
    )

    metric_row_id: Mapped[int] = mapped_column(primary_key=True)
    security_id: Mapped[int | None] = mapped_column(ForeignKey('security.security_id'))
    ticker: Mapped[str] = mapped_column(Identifier, nullable=False)
    as_of_date: Mapped[str] = mapped_column(Date, nullable=False)
    metric: Mapped[str] = mapped_column(Identifier, nullable=False)
    value: Mapped[float | None] = mapped_column(MetricValue)
    currency: Mapped[str | None] = mapped_column(String(3))
    method: Mapped[str | None] = mapped_column(ShortText)
    unavailable_reason: Mapped[str | None] = mapped_column(Text)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provenance: Mapped[dict | None] = mapped_column(JSONColumn)
    inputs_sha256: Mapped[str | None] = mapped_column(Sha256)


# ------------------------------------------------------------------- run index
class HarnessRun(TimestampMixin, Base):
    """An index over `runs/<RUN_ID>/`. The artifact remains authoritative.

    Append-only: a re-aggregated run is a new row with a different
    `aggregate_sha256`, and `is_current` moves rather than the old row changing.
    """
    __tablename__ = 'harness_run'
    __table_args__ = (
        UniqueConstraint('run_id', 'aggregate_sha256', name='uq_harness_run_version'),
        Index('ix_harness_run_current', 'ticker', 'is_current'),
        Index('ix_harness_run_asof', 'as_of_date'),
    )

    harness_run_id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(Identifier, nullable=False)
    security_id: Mapped[int | None] = mapped_column(ForeignKey('security.security_id'))
    ticker: Mapped[str] = mapped_column(Identifier, nullable=False)
    company_name: Mapped[str | None] = mapped_column(ShortText)
    jurisdiction: Mapped[str | None] = mapped_column(String(8))
    exchange: Mapped[str | None] = mapped_column(Identifier)
    currency: Mapped[str | None] = mapped_column(String(3))
    as_of_date: Mapped[str | None] = mapped_column(Date)
    stage: Mapped[str | None] = mapped_column(Identifier)
    core_score: Mapped[float | None] = mapped_column(Score)
    ex_valuation_score: Mapped[float | None] = mapped_column(Score)
    coverage_weight: Mapped[float | None] = mapped_column(Score)
    classification: Mapped[str | None] = mapped_column(ShortText)
    archetype: Mapped[str | None] = mapped_column(Identifier)
    hard_veto_status: Mapped[str | None] = mapped_column(Identifier)
    ic_state: Mapped[str | None] = mapped_column(Identifier)
    position_range: Mapped[str | None] = mapped_column(ShortText)
    price_to_base_value: Mapped[float | None] = mapped_column(Ratio)
    market_cap_usd: Mapped[float | None] = mapped_column(Money)
    current_price: Mapped[float | None] = mapped_column(Money)
    net_cash_per_share: Mapped[float | None] = mapped_column(Money)
    dilution_watch_status: Mapped[str | None] = mapped_column(Identifier)
    early_exit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    full_harness_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    triage_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    domain_scores: Mapped[dict | None] = mapped_column(JSONColumn)
    axis_scores: Mapped[dict | None] = mapped_column(JSONColumn)
    strategy_version: Mapped[str | None] = mapped_column(Identifier)
    decision_policy_version: Mapped[str | None] = mapped_column(Identifier)
    code_commit_sha: Mapped[str | None] = mapped_column(Sha256)
    input_snapshot_sha256: Mapped[str | None] = mapped_column(Sha256)
    aggregate_sha256: Mapped[str] = mapped_column(Sha256, nullable=False)
    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    frozen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow)


class ScreenRun(TimestampMixin, Base):
    """An executed screen, written once and never rewritten."""
    __tablename__ = 'screen_run'

    screen_run_id: Mapped[str] = mapped_column(Identifier, primary_key=True)
    as_of_date: Mapped[str | None] = mapped_column(Date)
    spec_id: Mapped[str | None] = mapped_column(Identifier)
    backend: Mapped[str | None] = mapped_column(Identifier)
    query_text: Mapped[str | None] = mapped_column(Text)
    matched_count: Mapped[int | None] = mapped_column(Integer)
    considered: Mapped[int | None] = mapped_column(Integer)
    spec: Mapped[dict | None] = mapped_column(JSONColumn)
    summary: Mapped[dict | None] = mapped_column(JSONColumn)
    results: Mapped[list | None] = mapped_column(JSONColumn)
    content_sha256: Mapped[str | None] = mapped_column(Sha256)
    code_commit_sha: Mapped[str | None] = mapped_column(Sha256)


class DeepDive(TimestampMixin, Base):
    """A deep-dive report, written once and never rewritten."""
    __tablename__ = 'deep_dive'
    __table_args__ = (Index('ix_deep_dive_ticker', 'ticker', 'as_of_date'),)

    deep_dive_id: Mapped[str] = mapped_column(Identifier, primary_key=True)
    run_id: Mapped[str | None] = mapped_column(Identifier)
    ticker: Mapped[str] = mapped_column(Identifier, nullable=False)
    company_name: Mapped[str | None] = mapped_column(ShortText)
    jurisdiction: Mapped[str | None] = mapped_column(String(8))
    as_of_date: Mapped[str | None] = mapped_column(Date)
    route: Mapped[str | None] = mapped_column(Identifier)
    red_team_overall: Mapped[str | None] = mapped_column(Identifier)
    agreement_with_harness: Mapped[str | None] = mapped_column(Identifier)
    report: Mapped[dict | None] = mapped_column(JSONColumn)
    provider_metadata: Mapped[list | None] = mapped_column(JSONColumn)
    content_sha256: Mapped[str | None] = mapped_column(Sha256)


# ----------------------------------------------------------------- monitoring
class MonitoringWatchItem(TimestampMixin, Base):
    """What a company has declared it is watching. Derived, so upserted.

    Every row is read back from an agent report or a deep dive; nothing here
    is authored by the monitoring layer. `watch_id` is stable across a rebuild
    on purpose — observations point at it, and an id that moved when a deep
    dive was re-run would orphan a company's whole history.
    """
    __tablename__ = 'monitoring_watch_item'
    __table_args__ = (
        CheckConstraint("kind IN ('kpi','falsifier')", name='ck_watch_item_kind'),
        Index('ix_watch_item_ticker', 'ticker', 'kind'),
    )

    watch_id: Mapped[str] = mapped_column(Identifier, primary_key=True)
    ticker: Mapped[str] = mapped_column(Identifier, nullable=False)
    run_id: Mapped[str | None] = mapped_column(Identifier)
    kind: Mapped[str] = mapped_column(Identifier, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source_kind: Mapped[str] = mapped_column(Identifier, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(Identifier)
    as_of_date: Mapped[str | None] = mapped_column(Date)
    cadence: Mapped[str | None] = mapped_column(Identifier)
    direction_required: Mapped[str | None] = mapped_column(Identifier)
    warning_threshold: Mapped[str | None] = mapped_column(Text)
    thesis_break_threshold: Mapped[str | None] = mapped_column(Text)
    comparison: Mapped[dict | None] = mapped_column(JSONColumn)
    machine_checkable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    not_machine_checkable_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class MonitoringObservation(TimestampMixin, Base):
    """One observed fact. Append-only, like every other record of what was seen.

    A correction is a new row whose `supersedes` names the old one; the old row
    stays. `source` is NOT NULL because a number nobody can trace is not
    evidence, and a status computed from one would be worse than no status.
    """
    __tablename__ = 'monitoring_observation'
    __table_args__ = (
        CheckConstraint("source_type IN ('filing','ir','industry','secondary','market','other')",
                        name='ck_observation_source_type'),
        CheckConstraint("fact_or_estimate IN ('fact','estimate','interpretation')",
                        name='ck_observation_fact_or_estimate'),
        Index('ix_observation_watch', 'watch_id', 'as_of_date'),
        Index('ix_observation_ticker', 'ticker', 'as_of_date'),
    )

    observation_id: Mapped[str] = mapped_column(Identifier, primary_key=True)
    ticker: Mapped[str] = mapped_column(Identifier, nullable=False)
    watch_id: Mapped[str] = mapped_column(Identifier, nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[float | None] = mapped_column(MetricValue)
    unit: Mapped[str | None] = mapped_column(Identifier)
    triggered: Mapped[bool | None] = mapped_column(Boolean)
    period: Mapped[str | None] = mapped_column(ShortText)
    as_of_date: Mapped[str] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Identifier, nullable=False)
    fact_or_estimate: Mapped[str] = mapped_column(Identifier, nullable=False, default='fact')
    note: Mapped[str | None] = mapped_column(Text)
    supersedes: Mapped[str | None] = mapped_column(Identifier)
    pre_analysis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recorded_at_utc: Mapped[str | None] = mapped_column(ShortText)


# ----------------------------------------------------------------- operations
class Job(TimestampMixin, Base):
    """Queued work, claimed out of this table rather than out of a broker.

    `idempotency_key` is what makes enqueueing safe; `available_at` and
    `lease_expires_at` are what make *claiming* safe. A worker that dies mid
    job leaves the row `running` forever unless the lease can expire, and a
    failed job that returns to `queued` immediately will hammer whatever broke
    it — so a retry moves `available_at` forward instead.

    Reclaiming an expired lease can run a handler twice. Every registered
    handler is required to be idempotent for exactly that reason; the contract
    is written down in `config/workers.json`.
    """
    __tablename__ = 'job'
    __table_args__ = (
        UniqueConstraint('idempotency_key', name='uq_job_idempotency'),
        CheckConstraint("status IN ('queued','running','completed','failed','cancelled')",
                        name='ck_job_status'),
        Index('ix_job_status_kind', 'status', 'kind'),
        Index('ix_job_claimable', 'status', 'available_at'),
    )

    job_id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(Identifier, nullable=False)
    status: Mapped[str] = mapped_column(Identifier, nullable=False, default='queued')
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONColumn)
    result: Mapped[dict | None] = mapped_column(JSONColumn)
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_id: Mapped[str | None] = mapped_column(ShortText)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class JobLock(TimestampMixin, Base):
    """A resource one running job holds, so a second job cannot touch it.

    The queue on its own stops two workers taking the same *row*. It says
    nothing about two different rows writing the same `runs/<ID>/` — and they
    do: a full-harness job rewrites `aggregate.json` while a deep dive reads
    it, and `dump_json` is a plain `write_text`, so the reader can see half a
    file.

    A lock is `(namespace, resource)`, unique, which is the guarantee that
    matters: the database itself refuses the second holder. `resource = '*'`
    means the whole namespace, for a job whose targets are not known until it
    selects them.

    Rows belong to a job and are deleted when it stops — including when its
    lease is reaped, because a dead worker must not hold a resource forever.
    """
    __tablename__ = 'job_lock'
    __table_args__ = (
        UniqueConstraint('namespace', 'resource', name='uq_job_lock_resource'),
        Index('ix_job_lock_job', 'job_id'),
    )

    lock_id: Mapped[int] = mapped_column(primary_key=True)
    namespace: Mapped[str] = mapped_column(Identifier, nullable=False)
    resource: Mapped[str] = mapped_column(ShortText, nullable=False)
    job_id: Mapped[int] = mapped_column(
        ForeignKey('job.job_id', ondelete='CASCADE'), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow)


class SyncLog(Base):
    """What a sync did, so a surprising table has an explanation."""
    __tablename__ = 'sync_log'

    sync_id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(Identifier, nullable=False)
    source: Mapped[str | None] = mapped_column(Text)
    inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detail: Mapped[dict | None] = mapped_column(JSONColumn)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


ALL_TABLES = (Issuer, Security, Filing, FinancialFact, MarketSnapshot, ScreeningMetric,
              HarnessRun, ScreenRun, DeepDive, MonitoringWatchItem, MonitoringObservation,
              Job, JobLock, SyncLog)
