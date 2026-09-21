"""Read XBRL company facts into normalized facts.

Two problems make this less mechanical than it looks.

**Period kind.** A company-facts entry gives `start` and `end` and leaves the
reader to work out whether that is a quarter, a year to date, or a full year.
The span decides it, with the bands declared in `config/sec.json`; a span that
matches no band is recorded as `ytd` with `requires_review` rather than being
assigned a kind that flatters it.

**Restatement.** The same tag, period and unit appears once per filing that
disclosed it, so a single fiscal year can carry four or five entries with
different `filed` dates and occasionally different values. The reader keeps the
most recent one filed at or before the cutoff — a later filing is information
the run did not have — and when an earlier filing had reported a different
number, the kept fact is flagged `is_restated` with the superseded value
preserved. Silently keeping the newest value would erase the fact that the
company changed its mind.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


def _date(value) -> Optional[date]:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def month_span(start, end) -> Optional[float]:
    first, last = _date(start), _date(end)
    if first is None or last is None:
        return None
    return round((last - first).days / 30.44, 2)


def period_kind_for(start, end, policy: dict) -> tuple:
    """(period_kind, requires_review, reason)."""
    if not start:
        return ('instant', False, None) if policy.get('instant_when_no_start', True) \
            else ('ytd', True, 'no start date')
    span = month_span(start, end)
    if span is None:
        return 'ytd', True, 'unreadable period dates'
    for band in policy['bands']:
        if band['min_months'] <= span <= band['max_months']:
            return band['period_kind'], False, None
    fallback = 'quarter' if policy.get('unmatched_policy') == 'quarter_with_review' else 'ytd'
    return fallback, True, f'{span:.1f}-month span matches no declared period band'


@dataclass(frozen=True)
class FactEntry:
    tag: str
    taxonomy: str
    metric: str
    unit: str
    value: float
    start: Optional[str]
    end: Optional[str]
    filed: str
    form: Optional[str]
    accession: Optional[str]
    fiscal_year: Optional[int]
    fiscal_period: Optional[str]
    frame: Optional[str]


class CompanyFactsReader:
    """Turn one `companyfacts` payload into deduplicated, dated entries."""

    def __init__(self, config: dict):
        self.config = config
        self.tag_map = config['tag_map']
        self.review_tags = config.get('review_required_tags') or {}
        self.period_policy = config['period_spans']
        self.unit_kinds = config.get('unit_kinds') or {}

    def metric_for(self, taxonomy: str, tag: str):
        """(metric, metric_detail, requires_review, reason) or None to skip."""
        escalation = self.review_tags.get(tag)
        if escalation:
            return (escalation.get('metric', 'other'), escalation.get('metric_detail'),
                    True, ' '.join(str(escalation.get('reason', '')).split()))
        metric = (self.tag_map.get(taxonomy) or {}).get(tag)
        if metric is None:
            return None
        return metric, None, False, None

    def entries(self, payload: dict, as_of_date: str) -> list:
        """Every mapped fact filed at or before the cutoff, newest filing first."""
        rows = []
        for taxonomy, tags in (payload.get('facts') or {}).items():
            for tag, body in (tags or {}).items():
                mapped = self.metric_for(taxonomy, tag)
                if mapped is None:
                    continue
                metric = mapped[0]
                for unit, observations in ((body or {}).get('units') or {}).items():
                    for row in observations or []:
                        filed = str(row.get('filed') or '')
                        if not filed or filed > as_of_date:
                            continue           # the cutoff is absolute, here as everywhere
                        value = row.get('val')
                        if not isinstance(value, (int, float)) or isinstance(value, bool):
                            continue
                        rows.append(FactEntry(
                            tag=tag, taxonomy=taxonomy, metric=metric, unit=unit,
                            value=float(value), start=row.get('start'), end=row.get('end'),
                            filed=filed, form=row.get('form'), accession=row.get('accn'),
                            fiscal_year=row.get('fy'), fiscal_period=row.get('fp'),
                            frame=row.get('frame')))
        rows.sort(key=lambda r: (r.filed, r.accession or ''), reverse=True)
        return rows

    def deduplicate(self, entries: list) -> list:
        """One entry per (tag, unit, period). Restatements are flagged, not hidden."""
        policy = self.config.get('restatement') or {}
        flag_changes = bool(policy.get('flag_when_value_changed', True))
        kept: dict = {}
        superseded: dict = {}
        for entry in entries:                   # already newest-first
            key = (entry.taxonomy, entry.tag, entry.unit, entry.start, entry.end)
            if key not in kept:
                kept[key] = entry
            elif flag_changes and entry.value != kept[key].value:
                superseded.setdefault(key, []).append(
                    {'value': entry.value, 'filed': entry.filed, 'form': entry.form,
                     'accession': entry.accession})
        return [(entry, superseded.get(key, [])) for key, entry in kept.items()]

    def unit_kind(self, unit: str) -> str:
        return self.unit_kinds.get(unit, 'currency' if unit.startswith('USD') else 'count')

    def fiscal_quarter(self, entry: FactEntry) -> Optional[int]:
        period = str(entry.fiscal_period or '').upper()
        if period.startswith('Q') and period[1:].isdigit():
            return int(period[1:])
        return None
