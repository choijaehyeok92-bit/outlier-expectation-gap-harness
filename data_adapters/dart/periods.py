"""Fiscal period arithmetic for Korean periodic reports.

This is the module most likely to be wrong in a way nobody notices, so it is
explicit about what it will not do.

A 3분기보고서 carries two different numbers for the same account: a three-month
figure and a nine-month cumulative one. Reading the cumulative as a quarter
triples a growth rate. So `thstrm_amount` becomes a `quarter` fact and
`thstrm_add_amount` becomes a `ytd` fact, and they are never merged.

Cash-flow statements are the trap inside the trap. Korean filers commonly
disclose cash flow on a cumulative basis only, which means the single column in
a 3분기보고서 is nine months of operating cash flow wearing a quarter's clothes.
The config marks the cash-flow statement `cumulative_only`, and this module
therefore refuses to emit a cash-flow quarter at all rather than inventing one.

When an interim income statement offers only one column and the report covers
more than three months, the period is genuinely ambiguous. The fallback records
it as `ytd` with `requires_review`, because understating a period is visible to
a reviewer and overstating one looks like growth.
"""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


def _end_of_month(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _shift_months(anchor: date, months: int) -> date:
    """Month arithmetic clamped to the month's last day."""
    total = (anchor.year * 12 + (anchor.month - 1)) + months
    year, month = divmod(total, 12)
    return _end_of_month(year, month + 1)


@dataclass(frozen=True)
class FiscalPeriods:
    fiscal_year: int
    fiscal_year_start: str
    fiscal_year_end: str
    period_end: str
    quarter: Optional[int]
    quarter_start: Optional[str]
    quarter_end: Optional[str]
    ytd_start: Optional[str]
    ytd_end: Optional[str]
    ytd_months: Optional[int]
    covers_months: int
    period_kind: str

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class PeriodResolver:
    """Turn (bsns_year, reprt_code, 결산월) into dated periods."""

    def __init__(self, config: dict):
        self.config = config
        self.report_codes = config['report_codes']
        self.statement_map = config['statement_map']
        self.columns = config['amount_columns']
        self.emit_ytd_when_equal = bool(
            config.get('emit_ytd_when_equal_to_quarter', False))
        self.ambiguous_policy = config.get('ambiguous_single_column', 'ytd_with_review')

    def report(self, reprt_code: str) -> dict:
        meta = self.report_codes.get(str(reprt_code))
        if meta is None:
            raise ValueError(f'unknown reprt_code {reprt_code!r}; declare it in config/dart.json')
        return meta

    def periods(self, bsns_year, reprt_code: str, fiscal_year_end_month: int = 12) -> FiscalPeriods:
        meta = self.report(reprt_code)
        year = int(bsns_year)
        month = int(fiscal_year_end_month or 12)
        if not 1 <= month <= 12:
            raise ValueError(f'fiscal year end month out of range: {fiscal_year_end_month!r}')

        fy_end = _end_of_month(year, month)
        fy_start = _shift_months(fy_end, -12) + timedelta(days=1)

        if meta['period_kind'] == 'fy':
            return FiscalPeriods(
                fiscal_year=year, fiscal_year_start=fy_start.isoformat(),
                fiscal_year_end=fy_end.isoformat(), period_end=fy_end.isoformat(),
                quarter=None, quarter_start=None, quarter_end=None,
                ytd_start=fy_start.isoformat(), ytd_end=fy_end.isoformat(), ytd_months=12,
                covers_months=12, period_kind='fy')

        quarter = int(meta['quarter'])
        ytd_months = int(meta.get('ytd_months') or quarter * 3)
        covers = int(meta.get('covers_months') or 3)
        quarter_end = _shift_months(fy_start - timedelta(days=1), ytd_months)
        quarter_start = _shift_months(quarter_end, -covers) + timedelta(days=1)
        return FiscalPeriods(
            fiscal_year=year, fiscal_year_start=fy_start.isoformat(),
            fiscal_year_end=fy_end.isoformat(), period_end=quarter_end.isoformat(),
            quarter=quarter, quarter_start=quarter_start.isoformat(),
            quarter_end=quarter_end.isoformat(),
            ytd_start=fy_start.isoformat(), ytd_end=quarter_end.isoformat(),
            ytd_months=ytd_months, covers_months=covers, period_kind='quarter')

    def statement_for(self, sj_div: str) -> dict:
        return self.statement_map.get(str(sj_div).upper(),
                                      {'statement': 'other', 'period_kind': 'flow'})

    def plan_row(self, sj_div: str, periods: FiscalPeriods,
                 current_amount, cumulative_amount) -> list:
        """Which dated facts one API row yields. Empty means: emit nothing.

        Returns dicts of {period_kind, period_start, period_end, fiscal_quarter,
        amount, column, requires_review, review_reason}.
        """
        statement = self.statement_for(sj_div)
        has_current = current_amount is not None
        has_cumulative = cumulative_amount is not None

        if statement['period_kind'] == 'instant':
            if not has_current:
                return []
            return [{'period_kind': 'instant', 'period_start': None,
                     'period_end': periods.period_end,
                     'fiscal_quarter': periods.quarter, 'amount': current_amount,
                     'column': self.columns['current_period'],
                     'requires_review': False, 'review_reason': None}]

        if periods.period_kind == 'fy':
            rows = []
            if has_current:
                rows.append({'period_kind': 'fy', 'period_start': periods.fiscal_year_start,
                             'period_end': periods.fiscal_year_end, 'fiscal_quarter': None,
                             'amount': current_amount, 'column': self.columns['current_period'],
                             'requires_review': False, 'review_reason': None})
            return rows

        # Interim report, flow statement.
        cumulative_only = bool(statement.get('cumulative_only'))
        rows = []

        if cumulative_only:
            # Never fabricate a three-month cash flow. Whatever single column the
            # filer gave is the cumulative one.
            amount = cumulative_amount if has_cumulative else current_amount
            if amount is None:
                return []
            conflict = has_cumulative and has_current and cumulative_amount != current_amount
            rows.append({
                'period_kind': 'ytd', 'period_start': periods.ytd_start,
                'period_end': periods.ytd_end, 'fiscal_quarter': periods.quarter,
                'amount': amount,
                'column': self.columns['current_cumulative'] if has_cumulative
                          else self.columns['current_period'],
                'requires_review': conflict,
                'review_reason': ('cash-flow row reported both a period and a cumulative column; '
                                  'the cumulative one was used') if conflict else None})
            return rows

        if has_current and has_cumulative:
            rows.append({'period_kind': 'quarter', 'period_start': periods.quarter_start,
                         'period_end': periods.quarter_end, 'fiscal_quarter': periods.quarter,
                         'amount': current_amount, 'column': self.columns['current_period'],
                         'requires_review': False, 'review_reason': None})
            if periods.ytd_months != periods.covers_months or self.emit_ytd_when_equal:
                rows.append({'period_kind': 'ytd', 'period_start': periods.ytd_start,
                             'period_end': periods.ytd_end, 'fiscal_quarter': periods.quarter,
                             'amount': cumulative_amount,
                             'column': self.columns['current_cumulative'],
                             'requires_review': False, 'review_reason': None})
            return rows

        if has_current and not has_cumulative:
            if periods.ytd_months == periods.covers_months:
                # Q1: the quarter and the year to date are the same three months.
                rows.append({'period_kind': 'quarter', 'period_start': periods.quarter_start,
                             'period_end': periods.quarter_end, 'fiscal_quarter': periods.quarter,
                             'amount': current_amount, 'column': self.columns['current_period'],
                             'requires_review': False, 'review_reason': None})
                return rows
            if self.ambiguous_policy == 'quarter_with_review':
                kind, start = 'quarter', periods.quarter_start
            else:
                kind, start = 'ytd', periods.ytd_start
            rows.append({
                'period_kind': kind, 'period_start': start, 'period_end': periods.period_end,
                'fiscal_quarter': periods.quarter, 'amount': current_amount,
                'column': self.columns['current_period'], 'requires_review': True,
                'review_reason': (f'{periods.ytd_months}-month interim report gave a single amount '
                                  f'column; recorded as {kind} pending confirmation of the '
                                  'reporting basis')})
            return rows

        if has_cumulative:
            rows.append({'period_kind': 'ytd', 'period_start': periods.ytd_start,
                         'period_end': periods.ytd_end, 'fiscal_quarter': periods.quarter,
                         'amount': cumulative_amount,
                         'column': self.columns['current_cumulative'],
                         'requires_review': False, 'review_reason': None})
        return rows
