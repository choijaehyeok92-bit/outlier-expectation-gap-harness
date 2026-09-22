"""Turning a declared threshold into a comparison, or admitting it cannot be.

Agent reports write thresholds as prose: `73% 이상`, `전년 대비 증가`, `-20%p
이상`. A deep dive is meant to write them typed, but the schema allows a string
there too. Monitoring has to compare an observation against them, and there are
only two honest ways to do that: reduce the text to a number and an operator by
rules anyone can read, or say plainly that it could not be reduced.

The second case is the important one, and a first draft of this module got it
wrong in a way worth recording. Searching the text for *any* number read
`quantified and rising breached for 2 consecutive periods` as `>= 2`, and
`>=revenue growth breached for…` as `>= 2` as well — nonsense, presented as a
checked threshold, which is worse than no check at all.

So the match is whole-string and strict. A comparator is removed, and what
remains must be **nothing but** a number and an allowlisted unit. Any leftover
word means the threshold says something this module does not implement — a
comparison against another series (`>=revenue growth`), a persistence rule
(`breached for 2 consecutive periods`), a qualitative condition (`quantified
and rising`) — and the answer is `None` rather than an interpretation. The item
is then reported as `not_machine_checkable` with its original wording intact
and a person reads it, exactly as the screener surfaces
`unresolved_conditions`.

No model is involved at any point. The comparators and magnitude words come
from `config/screening_lexicon.json`, the same table the screener parses with.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
LEXICON = ROOT / 'config' / 'screening_lexicon.json'

# `>=` before `>` so the longer symbol wins; Korean comparators come from the
# lexicon and are matched longest-first for the same reason.
_SYMBOLS = (('>=', '>='), ('≥', '>='), ('<=', '<='), ('≤', '<='), ('>', '>'), ('<', '<'))

# What may follow the number and still leave the threshold machine-checkable.
# Anything outside this list is prose the parser does not pretend to read.
_PERCENT_POINT_UNITS = ('%p', '% p', 'pp', '퍼센트포인트', '퍼센트 포인트')
_RATIO_UNITS = ('%', '퍼센트', 'percent', 'pct')
_PLAIN_UNITS = ('x', '배', '조', '억', '만', '천', 'trillion', 'billion', 'million', 'thousand',
                'bn', 'mn', 't', 'b', 'm', 'k', '원', 'krw', '₩', 'usd', '$', 'won', 'dollar')
_UNITS = sorted(_PERCENT_POINT_UNITS + _RATIO_UNITS + _PLAIN_UNITS, key=len, reverse=True)
_NUMBER_ONLY = re.compile(
    r'^\s*(?P<num>-?\d+(?:[.,]\d+)?)\s*(?P<unit>' +
    '|'.join(re.escape(u) for u in _UNITS) + r')?\s*$', re.I)


@dataclass(frozen=True)
class Comparison:
    """`operator` applied to `value`: the observation must satisfy it to be ok."""
    operator: str                    # >= | <= | > | <
    value: float
    unit: str                        # ratio | percent_point | number
    source_text: str

    def satisfied_by(self, observed: float) -> bool:
        if self.operator == '>=':
            return observed >= self.value
        if self.operator == '>':
            return observed > self.value
        if self.operator == '<=':
            return observed <= self.value
        return observed < self.value

    def to_dict(self) -> dict:
        return {'operator': self.operator, 'value': self.value, 'unit': self.unit,
                'source_text': self.source_text}


def _lexicon() -> dict:
    import json
    return json.loads(LEXICON.read_text(encoding='utf-8'))


def comparator_in(text: str, lexicon: Optional[dict] = None) -> Optional[str]:
    """The comparison the threshold's own wording states, if it states one."""
    return _strip_comparator(str(text), lexicon if lexicon is not None else _lexicon())[1]


def _strip_comparator(raw: str, lexicon: dict) -> tuple:
    """`(remainder, operator)` — the comparator removed, not merely detected.

    Removing it is what makes the strict match below safe: a comparator word
    that matched by accident leaves a remainder that is not a bare number, so
    the threshold is refused rather than half-read.
    """
    for token, operator in _SYMBOLS:
        if token in raw:
            return raw.replace(token, ' ', 1), operator
    table = lexicon.get('comparators') or {}
    lowered = raw.lower()
    for token in sorted(table, key=len, reverse=True):
        index = lowered.find(token.lower())
        if index >= 0:
            return raw[:index] + ' ' + raw[index + len(token):], table[token]
    return raw, None


