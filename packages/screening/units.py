"""Unit and magnitude parsing for screening thresholds.

Two rules hold this module up:

1. A percentage is a decimal fraction. "15%" is 0.15, never 15. The harness
   makes the same distinction (growth .15 is 15%), and a screener that got it
   wrong would silently return an empty or an absurd universe.
2. A currency amount keeps the currency it was written in. "1조" written by a
   Korean user means 1e12 KRW, and this module says so rather than quietly
   comparing it against a USD column. The compiler, not the parser, decides
   what to do without an FX rate.
"""
import re

_NUMBER = re.compile(r'(?P<num>\d+(?:[.,]\d+)?)\s*(?P<scale>조|억|만|천|trillion|billion|million|thousand|bn|mn|[tbmk])?', re.I)


class UnitError(ValueError):
    """The text could not be read as a number with a unit, and no guess is made."""


def _scales(lexicon):
    return {k.lower(): float(v) for k, v in (lexicon.get('number_scales') or {}).items()}


def _currencies(lexicon):
    return {k.lower(): v for k, v in (lexicon.get('currency_tokens') or {}).items()}


def parse_number(text, lexicon):
    """A bare magnitude with an optional Korean/English scale word."""
    match = _NUMBER.search(str(text))
    if not match:
        raise UnitError(f'no number in {text!r}')
    value = float(match.group('num').replace(',', ''))
    scale = (match.group('scale') or '').lower()
    if scale:
        table = _scales(lexicon)
        if scale not in table:
            raise UnitError(f'unknown scale {scale!r}')
        value *= table[scale]
    return value


def parse_percent(text):
    """`15%` and `15 퍼센트` become 0.15. A bare `0.15` stays 0.15.

    A number carrying a percent marker wins over any other number in the text,
    so "최근 3년 매출 CAGR 15% 이상" reads 15%, not the 3 in "3년". A bare number
    greater than 1 with no percent marker is ambiguous, so it is rejected
    rather than divided by 100 on a guess.
    """
    raw = str(text).strip()
    marked = re.search(r'(?P<num>-?\d+(?:[.,]\d+)?)\s*(?:%|퍼센트|percent|pct)', raw, re.I)
    if marked:
        return float(marked.group('num').replace(',', '')) / 100.0
    bare = re.search(r'(?P<num>-?\d+(?:[.,]\d+)?)', raw)
    if not bare:
        raise UnitError(f'no number in {text!r}')
    value = float(bare.group('num').replace(',', ''))
    if abs(value) > 1:
        raise UnitError(f'{text!r} is ambiguous: write 15% or 0.15, not 15')
    return value


def detect_currency(text, lexicon, default=None):
    """The currency a threshold was written in, or the declared default."""
    lowered = str(text).lower()
    for token, code in sorted(_currencies(lexicon).items(), key=lambda kv: -len(kv[0])):
        if token in lowered:
            return code
    return default


def parse_currency_amount(text, lexicon, default_currency=None):
    """Returns (value, currency). Currency may be None when the text did not say."""
    value = parse_number(text, lexicon)
    scale_used = bool(re.search(r'조|억|만|천', str(text)))
    # A Korean magnitude word with no currency token is a Korean-won amount by
    # convention; an English one carries no such convention and stays unknown.
    currency = detect_currency(text, lexicon, 'KRW' if scale_used else default_currency)
    return value, currency


def convert(value, from_currency, to_currency, fx_rates):
    """Convert with an explicitly supplied rate, or raise. No rate is ever invented.

    `fx_rates` maps a currency code to {'per_usd': float, ...}: units of that
    currency per one USD.
    """
    if from_currency == to_currency or from_currency is None or to_currency is None:
        return value
    rates = {'USD': 1.0}
    for code, row in (fx_rates or {}).items():
        try:
            rates[code.upper()] = float(row['per_usd'])
        except (KeyError, TypeError, ValueError):
            continue
    source, target = from_currency.upper(), to_currency.upper()
    if source not in rates or target not in rates:
        raise UnitError(f'no as-of FX rate for {source}->{target}')
    return value / rates[source] * rates[target]
