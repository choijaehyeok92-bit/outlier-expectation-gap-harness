"""Index a Stage 0 financial pack and resolve dated windows over it.

This is the layer where a trailing-twelve-month figure is actually assembled,
and it is the layer where a screening warehouse most easily goes quietly wrong.
Three rules hold it up.

**A quarter and a year-to-date figure are never added together.** They overlap.
The Phase 3 adapters were careful to keep them apart as separate facts, and
throwing them back into one sum here would undo that. Each TTM method commits
to one period kind.

**Missing is missing.** A metric with no usable window returns `None` and the
reason why, never a zero. A screen that reads an undisclosed line as zero
reports a company as debt-free because it did not say.

**A segment is not the company.** A pack holds "Revenue by geography — APAC"
next to "Total revenue" for the same period, and reading the wrong one produces
a gross margin of 2,000% — which is exactly what the first run of this
warehouse over real filings did. Only facts with no segment, or a segment
declared consolidated, are eligible.

**Every value carries its provenance.** Which method produced it, which facts
it consumed, and whether any of those facts was itself flagged for review — a
Korean interim income statement with a single ambiguous column, for instance.
The number is usable; the flag travels with it.
"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

FLOW_KINDS = ('quarter', 'ytd', 'fy')


def _date(value) -> Optional[date]:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _value(fact: dict) -> Optional[float]:
    raw = fact.get('value_reported')
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        return None
    return float(raw) * float(fact.get('scale_multiplier') or 1.0)


def span_months(fact: dict) -> Optional[int]:
    start, end = _date(fact.get('period_start')), _date(fact.get('period_end'))
    if start is None or end is None:
        return None
    return int(round((end - start).days / 30.44))


@dataclass
class Window:
    """A resolved value plus everything needed to audit it."""
    value: Optional[float]
    method: str
    reason: Optional[str] = None
    facts: list = field(default_factory=list)
    requires_review: bool = False
    review_reasons: list = field(default_factory=list)
    period_end: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.value is not None

    def to_dict(self) -> dict:
        return {'value': self.value, 'method': self.method, 'reason': self.reason,
                'facts': self.facts, 'requires_review': self.requires_review,
                'review_reasons': self.review_reasons, 'period_end': self.period_end}


def missing(method: str, reason: str) -> Window:
    return Window(value=None, method=method, reason=reason)


class FactIndex:
    """Facts from one pack, grouped for window resolution.

    The pack has already committed to a single consolidation basis, so nothing
    here has to choose between 연결 and 별도 — that decision was made once, at
    ingestion, and mixing them was refused there.
    """

    def __init__(self, pack: dict, policy: dict, selection: Optional[dict] = None,
                 as_of: Optional[str] = None):
        self.pack = pack
        self.policy = policy
        self.selection = selection or {}
        self.as_of = as_of
        self.currency = pack.get('reporting_currency')
        self.consolidation_basis = pack.get('consolidation_basis')
        self.excluded = {'segment': 0, 'post_cutoff': 0, 'no_value': 0, 'statement': 0}
        self.undated = 0
        self.by_metric: dict = {}
        for fact in pack.get('facts') or []:
            if _value(fact) is None:
                self.excluded['no_value'] += 1
                continue
            if not self._eligible(fact):
                continue
            self.by_metric.setdefault(fact.get('metric'), []).append(fact)
        for rows in self.by_metric.values():
            rows.sort(key=lambda f: (f.get('period_end') or '', f.get('filing_date') or ''))

    def _eligible(self, fact: dict) -> bool:
        if fact.get('statement') in (self.selection.get('exclude_statements') or []):
            self.excluded['statement'] += 1
            return False
        segment = fact.get('segment')
        if segment is not None:
            allowed = {s.lower() for s in
                       (self.selection.get('consolidated_segment_labels') or [])}
            if str(segment).strip().lower() not in allowed:
                self.excluded['segment'] += 1
                return False
        filed = fact.get('filing_date')
        if filed is None:
            self.undated += 1
        elif (self.selection.get('require_filing_date_at_or_before_as_of', True)
              and self.as_of and filed > self.as_of):
            # A figure disclosed after the cutoff is information this run did
            # not have, whatever period it describes.
            self.excluded['post_cutoff'] += 1
            return False
        return True

    def _pick(self, rows: list, label: str) -> tuple:
        """The newest-filed row, plus any conflicting value at the same period.

        Two consolidated figures for one period mean a restatement or a
        definitional difference. The later filing is used and the alternative is
        surfaced rather than dropped.
        """
        if not rows:
            return None, []
        chosen = rows[-1]
        period = chosen.get('period_end')
        rivals = [f for f in rows
                  if f.get('period_end') == period and _value(f) != _value(chosen)]
        if not rivals or not self.selection.get('flag_conflicting_values', True):
            return chosen, []
        return chosen, [f'{label}: {len(rivals)} other value(s) disclosed for {period} '
                        f'(using {chosen.get("fact_id")}, newest filing)']

    # ------------------------------------------------------------------ lookups
    def _rows(self, metric: str, kind: str, as_of: Optional[str] = None) -> list:
        rows = [f for f in self.by_metric.get(metric, []) if f.get('period_kind') == kind]
        if as_of:
            rows = [f for f in rows if (f.get('period_end') or '') <= as_of]
        return rows

    @staticmethod
    def _review(facts: list) -> tuple:
        flagged = [f for f in facts if f.get('requires_review')]
        return bool(flagged), [f"{f.get('fact_id')}: {f.get('review_reason')}" for f in flagged][:4]

    def instant(self, metric: str, as_of: str) -> Window:
        """The latest balance-sheet observation at or before the cutoff."""
        rows = self._rows(metric, 'instant', as_of)
        if not rows:
            return missing('instant', f'no instant fact for {metric} at or before {as_of}')
        fact, conflicts = self._pick(rows, metric)
        review, reasons = self._review([fact])
        return Window(_value(fact), 'instant', facts=[fact.get('fact_id')],
                      requires_review=review or bool(conflicts),
                      review_reasons=reasons + conflicts,
                      period_end=fact.get('period_end'))

    def fiscal_year(self, metric: str, year: int) -> Window:
        rows = [f for f in self._rows(metric, 'fy') if f.get('fiscal_year') == year]
        if not rows:
            return missing('fy', f'no fiscal-year fact for {metric} in FY{year}')
        fact, conflicts = self._pick(rows, f'{metric} FY{year}')
        review, reasons = self._review([fact])
        return Window(_value(fact), 'fy', facts=[fact.get('fact_id')],
                      requires_review=review or bool(conflicts),
                      review_reasons=reasons + conflicts,
                      period_end=fact.get('period_end'))

    def fiscal_year_instant(self, metric: str, year: int) -> Window:
        """A balance-sheet line as at a fiscal year end."""
        rows = [f for f in self._rows(metric, 'instant') if f.get('fiscal_year') == year]
        if not rows:
            return missing('fy_instant', f'no instant fact for {metric} at FY{year} end')
        fact = max(rows, key=lambda f: f.get('period_end') or '')
        review, reasons = self._review([fact])
        return Window(_value(fact), 'fy_instant', facts=[fact.get('fact_id')],
                      requires_review=review, review_reasons=reasons,
                      period_end=fact.get('period_end'))

    def latest_fiscal_year(self, metric: str, as_of: str) -> Optional[int]:
        rows = self._rows(metric, 'fy', as_of)
        return rows[-1].get('fiscal_year') if rows else None

    # ---------------------------------------------------------------- TTM paths
    def ttm(self, metric: str, as_of: str) -> Window:
        """Trailing twelve months from the most recent window any method can build.

        Every declared method is tried, and the winner is the one whose window
        ends latest — not simply the first that succeeds. A company that has
        filed both a nine-month interim and a full year since should be measured
        to the full year; taking the first workable method would quietly report
        a window three months stale. Ties go to the earlier-listed method, which
        is the more precise one.
        """
        methods = self.policy.get('methods', ('four_quarters', 'fy_ytd_bridge', 'latest_fy'))
        attempts, candidates = [], []
        for rank, method in enumerate(methods):
            window = getattr(self, f'_ttm_{method}')(metric, as_of)
            if not window.ok:
                attempts.append(f'{method}: {window.reason}')
                continue
            if self._stale(window, as_of):
                attempts.append(f'{method}: window ends {window.period_end}, older than '
                                f"{self.policy.get('max_staleness_days')} days before {as_of}")
                continue
            candidates.append((window.period_end or '', -rank, window))
        if not candidates:
            return missing('ttm', '; '.join(attempts) or f'no TTM path for {metric}')
        return max(candidates, key=lambda row: (row[0], row[1]))[2]

    def _stale(self, window: Window, as_of: str) -> bool:
        limit = self.policy.get('max_staleness_days')
        end, cutoff = _date(window.period_end), _date(as_of)
        if not limit or end is None or cutoff is None:
            return False
        return (cutoff - end).days > int(limit)

    def _ttm_four_quarters(self, metric: str, as_of: str) -> Window:
        """Four contiguous quarters. A gap disqualifies the window entirely."""
        rows = [f for f in self._rows(metric, 'quarter', as_of)
                if _date(f.get('period_start')) and _date(f.get('period_end'))]
        if len(rows) < 4:
            return missing('four_quarters', f'only {len(rows)} quarterly fact(s) available')
        rows.sort(key=lambda f: f.get('period_end') or '', reverse=True)
        gap = timedelta(days=int(self.policy.get('max_gap_days', 10)))
        chain = [rows[0]]
        for candidate in rows[1:]:
            expected = _date(chain[-1]['period_start']) - timedelta(days=1)
            if abs((_date(candidate['period_end']) - expected).days) <= gap.days:
                chain.append(candidate)
            if len(chain) == 4:
                break
        if len(chain) < 4:
            return missing('four_quarters', 'quarterly facts are not contiguous')
        review, reasons = self._review(chain)
        return Window(sum(_value(f) for f in chain), 'four_quarters',
                      facts=[f.get('fact_id') for f in chain],
                      requires_review=review, review_reasons=reasons,
                      period_end=chain[0].get('period_end'))

    def _ttm_fy_ytd_bridge(self, metric: str, as_of: str) -> Window:
        """Prior full year, plus this year to date, less last year to the same date.

        This is the path Korean cash-flow statements need, because they disclose
        cumulative figures only and therefore never offer four quarters.
        """
        ytds = [f for f in self._rows(metric, 'ytd', as_of) if span_months(f)]
        if not ytds:
            return missing('fy_ytd_bridge', 'no year-to-date fact available')
        current = ytds[-1]
        months = span_months(current)
        if months and months >= 11:
            review, reasons = self._review([current])
            return Window(_value(current), 'fy_ytd_bridge_full_year',
                          facts=[current.get('fact_id')], requires_review=review,
                          review_reasons=reasons, period_end=current.get('period_end'))
        year = current.get('fiscal_year')
        if year is None:
            return missing('fy_ytd_bridge', 'year-to-date fact carries no fiscal year')
        prior = [f for f in self._rows(metric, 'ytd')
                 if f.get('fiscal_year') == year - 1 and span_months(f) == months]
        if not prior:
            return missing('fy_ytd_bridge',
                           f'no FY{year - 1} year-to-date fact covering the same {months} months')
        full_year = self.fiscal_year(metric, year - 1)
        if not full_year.ok:
            return missing('fy_ytd_bridge', f'no FY{year - 1} full-year fact')
        used = [current, prior[-1]]
        review, reasons = self._review(used)
        return Window(full_year.value + _value(current) - _value(prior[-1]), 'fy_ytd_bridge',
                      facts=full_year.facts + [f.get('fact_id') for f in used],
                      requires_review=review or full_year.requires_review,
                      review_reasons=reasons + full_year.review_reasons,
                      period_end=current.get('period_end'))

    def _ttm_latest_fy(self, metric: str, as_of: str) -> Window:
        rows = self._rows(metric, 'fy', as_of)
        if not rows:
            return missing('latest_fy', 'no full-year fact at or before the cutoff')
        fact, conflicts = self._pick(rows, metric)
        review, reasons = self._review([fact])
        return Window(_value(fact), 'latest_fy', facts=[fact.get('fact_id')],
                      requires_review=review or bool(conflicts),
                      review_reasons=reasons + conflicts,
                      period_end=fact.get('period_end'))

    def ttm_average(self, metric: str, as_of: str) -> Window:
        """A share count is averaged over the window, never summed.

        Adding four quarterly weighted-average share counts would report a
        company with four times its shares outstanding.
        """
        full_year = self._ttm_latest_fy(metric, as_of)
        if full_year.ok:
            return Window(full_year.value, 'fy_average', facts=full_year.facts,
                          requires_review=full_year.requires_review,
                          review_reasons=full_year.review_reasons,
                          period_end=full_year.period_end)
        quarters = self._ttm_four_quarters(metric, as_of)
        if quarters.ok:
            return Window(quarters.value / 4.0, 'four_quarter_average', facts=quarters.facts,
                          requires_review=quarters.requires_review,
                          review_reasons=quarters.review_reasons,
                          period_end=quarters.period_end)
        rows = self._rows(metric, 'instant', as_of)
        if rows:
            fact = rows[-1]
            return Window(_value(fact), 'latest_instant', facts=[fact.get('fact_id')],
                          period_end=fact.get('period_end'))
        return missing('ttm_average', f'no usable share count for {metric}')
