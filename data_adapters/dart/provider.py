"""OpenDART regulatory provider.

Implements the same `RegulatoryDataProvider` interface as the SEC adapter, so
the harness sees a Korean filing and a US one in the same shape. What it does
not implement is any price method: a share price is not a regulatory
disclosure, and `MarketDataProvider` is where that lives.

Built from the published OpenDART specification in an environment with no
network access to `opendart.fss.or.kr` and no API key, so **the live endpoints
have never been exercised**. Everything that could drift — endpoint paths,
status codes, the names of the amount columns — is declared in
`config/dart.json` rather than written into this file, so a mismatch with the
real API is a config fix.

Status `013` ("조회된 데이터가 없습니다") is a normal empty answer, not a
failure. Treating it as an error would turn "this company filed no convertible
bonds" into a broken ingestion.
"""
import json
import re
from pathlib import Path
from typing import Optional

from ..base import AdapterError, RegulatoryDataProvider
from ..http import HttpClient, TransportError
from ..pack import FinancialPackBuilder, document_name
from ..types import Filing, FinancialFact, IngestionResult, Issuer, Security
from .accounts import AccountResolver
from .corpcode import CorpCodeCache
from .periods import PeriodResolver

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'config' / 'dart.json'
AMENDMENT = re.compile(r'\[(기재정정|첨부정정|첨부추가|변경등록|연장결정)\]')
PERIODIC_FORM = re.compile(r'(사업보고서|반기보고서|분기보고서)')
DATE8 = re.compile(r'^\d{8}$')


def load_config(path=None) -> dict:
    return json.loads(Path(path or CONFIG_PATH).read_text(encoding='utf-8'))


def _iso(value) -> Optional[str]:
    text = str(value or '').strip()
    if DATE8.match(text):
        return f'{text[:4]}-{text[4:6]}-{text[6:]}'
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
        return text
    return None


def parse_amount(value) -> Optional[float]:
    """`"1,234,567"` to a number. Blank, `-` and `–` mean not disclosed, not zero."""
    if value is None:
        return None
    text = str(value).strip().replace(',', '').replace('−', '-')
    if text in ('', '-', '–', '—', 'N/A'):
        return None
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1]
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


