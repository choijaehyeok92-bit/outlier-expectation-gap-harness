#!/usr/bin/env python3
"""Generate offline OpenDART fixtures.

These are **synthesized from the published OpenDART response specification**,
not captured from the live API: this repository was built in an environment
whose network policy blocks `opendart.fss.or.kr`, and with no API key. The
response *shapes* — envelope, field names, comma-formatted amounts, the 013
empty status — follow the spec; the *numbers* are illustrative and must never
be read as disclosures by these companies.

Refresh them for real with `RecordingTransport` once a key and egress exist:

    from data_adapters.testing import RecordingTransport
    provider = DartProvider(transport=RecordingTransport('data_adapters/fixtures/dart'))

    python scripts/build_dart_fixtures.py
"""
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data_adapters.testing import fixture_key  # noqa: E402

OUT = ROOT / 'data_adapters' / 'fixtures' / 'dart'
BASE = 'https://opendart.fss.or.kr/api'

# corp_code values are placeholders except Samsung Electronics'. A fixture that
# claimed to know every real corp_code would be asserting something it cannot.
COMPANIES = [
    {'corp_code': '00126380', 'corp_name': '삼성전자', 'stock_code': '005930',
     'corp_cls': 'Y', 'acc_mt': '12', 'induty_code': '264', 'full': False},
    {'corp_code': '01515323', 'corp_name': 'HD현대일렉트릭', 'stock_code': '267260',
     'corp_cls': 'Y', 'acc_mt': '12', 'induty_code': '281', 'full': True},
    {'corp_code': '01351263', 'corp_name': '에코프로비엠', 'stock_code': '247540',
     'corp_cls': 'K', 'acc_mt': '12', 'induty_code': '204', 'full': False},
    {'corp_code': '01998877', 'corp_name': '엔에이치스팩29호', 'stock_code': '456780',
     'corp_cls': 'K', 'acc_mt': '12', 'induty_code': '649', 'full': False},
    {'corp_code': '01777333', 'corp_name': '코넥스테스트', 'stock_code': '900999',
     'corp_cls': 'N', 'acc_mt': '12', 'induty_code': '469', 'full': False},
    {'corp_code': '01222111', 'corp_name': '비상장연구소', 'stock_code': None,
     'corp_cls': 'E', 'acc_mt': '12', 'induty_code': '721', 'full': False},
]
FULL = next(c for c in COMPANIES if c['full'])

REPORTS = [(2023, '11011'), (2024, '11011'), (2025, '11011'),
           (2025, '11013'), (2025, '11012'), (2025, '11014'),
           (2026, '11013'), (2026, '11012')]
REPORT_NAMES = {'11011': '사업보고서', '11012': '반기보고서', '11013': '분기보고서', '11014': '분기보고서'}
PERIOD_LABEL = {'11011': '12', '11013': '03', '11012': '06', '11014': '09'}
FILING_MONTH = {'11011': '03-17', '11013': '05-15', '11012': '08-14', '11014': '11-14'}

# Illustrative KRW figures, in won, scaled so a year reads like a mid-cap.
ANNUAL = {2023: 2_200_000_000_000, 2024: 3_300_000_000_000, 2025: 4_900_000_000_000}
MARGIN = {2023: 0.09, 2024: 0.14, 2025: 0.19}


def write(url: str, payload) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    key = fixture_key(url)
    if isinstance(payload, bytes):
        (OUT / f'{key}.zip').write_bytes(payload)
        return
    (OUT / f'{key}.json').write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n',
                                     encoding='utf-8')


def money(value) -> str:
    return f'{int(round(value)):,}'


def corp_code_zip() -> bytes:
    rows = ''.join(
        f'<list><corp_code>{c["corp_code"]}</corp_code>'
        f'<corp_name>{c["corp_name"]}</corp_name>'
        f'<stock_code>{c["stock_code"] or ""}</stock_code>'
        f'<modify_date>20260901</modify_date></list>'
        for c in COMPANIES)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><result>{rows}</result>'.encode('utf-8')
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('CORPCODE.xml', xml)
    return buffer.getvalue()


