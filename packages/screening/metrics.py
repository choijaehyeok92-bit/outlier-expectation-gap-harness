"""Compute screening metrics from a Stage 0 pack. Deterministically, in Python.

No language model reaches this file, and none ever should: a screening metric
that is re-derived by a model changes when nobody changed the filing, and every
threshold built on it moves with it.

A metric is an expression tree evaluated in a context — either "trailing twelve
months as at a date" or "this fiscal year". The same tree serves both, which is
what makes a per-share three-year CAGR possible without a second code path: it
is the per-share expression evaluated at two fiscal years.

Four refusals are worth naming, because each one is a number a careless
implementation would happily produce:

* A ratio whose denominator is zero or negative is not computed. Revenue of
  zero does not make a margin of infinity, and a loss-making base does not make
  a growth rate.
* A CAGR from a non-positive starting value is not computed. It is undefined,
  not large.
* A missing component is missing, not zero — unless the config explicitly says
  the component is optional, and then the assumption is recorded on the row.
* A cost or outflow keeps the positive-magnitude convention Stage 0 uses, so
  `capex_to_ocf` is a positive fraction rather than a sign puzzle.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .facts import FactIndex, Window

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'config' / 'screening_metrics.json'
BALANCE_SHEET_METRICS = {
    'cash', 'short_term_investments', 'long_term_investments', 'accounts_receivable',
    'inventory', 'accounts_payable', 'deferred_revenue', 'ppe_net', 'goodwill', 'intangibles',
    'total_assets', 'short_term_debt', 'long_term_debt', 'convertible_debt', 'total_debt',
    'lease_liabilities', 'total_liabilities', 'total_equity', 'period_end_shares',
}


def load_config(path=None) -> dict:
    return json.loads(Path(path or CONFIG_PATH).read_text(encoding='utf-8'))


@dataclass
class MetricValue:
    """A computed metric and the audit trail behind it."""
    metric_id: str
    value: Optional[float]
    method: str
    reason: Optional[str] = None
    inputs: list = field(default_factory=list)
    assumptions: list = field(default_factory=list)
    requires_review: bool = False
    review_reasons: list = field(default_factory=list)
    period_end: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.value is not None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v not in (None, [], False)} | \
               {'metric_id': self.metric_id, 'value': self.value}


def _missing(metric_id: str, method: str, reason: str) -> MetricValue:
    return MetricValue(metric_id, None, method, reason=reason)


def _merge(metric_id: str, method: str, value: Optional[float], parts, **extra) -> MetricValue:
    inputs, assumptions, reasons = [], [], []
    review = False
    for part in parts:
        if part is None:
            continue
        inputs.extend(getattr(part, 'inputs', None) or getattr(part, 'facts', []) or [])
        assumptions.extend(getattr(part, 'assumptions', []) or [])
        reasons.extend(getattr(part, 'review_reasons', []) or [])
        review = review or bool(getattr(part, 'requires_review', False))
    ends = [getattr(p, 'period_end', None) for p in parts if getattr(p, 'period_end', None)]
    return MetricValue(metric_id, value, method, inputs=sorted(set(inputs)),
                       assumptions=assumptions, requires_review=review,
                       review_reasons=reasons[:6], period_end=max(ends) if ends else None,
                       **extra)


class MetricCalculator:
    """Evaluate the declared metric set against one company's pack."""

    def __init__(self, pack: dict, config: Optional[dict] = None,
                 market_snapshot: Optional[dict] = None, as_of: Optional[str] = None):
        self.config = config or load_config()
        self.definitions = {row['id']: row for row in self.config['definitions']}
        self.index = FactIndex(pack, self.config['ttm_policy'],
                               selection=self.config.get('fact_selection'), as_of=as_of)
        self.market = dict(market_snapshot or {})
        self.components = self.config.get('components') or {}
        self.per_share_default = (self.config.get('per_share') or {}).get('denominators') or []
        self._cache: dict = {}
        self.anchor_fiscal_year: Optional[int] = None

    # ----------------------------------------------------------------- context
    def resolve_anchor(self, as_of: str) -> Optional[int]:
        """The most recent complete fiscal year with data, shared by every
        fiscal-year metric so that two CAGRs on one row cover the same span."""
        if self.anchor_fiscal_year is None:
            for metric in ('revenue', 'operating_cash_flow', 'total_assets'):
                year = self.index.latest_fiscal_year(metric, as_of)
                if year is not None:
                    self.anchor_fiscal_year = year
                    break
        return self.anchor_fiscal_year

    def evaluate(self, metric_id: str, context: tuple) -> MetricValue:
        key = (metric_id, context)
        if key in self._cache:
            return self._cache[key]
        self._cache[key] = _missing(metric_id, 'cycle', 'circular metric definition')
        result = self._evaluate(metric_id, context)
        self._cache[key] = result
        return result

    def _evaluate(self, metric_id: str, context: tuple) -> MetricValue:
        definition = self.definitions.get(metric_id)
        if definition is None:
            return _missing(metric_id, 'undefined', f'{metric_id} is not declared in config')
        handler = getattr(self, f'_kind_{definition["kind"]}', None)
        if handler is None:
            return _missing(metric_id, definition['kind'], f'unsupported kind {definition["kind"]!r}')
        result = handler(definition, context)
        if not result.ok and definition.get('fallback'):
            fallback = dict(definition['fallback'])
            fallback['id'] = metric_id
            handler = getattr(self, f'_kind_{fallback["kind"]}', None)
            if handler is not None:
                alternate = handler(fallback, context)
                if alternate.ok:
                    alternate.method = f'{alternate.method}(fallback)'
                    alternate.assumptions = list(alternate.assumptions) + [
                        f'{metric_id}: primary source unavailable ({result.reason}); '
                        f'used the declared fallback']
                    return alternate
        return result

    # ------------------------------------------------------------------- kinds
    def _window(self, source_metric: str, context: tuple, averaged: bool = False) -> Window:
        kind, point = context
        if source_metric in BALANCE_SHEET_METRICS:
            return self.index.instant(source_metric, point) if kind == 'ttm' \
                else self.index.fiscal_year_instant(source_metric, point)
        if kind == 'fy':
            return self.index.fiscal_year(source_metric, point)
        return self.index.ttm_average(source_metric, point) if averaged \
            else self.index.ttm(source_metric, point)

    def _kind_ttm(self, definition: dict, context: tuple) -> MetricValue:
        window = self._window(definition['source_metric'], context)
        if not window.ok:
            return _missing(definition['id'], window.method, window.reason)
        return _merge(definition['id'], window.method, window.value, [window])

    def _kind_ttm_average(self, definition: dict, context: tuple) -> MetricValue:
        window = self._window(definition['source_metric'], context, averaged=True)
        if not window.ok:
            return _missing(definition['id'], window.method, window.reason)
        return _merge(definition['id'], window.method, window.value, [window])

    def _kind_instant(self, definition: dict, context: tuple) -> MetricValue:
        return self._kind_ttm(definition, context)

    def _kind_component(self, definition: dict, context: tuple) -> MetricValue:
        spec = self.components.get(definition['component'])
        if spec is None:
            return _missing(definition['id'], 'component',
                            f'component {definition["component"]!r} is not declared')
        for preferred in spec.get('prefer') or []:
            window = self._window(preferred, context)
            if window.ok:
                return _merge(definition['id'], f'component:{preferred}', window.value, [window])

        total, parts, assumptions = 0.0, [], []
        for row in spec.get('sum_of') or []:
            window = self._window(row['metric'], context)
            if window.ok:
                total += window.value
                parts.append(window)
            elif row.get('required'):
                return _missing(definition['id'], 'component',
                                f'{row["metric"]} is required for {definition["component"]} '
                                f'and was not disclosed ({window.reason})')
            else:
                # Declared optional: treated as absent, and the assumption is
                # written down rather than being invisible in the total.
                assumptions.append(f'{definition["component"]}: {row["metric"]} not disclosed, '
                                   'treated as nil')
        if not parts:
            return _missing(definition['id'], 'component', 'no component was disclosed')
        result = _merge(definition['id'], 'component:sum', total, parts)
        result.assumptions = list(result.assumptions) + assumptions
        return result

    def _kind_difference(self, definition: dict, context: tuple) -> MetricValue:
        minuend = self.evaluate(definition['minuend'], context)
        subtrahend = self.evaluate(definition['subtrahend'], context)
        if not minuend.ok:
            return _missing(definition['id'], 'difference',
                            f'{definition["minuend"]} unavailable: {minuend.reason}')
        if not subtrahend.ok:
            return _missing(definition['id'], 'difference',
                            f'{definition["subtrahend"]} unavailable: {subtrahend.reason}')
        return _merge(definition['id'], 'difference', minuend.value - subtrahend.value,
                      [minuend, subtrahend])

    def _kind_sum(self, definition: dict, context: tuple) -> MetricValue:
        parts = [self.evaluate(name, context) for name in definition['metrics']]
        if any(not part.ok for part in parts):
            unavailable = [p.metric_id for p in parts if not p.ok]
            return _missing(definition['id'], 'sum', f'unavailable: {", ".join(unavailable)}')
        return _merge(definition['id'], 'sum', sum(p.value for p in parts), parts)

    def _kind_ratio(self, definition: dict, context: tuple) -> MetricValue:
        numerator = self.evaluate(definition['numerator'], context)
        denominator = self.evaluate(definition['denominator'], context)
        if not numerator.ok or not denominator.ok:
            unavailable = [p.metric_id for p in (numerator, denominator) if not p.ok]
            return _missing(definition['id'], 'ratio', f'unavailable: {", ".join(unavailable)}')
        if denominator.value == 0:
            return _missing(definition['id'], 'ratio',
                            f'{denominator.metric_id} is zero; a ratio would be undefined')
        if definition.get('denominator_must_be_positive') and denominator.value < 0:
            return _missing(definition['id'], 'ratio',
                            f'{denominator.metric_id} is negative ({denominator.value:,.0f}); '
                            'a ratio against it would invert the comparison')
        return _merge(definition['id'], 'ratio', numerator.value / denominator.value,
                      [numerator, denominator])

    def _shares(self, definition: dict, context: tuple) -> MetricValue:
        for name in (definition.get('denominator_preference') or self.per_share_default):
            window = self._window(name, context, averaged=True)
            if window.ok and window.value:
                return _merge(f'shares:{name}', f'shares:{name}', window.value, [window])
        return _missing('shares', 'per_share', 'no usable share count was disclosed')

    def _kind_per_share(self, definition: dict, context: tuple) -> MetricValue:
        amount = self.evaluate(definition['metric'], context)
        shares = self._shares(definition, context)
        if not amount.ok:
            return _missing(definition['id'], 'per_share',
                            f'{definition["metric"]} unavailable: {amount.reason}')
        if not shares.ok or not shares.value:
            return _missing(definition['id'], 'per_share', shares.reason or 'no share count')
        result = _merge(definition['id'], f'per_share({shares.method})',
                        amount.value / shares.value, [amount, shares])
        return result

    def _points(self, definition: dict, context: tuple, years: int) -> tuple:
        """The two endpoints a growth or CAGR compares."""
        kind, point = context
        if definition.get('basis') == 'fy' or kind == 'fy':
            anchor = point if kind == 'fy' else self.resolve_anchor(point)
            if anchor is None:
                return None, None, 'no complete fiscal year is available'
            return ('fy', anchor), ('fy', anchor - years), None
        from datetime import date
        cutoff = date.fromisoformat(point)
        try:
            earlier = cutoff.replace(year=cutoff.year - years)
        except ValueError:                      # 29 February
            earlier = cutoff.replace(year=cutoff.year - years, day=28)
        return ('ttm', point), ('ttm', earlier.isoformat()), None

    def _kind_growth(self, definition: dict, context: tuple) -> MetricValue:
        years = int(definition.get('years', 1))
        end_context, start_context, problem = self._points(definition, context, years)
        if problem:
            return _missing(definition['id'], 'growth', problem)
        end = self.evaluate(definition['metric'], end_context)
        start = self.evaluate(definition['metric'], start_context)
        if not end.ok or not start.ok:
            return _missing(definition['id'], 'growth',
                            f'endpoints unavailable: {end.reason or ""} {start.reason or ""}'.strip())
        if (self.config.get('growth_policy') or {}).get('require_positive_base', True) \
                and start.value <= 0:
            return _missing(definition['id'], 'growth',
                            f'base value is {start.value:,.0f}; a growth rate from a '
                            'non-positive base would misreport the direction')
        return _merge(definition['id'], f'growth:{definition.get("basis", "ttm")}',
                      end.value / start.value - 1.0, [end, start])

    def _kind_cagr(self, definition: dict, context: tuple) -> MetricValue:
        years = int(definition.get('years', 3))
        end_context, start_context, problem = self._points(definition, context, years)
        if problem:
            return _missing(definition['id'], 'cagr', problem)
        end = self.evaluate(definition['metric'], end_context)
        start = self.evaluate(definition['metric'], start_context)
        if not end.ok or not start.ok:
            return _missing(definition['id'], 'cagr',
                            f'endpoints unavailable: {end.reason or ""} {start.reason or ""}'.strip())
        require_positive = (self.config.get('cagr_policy') or {}).get('require_positive_endpoints', True)
        if require_positive and (start.value <= 0 or end.value <= 0):
            return _missing(definition['id'], 'cagr',
                            f'endpoint values {start.value:,.0f} → {end.value:,.0f} are not both '
                            'positive; a compound rate between them is undefined')
        return _merge(definition['id'], f'cagr:{years}y', (end.value / start.value) ** (1.0 / years) - 1.0,
                      [end, start])

    def _kind_market(self, definition: dict, context: tuple) -> MetricValue:
        value = self.market.get(definition['field'])
        if value is None and definition['field'] == 'market_cap':
            close, shares = self.market.get('close'), self.market.get('shares_outstanding')
            if close is not None and shares is not None:
                return MetricValue(definition['id'], close * shares, 'market:close*shares',
                                   period_end=self.market.get('as_of_date'))
        if value is None:
            return _missing(definition['id'], 'market',
                            f'no market observation for {definition["field"]}')
        return MetricValue(definition['id'], float(value), 'market',
                           period_end=self.market.get('as_of_date'))

    # ------------------------------------------------------------------ driver
    def compute(self, as_of: str, include_internal: bool = False) -> dict:
        """Every declared metric at the cutoff, with provenance for each."""
        if self.index.as_of is None:
            self.index = FactIndex(self.index.pack, self.config['ttm_policy'],
                                   selection=self.config.get('fact_selection'), as_of=as_of)
            self._cache.clear()
        context = ('ttm', as_of)
        self.resolve_anchor(as_of)
        values, provenance = {}, {}
        for definition in self.config['definitions']:
            if definition.get('internal') and not include_internal:
                continue
            result = self.evaluate(definition['id'], context)
            values[definition['id']] = result.value
            provenance[definition['id']] = result.to_dict()
        return {
            'as_of_date': as_of,
            'currency': self.index.currency,
            'consolidation_basis': self.index.consolidation_basis,
            'anchor_fiscal_year': self.anchor_fiscal_year,
            'facts_excluded': dict(self.index.excluded),
            'facts_without_filing_date': self.index.undated,
            'metrics': values,
            'provenance': provenance,
            'computed': sum(1 for v in values.values() if v is not None),
            'unavailable': sorted(k for k, v in values.items() if v is None),
            'requires_review': sorted(k for k, row in provenance.items()
                                      if row.get('requires_review')),
        }
