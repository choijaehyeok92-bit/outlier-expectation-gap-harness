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


class DeepDivePlanRequest(BaseModel):
    run_id: str
    user_requested: bool = False


class DeepDiveRunRequest(BaseModel):
    run_id: str
    provider: Literal['fixture', 'anthropic', 'openai'] = 'fixture'
    model: str | None = None
    user_requested: bool = False
