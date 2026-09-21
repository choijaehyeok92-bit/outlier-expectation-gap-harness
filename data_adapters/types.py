"""Shared entity model. One shape for both markets.

These mirror the DB schema in docs/WEB_PLATFORM_ARCHITECTURE.md §5 so an
adapter's output can be written to Postgres later without a translation step.

Two fields carry most of the weight. `consolidation_basis` is on every fact
because a series that silently mixes 연결 and 별도 is wrong in a way no later
stage can detect. `period_kind` is on every fact because a Korean 3분기보고서
reports a nine-month cumulative figure next to a three-month one, and reading
one as the other destroys every growth rate downstream.
"""
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

Jurisdiction = Literal['US', 'KR']
Regulator = Literal['SEC', 'DART']
PeriodKind = Literal['instant', 'quarter', 'ytd', 'fy']
Consolidation = Literal['CFS', 'OFS']


def _clean(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if v is not None}


@dataclass(frozen=True)
class Issuer:
    jurisdiction: Jurisdiction
    regulator: Regulator
    regulator_issuer_id: str            # CIK (zero-padded) / DART corp_code
    legal_name: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    fiscal_year_end: Optional[str] = None   # MM-DD
    extra: dict = field(default_factory=dict)

    @property
    def issuer_key(self) -> str:
        return f'{self.regulator}:{self.regulator_issuer_id}'

    def to_dict(self) -> dict:
        return _clean(asdict(self)) | {'issuer_key': self.issuer_key}


@dataclass(frozen=True)
class Security:
    issuer_key: str
    ticker: str
    exchange: str
    currency: str
    security_type: str                  # common / etf / cef / preferred / warrant / unit / spac / unknown
    active: bool = True
    name: Optional[str] = None
    excluded_reason: Optional[str] = None
    requires_review: bool = False

    @property
    def security_key(self) -> str:
        return f'{self.exchange}:{self.ticker}'

    def to_dict(self) -> dict:
        return _clean(asdict(self)) | {'security_key': self.security_key}


@dataclass(frozen=True)
class MarketSnapshot:
    security_key: str
    as_of_date: str
    close: Optional[float]
    market_cap: Optional[float]
    shares_outstanding: Optional[float]
    currency: str
    source: str

    def to_dict(self) -> dict:
        return _clean(asdict(self))


@dataclass(frozen=True)
class Filing:
    issuer_key: str
    regulator: Regulator
    form_type: str                      # 10-K / 10-Q / 사업보고서 / 분기보고서 …
    filing_date: str
    accession: str                      # accessionNumber / rcept_no
    title: Optional[str] = None
    period_end: Optional[str] = None
    reprt_code: Optional[str] = None    # DART only
    is_amendment: bool = False
    document_url: Optional[str] = None
    requirement: Optional[str] = None   # which intake requirement pulled it
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _clean(asdict(self))


@dataclass(frozen=True)
class FinancialFact:
    """One disclosed number. No calculation, no normalisation, no judgement."""
    issuer_key: str
    metric: str                         # financial_pack.schema.json metric enum
    value: Optional[float]
    period_kind: PeriodKind
    statement: str                      # income / balance_sheet / cash_flow / shares / …
    source_document: str
    consolidation_basis: Optional[Consolidation] = None
    metric_detail: Optional[str] = None
    reported_label: Optional[str] = None
    unit_kind: str = 'currency'
    currency: Optional[str] = None
    scale_multiplier: float = 1.0
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    fiscal_year: Optional[int] = None
    fiscal_quarter: Optional[int] = None
    filing_date: Optional[str] = None
    source_locator: Optional[str] = None
    source_section: Optional[str] = None
    gaap_status: str = 'gaap'
    is_amended: bool = False
    is_restated: bool = False
    confidence: Optional[float] = None
    requires_review: bool = False
    review_reason: Optional[str] = None
    mapping_stage: Optional[str] = None   # which step of the resolution chain matched
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return _clean(asdict(self))


@dataclass
class IngestionResult:
    """What one ingestion produced, including what it refused to do."""
    issuer: Issuer
    filings: list = field(default_factory=list)
    facts: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    excluded_post_cutoff: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def warn(self, severity: str, message: str, **extra: Any) -> None:
        self.warnings.append({'severity': severity, 'message': message, **extra})

    def to_dict(self) -> dict:
        return {'issuer': self.issuer.to_dict(),
                'filings': [f.to_dict() for f in self.filings],
                'facts': [f.to_dict() for f in self.facts],
                'warnings': self.warnings,
                'excluded_post_cutoff': self.excluded_post_cutoff,
                'metadata': self.metadata}