def filing_rows(company: dict) -> list:
    rows = []
    for year, code in REPORTS:
        filing_year = year + 1 if code == '11011' else year
        rcept = f'{filing_year}{FILING_MONTH[code].replace("-", "")}00{len(rows):04d}'
        rows.append({
            'corp_code': company['corp_code'], 'corp_name': company['corp_name'],
            'stock_code': company['stock_code'] or '', 'corp_cls': company['corp_cls'],
            'report_nm': f'{REPORT_NAMES[code]} ({year}.{PERIOD_LABEL[code]})',
            'rcept_no': rcept, 'flr_nm': company['corp_name'],
            'rcept_dt': f'{filing_year}{FILING_MONTH[code].replace("-", "")}', 'rm': ''})
    # One amendment and one post-cutoff filing, so the tests have both to find.
    rows.append({'corp_code': company['corp_code'], 'corp_name': company['corp_name'],
                 'stock_code': company['stock_code'] or '', 'corp_cls': company['corp_cls'],
                 'report_nm': '[기재정정]분기보고서 (2025.03)', 'rcept_no': '20250620009999',
                 'flr_nm': company['corp_name'], 'rcept_dt': '20250620', 'rm': '정정'})
    rows.append({'corp_code': company['corp_code'], 'corp_name': company['corp_name'],
                 'stock_code': company['stock_code'] or '', 'corp_cls': company['corp_cls'],
                 'report_nm': '분기보고서 (2026.09)', 'rcept_no': '20261114000001',
                 'flr_nm': company['corp_name'], 'rcept_dt': '20261114', 'rm': ''})
    rows.sort(key=lambda r: r['rcept_dt'], reverse=True)
    return rows


def statement_rows(year: int, code: str, rcept_no: str, basis: str) -> list:
    """BS / IS / CF rows shaped like fnlttSinglAcntAll, for one report."""
    annual = ANNUAL.get(year, ANNUAL[2025])
    share = {'11011': 1.0, '11013': 0.22, '11012': 0.26, '11014': 0.27}[code]
    cumulative = {'11011': 1.0, '11013': 0.22, '11012': 0.48, '11014': 0.75}[code]
    factor = 1.0 if basis == 'CFS' else 0.82        # 별도 is smaller; never mixed with 연결
    revenue = annual * share * factor
    revenue_ytd = annual * cumulative * factor
    margin = MARGIN.get(year, 0.19)
    period_name = f'제 {year - 1946} 기' + ('' if code == '11011' else f' {PERIOD_LABEL[code]}월')
    interim = code != '11011'

    def flow(sj, account_id, name, value, ytd_value, cumulative_only=False):
        row = {'rcept_no': rcept_no, 'reprt_code': code, 'bsns_year': str(year),
               'corp_code': FULL['corp_code'], 'sj_div': sj,
               'sj_nm': {'IS': '손익계산서', 'CF': '현금흐름표'}[sj],
               'account_id': account_id, 'account_nm': name, 'account_detail': '-',
               'thstrm_nm': period_name, 'thstrm_amount': '' if cumulative_only else money(value),
               'frmtrm_nm': '', 'frmtrm_amount': '', 'bfefrmtrm_nm': '', 'bfefrmtrm_amount': '',
               'ord': str(len(rows) + 1), 'currency': 'KRW'}
        if interim:
            row['thstrm_add_amount'] = money(ytd_value)
        return row

    def instant(account_id, name, value):
        return {'rcept_no': rcept_no, 'reprt_code': code, 'bsns_year': str(year),
                'corp_code': FULL['corp_code'], 'sj_div': 'BS', 'sj_nm': '재무상태표',
                'account_id': account_id, 'account_nm': name, 'account_detail': '-',
                'thstrm_nm': period_name + '말', 'thstrm_amount': money(value),
                'frmtrm_nm': '', 'frmtrm_amount': '', 'bfefrmtrm_nm': '', 'bfefrmtrm_amount': '',
                'ord': str(len(rows) + 1), 'currency': 'KRW'}

    rows: list = []
    rows += [
        flow('IS', 'ifrs-full_Revenue', '수익(매출액)', revenue, revenue_ytd),
        flow('IS', 'ifrs-full_CostOfSales', '매출원가', revenue * 0.72, revenue_ytd * 0.72),
        flow('IS', 'ifrs-full_GrossProfit', '매출총이익', revenue * 0.28, revenue_ytd * 0.28),
        # One line with no account_id, matched by label alone.
        flow('IS', '-표준계정코드 미사용-', '판매비와관리비', revenue * 0.09, revenue_ytd * 0.09),
        flow('IS', 'dart_OperatingIncomeLoss', '영업이익', revenue * margin, revenue_ytd * margin),
        flow('IS', 'ifrs-full_ProfitLoss', '당기순이익', revenue * margin * 0.76,
             revenue_ytd * margin * 0.76),
        # A line the map does not know: must land as metric=other, requires_review.
        flow('IS', '-표준계정코드 미사용-', '지분법적용투자주식처분이익', revenue * 0.004,
             revenue_ytd * 0.004),
    ]
    rows += [
        instant('ifrs-full_CashAndCashEquivalents', '현금및현금성자산', annual * 0.21 * factor),
        instant('ifrs-full_Inventories', '재고자산', annual * 0.17 * factor),
        instant('ifrs-full_TradeAndOtherCurrentReceivables', '매출채권', annual * 0.19 * factor),
        instant('ifrs-full_Assets', '자산총계', annual * 1.35 * factor),
        instant('ifrs-full_Liabilities', '부채총계', annual * 0.78 * factor),
        instant('ifrs-full_Equity', '자본총계', annual * 0.57 * factor),
        instant('dart_ShortTermBorrowings', '단기차입금', annual * 0.06 * factor),
        instant('ifrs-full_NoncurrentPortionOfNoncurrentBorrowings', '장기차입금',
                annual * 0.11 * factor),
    ]
    # Cash flow: cumulative only in interim reports, which is the usual Korean
    # practice and the trap this fixture exists to exercise.
    rows += [
        flow('CF', 'ifrs-full_CashFlowsFromUsedInOperatingActivities', '영업활동현금흐름',
             revenue * 0.13, revenue_ytd * 0.13, cumulative_only=interim),
        flow('CF', 'ifrs-full_CashFlowsFromUsedInInvestingActivities', '투자활동현금흐름',
             -revenue * 0.07, -revenue_ytd * 0.07, cumulative_only=interim),
        flow('CF', '-표준계정코드 미사용-', '유형자산의 취득', -revenue * 0.05,
             -revenue_ytd * 0.05, cumulative_only=interim),
        flow('CF', '-표준계정코드 미사용-', '기말현금및현금성자산', annual * 0.21 * factor,
             annual * 0.21 * factor, cumulative_only=interim),
    ]
    return rows