def _number(text: str, lexicon: dict):
    """`(value, unit)` when the text is nothing but a number and a known unit.

    Whole-string, deliberately. `20%` parses; `20% breached for 2 consecutive
    periods` does not, because the extra words state a persistence rule this
    module does not evaluate.
    """
    match = _NUMBER_ONLY.match(str(text))
    if not match:
        return None
    number = float(match.group('num').replace(',', ''))
    unit = (match.group('unit') or '').strip().lower()
    if unit in [u.lower() for u in _PERCENT_POINT_UNITS]:
        return number / 100.0, 'percent_point'
    if unit in [u.lower() for u in _RATIO_UNITS]:
        return number / 100.0, 'ratio'
    scales = {k.lower(): float(v) for k, v in (lexicon.get('number_scales') or {}).items()}
    if unit in scales:
        number *= scales[unit]
    return number, 'number'


def parse(text, direction_required: Optional[str] = None,
          direction_operators: Optional[dict] = None,
          lexicon: Optional[dict] = None) -> Optional[Comparison]:
    """A `Comparison`, or None when the text cannot be reduced to one.

    A number alone is not enough: something has to say which side of it is
    acceptable. The threshold's own wording says so first; `direction_required`
    from the report says so second; `stable` says nothing usable, because a
    two-sided band needs a reference value that nobody declared.
    """
    if text is None or (isinstance(text, str) and not text.strip()):
        return None
    lexicon = lexicon if lexicon is not None else _lexicon()

    if isinstance(text, (int, float)) and not isinstance(text, bool):
        # A bare number states no side, so the report's declared direction is
        # the only thing that can supply one.
        value, unit, stated, source = float(text), 'number', None, repr(text)
    else:
        source = str(text)
        remainder, stated = _strip_comparator(source, lexicon)
        parsed = _number(remainder, lexicon)
        if parsed is None:
            return None
        value, unit = parsed

    operator = stated or (direction_operators or {}).get(direction_required)
    if not operator:
        return None
    return Comparison(operator=operator, value=value, unit=unit, source_text=source)


RATIO_UNITS = ('ratio', 'percent_point')
DECLARED_UNITS = {'ratio': 1.0, 'percent': 0.01, 'percent_point': 0.01, 'number': 1.0}


def observed_number(value, unit: str, declared_unit: Optional[str] = None,
                    lexicon: Optional[dict] = None) -> tuple:
    """`(number, None)` on the threshold's scale, or `(None, reason)`.

    The hazard this guards against is one silent inversion. A gross margin of
    71% recorded as the bare number `71`, compared against a threshold written
    `73% 이상` (0.73), satisfies `>= 0.73` and reports **ok** for what is in
    truth a breach. Dividing by 100 on a hunch is no better: a debt-to-equity
    of 2.0 is a real ratio above 1.

    So nothing is rescaled on a guess. A bare number above 1 against a
    fraction-scaled threshold is refused, and the recorder is asked to say
    which they meant — `--unit percent`, or `71%` in the value itself. Once
    said, it is arithmetic.
    """
    if value is None or isinstance(value, bool):
        return None, 'no numeric observation'
    if declared_unit:
        if declared_unit not in DECLARED_UNITS:
            return None, f'unknown observation unit {declared_unit!r}'
        raw = value if isinstance(value, (int, float)) else _bare(value)
        if raw is None:
            return None, f'{value!r} is not a number'
        return float(raw) * DECLARED_UNITS[declared_unit], None
    if isinstance(value, (int, float)):
        if unit in RATIO_UNITS and abs(value) > 1:
            return None, (f'{value} is ambiguous against a threshold on a 0–1 scale: record it '
                          f'as {value}% or pass an explicit unit')
        return float(value), None
    lexicon = lexicon if lexicon is not None else _lexicon()
    parsed = _number(_strip_comparator(str(value), lexicon)[0], lexicon)
    if parsed is None:
        return None, f'{value!r} could not be read as a number'
    number, observed_unit = parsed
    if unit in RATIO_UNITS and observed_unit == 'number' and abs(number) > 1:
        return None, (f'{value!r} is ambiguous against a threshold on a 0–1 scale: write a '
                      f'percent marker or pass an explicit unit')
    return number, None


def _bare(text) -> Optional[float]:
    match = re.search(r'-?\d+(?:[.,]\d+)?', str(text))
    return float(match.group(0).replace(',', '')) if match else None