class DartProvider(RegulatoryDataProvider):
    jurisdiction = 'KR'
    regulator = 'DART'

    def __init__(self, api_key: Optional[str] = None, config: Optional[dict] = None,
                 transport=None, corp_codes: Optional[CorpCodeCache] = None,
                 resolver: Optional[AccountResolver] = None, user_agent: str = 'outlier-harness/1.0',
                 client: Optional[HttpClient] = None):
        import os
        self.config = config or load_config()
        self.api_key = api_key or os.environ.get(self.config.get('api_key_env', 'OPENDART_API_KEY'))
        self.client = client or HttpClient(
            user_agent, transport=transport,
            spacing_seconds=float(self.config.get('request_spacing_seconds', 0.12)))
        self.corp_codes = corp_codes if corp_codes is not None else CorpCodeCache()
        self.accounts = resolver or AccountResolver()
        self.periods = PeriodResolver(self.config)
        self._company_cache: dict = {}

    # ------------------------------------------------------------------ plumbing
    def _url(self, endpoint_key: str) -> str:
        path = self.config['endpoints'].get(endpoint_key) or \
            (self.config['capital_event_endpoints'].get(endpoint_key) or {}).get('path')
        if not path:
            raise AdapterError(f'no endpoint declared for {endpoint_key!r} in config/dart.json')
        return f"{self.config['api_base'].rstrip('/')}/{path}"

    def _require_key(self) -> str:
        if not self.api_key:
            raise AdapterError(
                f"{self.config.get('api_key_env', 'OPENDART_API_KEY')} is not set; "
                'the OpenDART key is a backend secret and is never accepted from a client')
        return self.api_key

    def call(self, endpoint_key: str, **params) -> dict:
        """One API call. Returns {'rows': [...], 'empty': bool, 'status': code}."""
        payload = self.client.get_json(self._url(endpoint_key),
                                       {'crtfc_key': self._require_key(), **params})
        status = str(payload.get('status', '000'))
        meta = self.config['status_codes'].get(status, {'ok': False, 'meaning': 'unknown status'})
        if not meta.get('ok'):
            raise AdapterError(f"OpenDART {endpoint_key} -> status {status}: "
                               f"{meta.get('meaning')} ({payload.get('message')})")
        rows = payload.get('list') or []
        return {'rows': rows, 'empty': bool(meta.get('empty')) or not rows,
                'status': status, 'payload': payload}

    # ------------------------------------------------------------------- issuer
    def company_profile(self, corp_code: str) -> dict:
        if corp_code in self._company_cache:
            return self._company_cache[corp_code]
        payload = self.client.get_json(self._url('company_profile'),
                                       {'crtfc_key': self._require_key(), 'corp_code': corp_code})
        status = str(payload.get('status', '000'))
        meta = self.config['status_codes'].get(status, {'ok': False})
        if not meta.get('ok'):
            raise AdapterError(f'OpenDART company.json -> status {status}: {payload.get("message")}')
        self._company_cache[corp_code] = payload
        return payload

    def resolve_issuer(self, identifier: str) -> Issuer:
        entry = self.corp_codes.resolve(identifier)
        if entry is None:
            raise AdapterError(f'{identifier}: not in the corpCode cache; run '
                               '`harness.py universe sync --markets KR` first')
        profile = {}
        try:
            profile = self.company_profile(entry.corp_code)
        except (AdapterError, TransportError):
            # A profile lookup failure must not invent a fiscal calendar. The
            # default of December is recorded as an assumption, not a fact.
            profile = {}
        accounting_month = str(profile.get('acc_mt') or '').strip()
        corp_cls = str(profile.get('corp_cls') or '').strip() or None
        return Issuer(
            jurisdiction='KR', regulator='DART', regulator_issuer_id=entry.corp_code,
            legal_name=profile.get('corp_name') or entry.corp_name,
            industry=str(profile.get('induty_code') or '') or None,
            fiscal_year_end=f'{int(accounting_month):02d}-31' if accounting_month.isdigit() else None,
            extra={'stock_code': entry.stock_code,
                   'stock_name': profile.get('stock_name'),
                   'corp_cls': corp_cls,
                   'corp_name_eng': profile.get('corp_name_eng'),
                   'accounting_month': accounting_month or None,
                   'fiscal_year_end_assumed': not accounting_month.isdigit()})

    def fiscal_year_end_month(self, issuer: Issuer) -> int:
        month = (issuer.extra or {}).get('accounting_month')
        return int(month) if str(month or '').isdigit() else 12

    # ------------------------------------------------------------------ filings
    def _all_filings(self, issuer: Issuer, as_of_date: str, begin_date: str = '19990101',
                     page_count: int = 100, max_pages: int = 20, **kwargs) -> list:
        end = as_of_date.replace('-', '')
        rows, page = [], 1
        while page <= max_pages:
            result = self.call('filing_search', corp_code=issuer.regulator_issuer_id,
                               bgn_de=begin_date, end_de=end, page_no=page,
                               page_count=page_count, sort='date', sort_mth='desc')
            rows.extend(result['rows'])
            total_pages = int(result['payload'].get('total_page') or 1)
            if result['empty'] or page >= total_pages:
                break
            page += 1
        return [self._filing_from_row(issuer, row) for row in rows]

    def _filing_from_row(self, issuer: Issuer, row: dict) -> Filing:
        report_name = str(row.get('report_nm') or '').strip()
        form = PERIODIC_FORM.search(report_name)
        return Filing(
            issuer_key=issuer.issuer_key, regulator='DART',
            form_type=form.group(1) if form else AMENDMENT.sub('', report_name).strip() or 'report',
            filing_date=_iso(row.get('rcept_dt')) or '',
            accession=str(row.get('rcept_no') or '').strip(),
            title=report_name,
            period_end=None,
            reprt_code=None,
            is_amendment=bool(AMENDMENT.search(report_name)),
            document_url=self.client.build_url(self._url('raw_document'),
                                               {'rcept_no': row.get('rcept_no')}),
            extra={'report_nm': report_name, 'corp_cls': row.get('corp_cls'),
                   'filer': row.get('flr_nm'), 'remark': row.get('rm')})

    def fetch_raw_filing(self, filing: Filing) -> bytes:
        """The original submission. Treat the bytes as untrusted content."""
        return self.client.get(self._url('raw_document'),
                               {'crtfc_key': self._require_key(), 'rcept_no': filing.accession})

    # ------------------------------------------------------- structured financials
    def periodic_reports(self, issuer: Issuer, as_of_date: str, years: int = 4) -> list:
        """(bsns_year, reprt_code) pairs whose report could exist by the cutoff.

        A report is only a candidate once its period has ended; whether it was
        actually filed by the cutoff is decided by the API and by the filing
        list, not guessed here.
        """
        month = self.fiscal_year_end_month(issuer)
        cutoff_year = int(as_of_date[:4])
        candidates = []
        for year in range(cutoff_year, cutoff_year - years, -1):
            for code in self.config['periodic_report_order']:
                periods = self.periods.periods(year, code, month)
                if periods.period_end <= as_of_date:
                    candidates.append((year, code, periods))
        return candidates

    def statements_for(self, issuer: Issuer, bsns_year: int, reprt_code: str) -> tuple:
        """Rows plus the basis they came from. CFS first, OFS only as a fallback."""
        last_error = None
        for basis in self.config['consolidation']['preference']:
            try:
                result = self.call('financial_statements_all',
                                   corp_code=issuer.regulator_issuer_id,
                                   bsns_year=str(bsns_year), reprt_code=str(reprt_code),
                                   fs_div=basis)
            except (AdapterError, TransportError) as error:
                last_error = error
                continue
            if not result['empty']:
                return result['rows'], basis
        if last_error is not None:
            raise last_error
        return [], None

    def fetch_structured_financials(self, issuer: Issuer, as_of_date: str, years: int = 4,
                                    filings_by_accession: Optional[dict] = None,
                                    result: Optional[IngestionResult] = None, **kwargs) -> list:
        facts: list = []
        filings_by_accession = filings_by_accession or {}
        month = self.fiscal_year_end_month(issuer)
        for bsns_year, reprt_code, periods in self.periodic_reports(issuer, as_of_date, years):
            try:
                rows, basis = self.statements_for(issuer, bsns_year, reprt_code)
            except (AdapterError, TransportError) as error:
                if result is not None:
                    result.warn('medium', f'{bsns_year}/{reprt_code}: statements unavailable ({error})')
                continue
            if not rows:
                continue
            facts.extend(self._facts_from_rows(issuer, rows, periods, basis, reprt_code,
                                               as_of_date, filings_by_accession, result))
        return facts

    def _facts_from_rows(self, issuer: Issuer, rows: list, periods, basis: Optional[str],
                         reprt_code: str, as_of_date: str, filings_by_accession: dict,
                         result: Optional[IngestionResult]) -> list:
        report_meta = self.config['report_codes'][str(reprt_code)]
        facts = []
        for row in rows:
            sj_div = str(row.get('sj_div') or '').upper()
            statement_meta = self.periods.statement_for(sj_div)
            statement = statement_meta['statement']
            resolution = self.accounts.resolve(
                (row.get('account_id') or '').strip() or None,
                row.get('account_nm'), statement, row.get('account_detail'))

            accession = str(row.get('rcept_no') or '').strip()
            filing = filings_by_accession.get(accession)
            filing_date = filing.filing_date if filing else None
            if filing_date and filing_date > as_of_date:
                continue                      # belt and braces: the cutoff wins everywhere
            source_document = (document_name(filing) if filing
                               else f'{report_meta["name"]}_{periods.period_end}_{accession or "unknown"}.xml')

            planned = self.periods.plan_row(
                sj_div, periods,
                parse_amount(row.get(self.config['amount_columns']['current_period'])),
                parse_amount(row.get(self.config['amount_columns']['current_cumulative'])))
            for plan in planned:
                review = resolution.requires_review or plan['requires_review']
                reasons = [r for r in (resolution.review_reason, plan['review_reason']) if r]
                facts.append(FinancialFact(
                    issuer_key=issuer.issuer_key,
                    metric=resolution.metric,
                    metric_detail=resolution.metric_detail,
                    reported_label=str(row.get('account_nm') or '').strip() or None,
                    value=plan['amount'],
                    period_kind=plan['period_kind'],
                    statement=statement,
                    consolidation_basis=basis,
                    unit_kind='currency',
                    currency=str(row.get('currency') or 'KRW').strip() or 'KRW',
                    scale_multiplier=1.0,
                    period_start=plan['period_start'],
                    period_end=plan['period_end'],
                    fiscal_year=periods.fiscal_year,
                    fiscal_quarter=plan['fiscal_quarter'],
                    filing_date=filing_date,
                    source_document=source_document,
                    source_section=str(row.get('sj_nm') or '').strip() or None,
                    source_locator=f"{sj_div}/{row.get('account_id') or row.get('account_nm')}"
                                   f"/{plan['column']}",
                    gaap_status='gaap',
                    confidence=resolution.confidence,
                    requires_review=review,
                    review_reason='; '.join(reasons) or None,
                    mapping_stage=resolution.stage,
                    extra={'reprt_code': str(reprt_code), 'rcept_no': accession}))
        if result is not None and facts:
            unmapped = sum(1 for f in facts if f.mapping_stage == 'unmapped')
            if unmapped:
                result.warn('low', f'{report_meta["name"]} {periods.fiscal_year}: {unmapped} line(s) '
                                   'had no account mapping and are recorded as metric=other '
                                   'with requires_review')
        return facts

    # --------------------------------------------------------------- share data
    def fetch_share_data(self, issuer: Issuer, as_of_date: str, years: int = 4,
                         result: Optional[IngestionResult] = None, **kwargs) -> dict:
        """Share counts and capital-structure events, as facts plus dated events.

        The revised dilution Hard Veto is untouched by this. These are
        observables for the evidence layer; whether they amount to a veto is
        still the configured owner's call.
        """
        facts, events = [], []
        month = self.fiscal_year_end_month(issuer)
        for bsns_year, reprt_code, periods in self.periodic_reports(issuer, as_of_date, years):
            try:
                rows = self.call('share_total', corp_code=issuer.regulator_issuer_id,
                                 bsns_year=str(bsns_year), reprt_code=str(reprt_code))['rows']
            except (AdapterError, TransportError) as error:
                if result is not None:
                    result.warn('low', f'{bsns_year}/{reprt_code}: share totals unavailable ({error})')
                continue
            for row in rows:
                facts.extend(self._share_facts(issuer, row, periods, reprt_code, as_of_date))

        for key, meta in (self.config.get('capital_event_endpoints') or {}).items():
            try:
                rows = self.call(key, corp_code=issuer.regulator_issuer_id,
                                 bgn_de='19990101', end_de=as_of_date.replace('-', ''))['rows']
            except (AdapterError, TransportError) as error:
                if result is not None:
                    result.warn('low', f'{meta["label"]}: unavailable ({error})')
                continue
            for row in rows:
                filed = _iso(row.get('rcept_dt') or row.get('rcept_no', '')[:8])
                if filed and filed > as_of_date:
                    continue
                events.append({'kind': meta['dilution_kind'], 'label': meta['label'],
                               'endpoint': key, 'filing_date': filed,
                               'rcept_no': row.get('rcept_no'), 'detail': row})
        return {'facts': facts, 'events': events}

    def _share_facts(self, issuer: Issuer, row: dict, periods, reprt_code, as_of_date) -> list:
        mapping = self.config['share_metrics']
        columns = (('istc_totqy', mapping['issued_total'], '발행주식총수'),
                   ('tesstk_co', mapping['treasury'], '자기주식수'),
                   ('distb_stock_co', mapping['distributed'], '유통주식수'))
        share_class = str(row.get('se') or '').strip() or None
        facts = []
        for column, metric, label in columns:
            value = parse_amount(row.get(column))
            if value is None:
                continue
            facts.append(FinancialFact(
                issuer_key=issuer.issuer_key, metric=metric,
                metric_detail=None if metric != 'other' else f'{label}({share_class or "합계"})',
                reported_label=f'{label} {share_class or ""}'.strip(),
                value=value, period_kind='instant', statement='shares',
                consolidation_basis=None, unit_kind='shares', currency=None,
                scale_multiplier=1.0, period_start=None, period_end=periods.period_end,
                fiscal_year=periods.fiscal_year, fiscal_quarter=periods.quarter,
                filing_date=None,
                source_document=f'{self.config["report_codes"][str(reprt_code)]["name"]}'
                                f'_{periods.period_end}_주식총수.xml',
                source_section='주식의 총수 현황',
                source_locator=f'share_total/{column}',
                gaap_status='not_applicable', confidence=0.95,
                requires_review=False, mapping_stage='share_total',
                extra={'share_class': share_class, 'reprt_code': str(reprt_code)}))
        return facts

    # ---------------------------------------------------------------- universe
    def list_universe(self, enrich_limit: int = 0, **kwargs) -> list:
        """Listed Korean securities from the corpCode cache.

        The cache says which corporations are listed; it does not say on which
        market. `corp_cls` does, but it costs one company.json call per issuer,
        so enrichment is bounded by `enrich_limit` and everything unenriched is
        marked `requires_review` rather than assigned a market by guesswork.
        """
        rules = [(re.compile(rule['pattern']), rule) for rule in
                 (self.config['universe'].get('name_exclusions') or [])]
        allowed = set(self.config['universe']['exchanges'])
        excluded_markets = set(self.config['universe'].get('excluded_exchanges') or [])
        corp_cls_map = self.config['corp_cls_map']
        securities, enriched = [], 0

        for entry in sorted(self.corp_codes.listed, key=lambda e: e.stock_code or ''):
            security_type, excluded_reason = 'common', None
            for pattern, rule in rules:
                if pattern.search(entry.corp_name):
                    security_type = rule['security_type']
                    excluded_reason = rule['reason']
                    break

            exchange, requires_review = 'KRX', True
            if enriched < enrich_limit:
                try:
                    profile = self.company_profile(entry.corp_code)
                    enriched += 1
                    mapped = corp_cls_map.get(str(profile.get('corp_cls') or '').strip())
                    if mapped:
                        exchange, requires_review = mapped['exchange'], False
                except (AdapterError, TransportError):
                    pass

            if exchange in excluded_markets:
                excluded_reason = excluded_reason or f'{exchange} is excluded by config'
            elif not requires_review and exchange not in allowed:
                excluded_reason = excluded_reason or f'{exchange} is not a configured exchange'

            securities.append(Security(
                issuer_key=f'DART:{entry.corp_code}', ticker=entry.stock_code,
                exchange=exchange, currency='KRW', security_type=security_type,
                active=True, name=entry.corp_name, excluded_reason=excluded_reason,
                requires_review=requires_review))
        return securities

    # ------------------------------------------------------------------- pack
    def build_financial_pack(self, identifier: str, as_of_date: str, years: int = 4,
                             **kwargs) -> dict:
        issuer = self.resolve_issuer(identifier)
        result = IngestionResult(issuer=issuer)
        listing = self.list_filings(issuer, as_of_date)
        result.filings = listing['filings']
        result.excluded_post_cutoff = listing['excluded_post_cutoff']
        by_accession = {f.accession: f for f in listing['filings']}

        facts = self.fetch_structured_financials(
            issuer, as_of_date, years=years, filings_by_accession=by_accession, result=result)
        shares = self.fetch_share_data(issuer, as_of_date, years=years, result=result)
        facts.extend(shares['facts'])
        result.facts = facts

        # Only the filings a fact actually cites, plus the periodic reports, are
        # declared as documents: a pack should not claim to hold a document it
        # pulled nothing out of.
        cited = {f.source_document for f in facts}
        documents = [f for f in listing['filings'] if document_name(f) in cited]
        synthetic = sorted(cited - {document_name(f) for f in documents})

        builder = FinancialPackBuilder(
            ticker=(issuer.extra or {}).get('stock_code') or identifier,
            as_of_date=as_of_date, issuer=issuer, reporting_currency='KRW',
            consolidation_preference=tuple(self.config['consolidation']['preference']),
            document_type_map=self.config['document_type_map'])
        pack = builder.build(documents + self._synthetic_filings(issuer, synthetic),
                             facts, extra_warnings=result.warnings)
        pack['ingestion'] = {
            'regulator': 'DART', 'jurisdiction': 'KR',
            'account_map_version': self.accounts.version,
            'consolidation_basis': pack.get('consolidation_basis'),
            'excluded_post_cutoff': len(result.excluded_post_cutoff),
            'capital_events': shares['events'],
            'fiscal_year_end_month': self.fiscal_year_end_month(issuer),
            'fiscal_year_end_assumed': bool((issuer.extra or {}).get('fiscal_year_end_assumed')),
            'live_api_verified': False,
        }
        return pack

    @staticmethod
    def _synthetic_filings(issuer: Issuer, names) -> list:
        """Documents a fact cited that the filing list did not contain.

        The share-total endpoint and the statement endpoint both answer per
        report rather than per document, so a fact can legitimately cite a
        report the filing search did not return. Declaring it keeps the pack's
        documents[] complete instead of dropping the fact.
        """
        rows = []
        for name in names:
            stem = name.rsplit('.', 1)[0]
            parts = stem.split('_')
            rows.append(Filing(
                issuer_key=issuer.issuer_key, regulator='DART',
                form_type=parts[0], filing_date=parts[1] if len(parts) > 1 else '',
                accession='_'.join(parts[2:]) or stem, title=stem,
                extra={'synthetic': True}))
        return rows