def share_rows(year: int, code: str) -> list:
    issued = 36_000_000 + (year - 2023) * 250_000
    return [{'rcept_no': '-', 'corp_code': FULL['corp_code'], 'corp_name': FULL['corp_name'],
             'se': '보통주', 'isu_stock_totqy': money(issued * 3), 'now_to_isu_stock_totqy': '-',
             'now_to_dcrs_stock_totqy': '-', 'redc_stock_totqy': '-',
             'istc_totqy': money(issued), 'tesstk_co': money(issued * 0.012),
             'distb_stock_co': money(issued * 0.988)}]


def main() -> None:
    write(f'{BASE}/corpCode.xml', corp_code_zip())

    for company in COMPANIES:
        write(f'{BASE}/company.json?corp_code={company["corp_code"]}',
              {'status': '000', 'message': '정상', **{k: v for k, v in company.items()
                                                     if k not in ('full',)},
               'stock_name': company['corp_name'], 'corp_name_eng': '', 'ceo_nm': '-',
               'est_dt': '19800101', 'stock_code': company['stock_code'] or ''})

    rows = filing_rows(FULL)
    for page in (1,):
        write(f'{BASE}/list.json?corp_code={FULL["corp_code"]}&bgn_de=19990101'
              f'&end_de=20260918&page_no={page}&page_count=100&sort=date&sort_mth=desc',
              {'status': '000', 'message': '정상', 'page_no': page, 'page_count': 100,
               'total_count': len(rows), 'total_page': 1, 'list': rows})

    by_report = {}
    for row in rows:
        match = [(y, c) for y, c in REPORTS
                 if row['report_nm'].startswith(REPORT_NAMES[c])
                 and f'({y}.{PERIOD_LABEL[c]})' in row['report_nm']]
        if match:
            by_report[match[0]] = row['rcept_no']

    for year, code in REPORTS:
        rcept = by_report.get((year, code), f'{year}0000000000')
        for basis in ('CFS', 'OFS'):
            write(f'{BASE}/fnlttSinglAcntAll.json?corp_code={FULL["corp_code"]}'
                  f'&bsns_year={year}&reprt_code={code}&fs_div={basis}',
                  {'status': '000', 'message': '정상',
                   'list': statement_rows(year, code, rcept, basis)})
        write(f'{BASE}/stockTotqySttus.json?corp_code={FULL["corp_code"]}'
              f'&bsns_year={year}&reprt_code={code}',
              {'status': '000', 'message': '정상', 'list': share_rows(year, code)})

    # One real capital event, and the rest genuinely empty.
    write(f'{BASE}/cvbdIsDecsn.json?corp_code={FULL["corp_code"]}'
          f'&bgn_de=19990101&end_de=20260918',
          {'status': '000', 'message': '정상',
           'list': [{'rcept_no': '20240412000321', 'corp_cls': 'Y',
                     'corp_code': FULL['corp_code'], 'corp_name': FULL['corp_name'],
                     'bd_tm': '3', 'bd_knd': '무기명식 이권부 무보증 사모 전환사채',
                     'bd_fta': '150,000,000,000', 'cv_prc': '62,500',
                     'cv_rqsd_bgd': '20250412', 'cv_rqsd_edd': '20290312',
                     'rcept_dt': '20240412'}]})

    count = len(list(OUT.glob('*')))
    print(f'wrote {count} DART fixtures -> {OUT.relative_to(ROOT)}')
    print(f'  full company: {FULL["corp_name"]} ({FULL["stock_code"]}), '
          f'{len(REPORTS)} periodic reports x CFS/OFS')


if __name__ == '__main__':
    main()
