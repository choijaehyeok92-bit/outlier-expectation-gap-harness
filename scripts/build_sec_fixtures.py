#!/usr/bin/env python3
"""Generate offline SEC EDGAR fixtures.

Synthesized from the published EDGAR/XBRL response shapes, not captured from
`data.sec.gov`: this environment's network policy blocks it. The envelopes,
field names and the `units → [{start, end, val, filed, form, accn, fy, fp}]`
layout follow the documented structure; the figures are illustrative.

Refresh for real with `RecordingTransport` once egress exists:

    provider = SecEdgarProvider(transport=RecordingTransport('data_adapters/fixtures/sec'))

    python scripts/build_sec_fixtures.py
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_adapters.testing import fixture_key  # noqa: E402

OUT = ROOT / 'data_adapters' / 'fixtures' / 'sec'
CIK = 789019                       # Microsoft's real CIK; the numbers below are not.
TICKER = 'MSFT'
NAME = 'MICROSOFT CORP'
FY_END = (6, 30)                   # June fiscal year end, so the period bands get exercised

ANNUAL_REVENUE = {2022: 198_300_000_000, 2023: 211_900_000_000, 2024: 245_100_000_000,
                  2025: 281_700_000_000, 2026: 324_400_000_000}
QUARTER_SHARE = [0.235, 0.245, 0.255, 0.265]

TAGS = [
    ('RevenueFromContractWithCustomerExcludingAssessedTax', 'USD', 1.0),
    ('CostOfRevenue', 'USD', 0.30),
    ('GrossProfit', 'USD', 0.70),
    ('ResearchAndDevelopmentExpense', 'USD', 0.12),
    ('SellingGeneralAndAdministrativeExpense', 'USD', 0.10),
    ('OperatingIncomeLoss', 'USD', 0.45),
    ('NetIncomeLoss', 'USD', 0.36),
    ('NetCashProvidedByUsedInOperatingActivities', 'USD', 0.50),
    ('PaymentsToAcquirePropertyPlantAndEquipment', 'USD', 0.26),
    ('ShareBasedCompensation', 'USD', 0.04),
]
SHARE_TAGS = [
    ('WeightedAverageNumberOfDilutedSharesOutstanding', 'shares', 7_600_000_000, -45_000_000),
]
INSTANTS = [
    ('CashAndCashEquivalentsAtCarryingValue', 'USD', 0.09),
    ('Assets', 'USD', 2.10),
    ('Liabilities', 'USD', 0.95),
    ('StockholdersEquity', 'USD', 1.15),
    ('LongTermDebtNoncurrent', 'USD', 0.14),
    ('ShortTermBorrowings', 'USD', 0.02),
    ('Goodwill', 'USD', 0.42),
]


def write(url: str, payload) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    key = fixture_key(url)
    name = key if key.endswith('.json') else f'{key}.json'
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n',
                            encoding='utf-8')


def fy_bounds(fiscal_year: int):
    end = date(fiscal_year, *FY_END)
    start = date(fiscal_year - 1, FY_END[0], FY_END[1]) + \
        (date(fiscal_year - 1, FY_END[0], FY_END[1]).max - date(fiscal_year - 1, FY_END[0], FY_END[1]).max)
    return date(fiscal_year - 1, FY_END[0] + 1, 1), end


def quarter_bounds(fiscal_year: int, quarter: int):
    start_month = FY_END[0] + 1 + 3 * (quarter - 1)
    year = fiscal_year - 1 + (start_month - 1) // 12
    start_month = (start_month - 1) % 12 + 1
    start = date(year, start_month, 1)
    end_month = start_month + 2
    end_year = year + (end_month - 1) // 12
    end_month = (end_month - 1) % 12 + 1
    import calendar
    return start, date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])


def filings_rows():
    rows = []
    for fiscal_year in sorted(ANNUAL_REVENUE):
        _start, end = fy_bounds(fiscal_year)
        rows.append({'form': '10-K', 'filingDate': (end.replace(month=7, day=30)).isoformat(),
                     'accessionNumber': f'0000950170-{str(fiscal_year)[2:]}-0001{fiscal_year % 100:02d}',
                     'primaryDocument': f'msft-{fiscal_year}0630.htm',
                     'reportDate': end.isoformat(), 'primaryDocDescription': '10-K'})
        for quarter in (1, 2, 3):
            _qs, qe = quarter_bounds(fiscal_year, quarter)
            filed = date(qe.year + (1 if qe.month == 12 else 0),
                         (qe.month % 12) + 1, 28)
            rows.append({'form': '10-Q', 'filingDate': filed.isoformat(),
                         'accessionNumber': f'0000950170-{str(qe.year)[2:]}-000{quarter}{fiscal_year % 100:02d}',
                         'primaryDocument': f'msft-{qe.isoformat().replace("-", "")}.htm',
                         'reportDate': qe.isoformat(), 'primaryDocDescription': '10-Q'})
    rows.append({'form': 'DEF 14A', 'filingDate': '2025-10-16',
                 'accessionNumber': '0001193125-25-267270',
                 'primaryDocument': 'd12345ddef14a.htm', 'reportDate': '2025-10-16',
                 'primaryDocDescription': 'DEF 14A'})
    rows.append({'form': '8-K', 'filingDate': '2026-07-29',
                 'accessionNumber': '0001193125-26-380280',
                 'primaryDocument': 'd8k.htm', 'reportDate': '2026-07-29',
                 'primaryDocDescription': '8-K'})
    rows.append({'form': '10-Q', 'filingDate': '2026-10-28',
                 'accessionNumber': '0000950170-26-900001',
                 'primaryDocument': 'msft-20260930.htm', 'reportDate': '2026-09-30',
                 'primaryDocDescription': '10-Q filed after a 2026-09-18 cutoff'})
    rows.sort(key=lambda r: r['filingDate'], reverse=True)
    return rows


def company_facts(filings):
    by_period = {}
    for row in filings:
        by_period[row['reportDate']] = row

    def entry(start, end, value, form, accession, fiscal_year, fiscal_period, filed):
        payload = {'end': end.isoformat(), 'val': round(value), 'accn': accession,
                   'fy': fiscal_year, 'fp': fiscal_period, 'form': form, 'filed': filed}
        if start is not None:
            payload['start'] = start.isoformat()
        return payload

    facts = {'us-gaap': {}, 'dei': {}}
    for tag, unit, ratio in TAGS:
        observations = []
        for fiscal_year, revenue in sorted(ANNUAL_REVENUE.items()):
            start, end = fy_bounds(fiscal_year)
            annual = by_period.get(end.isoformat())
            if annual:
                observations.append(entry(start, end, revenue * ratio, '10-K',
                                          annual['accessionNumber'], fiscal_year, 'FY',
                                          annual['filingDate']))
            for quarter in (1, 2, 3):
                qs, qe = quarter_bounds(fiscal_year, quarter)
                row = by_period.get(qe.isoformat())
                if not row:
                    continue
                observations.append(entry(qs, qe, revenue * ratio * QUARTER_SHARE[quarter - 1],
                                          '10-Q', row['accessionNumber'], fiscal_year,
                                          f'Q{quarter}', row['filingDate']))
                observations.append(entry(start, qe,
                                          revenue * ratio * sum(QUARTER_SHARE[:quarter]),
                                          '10-Q', row['accessionNumber'], fiscal_year,
                                          f'Q{quarter}', row['filingDate']))
        facts['us-gaap'][tag] = {'label': tag, 'description': 'fixture',
                                 'units': {unit: observations}}

    for tag, unit, ratio in INSTANTS:
        observations = []
        for fiscal_year, revenue in sorted(ANNUAL_REVENUE.items()):
            _start, end = fy_bounds(fiscal_year)
            row = by_period.get(end.isoformat())
            if row:
                observations.append(entry(None, end, revenue * ratio, '10-K',
                                          row['accessionNumber'], fiscal_year, 'FY',
                                          row['filingDate']))
        facts['us-gaap'][tag] = {'label': tag, 'description': 'fixture',
                                 'units': {unit: observations}}

    # Annual diluted share counts, so the per-share and dilution metrics have a
    # fiscal-year series to compare across.
    for tag, unit, base, step in SHARE_TAGS:
        observations = []
        for offset, fiscal_year in enumerate(sorted(ANNUAL_REVENUE)):
            start, end = fy_bounds(fiscal_year)
            row = by_period.get(end.isoformat())
            if row:
                observations.append(entry(start, end, base + step * offset, '10-K',
                                          row['accessionNumber'], fiscal_year, 'FY',
                                          row['filingDate']))
        facts['us-gaap'][tag] = {'label': tag, 'description': 'fixture',
                                 'units': {unit: observations}}

    # One restatement: the FY2025 10-K revises the FY2024 revenue it reports as a
    # comparative. The revision is filed a year later, which is what makes it a
    # restatement rather than two versions of the same filing.
    revenue_tag = facts['us-gaap']['RevenueFromContractWithCustomerExcludingAssessedTax']['units']['USD']
    start, end = fy_bounds(2024)
    fy2025 = by_period.get(fy_bounds(2025)[1].isoformat())
    revenue_tag.append(entry(start, end, ANNUAL_REVENUE[2024] * 0.985, '10-K',
                             fy2025['accessionNumber'], 2025, 'FY', fy2025['filingDate']))

    # One post-cutoff fact that must never appear in a 2026-09-18 pack.
    revenue_tag.append(entry(date(2026, 7, 1), date(2026, 9, 30), 90_000_000_000, '10-Q',
                             '0000950170-26-900001', 2027, 'Q1', '2026-10-28'))

    facts['dei']['EntityCommonStockSharesOutstanding'] = {
        'label': 'Shares outstanding', 'units': {'shares': [
            entry(None, date(2026, 6, 30), 7_420_000_000, '10-K',
                  '0000950170-26-000126', 2026, 'FY', '2026-07-30')]}}
    return {'cik': CIK, 'entityName': NAME, 'facts': facts}


def main() -> None:
    write('https://www.sec.gov/files/company_tickers.json',
          {'0': {'cik_str': CIK, 'ticker': TICKER, 'title': NAME},
           '1': {'cik_str': 1819994, 'ticker': 'RKLB', 'title': 'Rocket Lab Corp'}})

    filings = filings_rows()
    write(f'https://data.sec.gov/submissions/CIK{CIK:010d}.json',
          {'cik': str(CIK), 'name': NAME, 'tickers': [TICKER], 'exchanges': ['Nasdaq'],
           'filings': {'recent': {key: [row.get(key) for row in filings] for key in
                                  ('form', 'filingDate', 'accessionNumber', 'primaryDocument',
                                   'reportDate', 'primaryDocDescription')}}})

    write(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK:010d}.json',
          company_facts(filings))

    write('https://www.sec.gov/files/company_tickers_exchange.json',
          {'fields': ['cik', 'name', 'ticker', 'exchange'],
           'data': [
               [CIK, NAME, TICKER, 'Nasdaq'],
               [1819994, 'Rocket Lab Corp', 'RKLB', 'Nasdaq'],
               [1067983, 'BERKSHIRE HATHAWAY INC', 'BRK-B', 'NYSE'],
               [1000045, 'NICHOLAS FINANCIAL INC', 'NICK', 'Nasdaq'],
               [1820302, 'Ajax Capital Acquisition Corp', 'AJAX', 'NYSE'],
               [1820302, 'Ajax Capital Acquisition Corp', 'AJAX-W', 'NYSE'],
               [1084765, 'SPDR S&P 500 ETF Trust', 'SPY', 'NYSE American'],
               [1090727, 'Some Company', 'SOMEC', 'OTC'],
           ]})

    print(f'wrote {len(list(OUT.glob("*")))} SEC fixtures -> {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
