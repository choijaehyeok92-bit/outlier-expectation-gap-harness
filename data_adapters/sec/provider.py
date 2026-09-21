"""SEC EDGAR regulatory provider.

Document acquisition is the harness's existing `harness_core/fetch.py`: it
already resolves a ticker to a CIK, reads the submissions index, respects the
as-of cutoff and carries the contact User-Agent that SEC fair access requires.
Rewriting that would mean two things to keep correct instead of one, so this
provider wraps it and adds what it did not do — XBRL company facts turned into
normalized facts.

Same interface as `DartProvider`, and the same silence about prices.
"""
import json
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness_core import fetch as edgar_fetch                       # noqa: E402
from ..base import AdapterError, RegulatoryDataProvider             # noqa: E402
from ..http import HttpClient, TransportError                       # noqa: E402
from ..pack import FinancialPackBuilder, document_name              # noqa: E402
from ..types import Filing, FinancialFact, IngestionResult, Issuer, Security  # noqa: E402
from .xbrl import CompanyFactsReader, period_kind_for               # noqa: E402

CONFIG_PATH = ROOT / 'config' / 'sec.json'
INTAKE_PATH = ROOT / 'config' / 'intake.json'


def load_config(path=None) -> dict:
    return json.loads(Path(path or CONFIG_PATH).read_text(encoding='utf-8'))


class SecEdgarProvider(RegulatoryDataProvider):
    jurisdiction = 'US'
    regulator = 'SEC'

    def __init__(self, user_agent: Optional[str] = None, config: Optional[dict] = None,
                 transport=None, intake_policy: Optional[dict] = None,
                 client: Optional[HttpClient] = None):
        import os
        self.config = config or load_config()
        self.user_agent = user_agent or os.environ.get(
            self.config.get('user_agent_env', 'SEC_USER_AGENT'))
        self.client = client or HttpClient(
            self.user_agent or 'outlier-harness (contact not configured)', transport=transport,
            spacing_seconds=float(self.config.get('request_spacing_seconds', 0.12)))
        self.intake_policy = intake_policy or json.loads(
            INTAKE_PATH.read_text(encoding='utf-8'))
        self.facts_reader = CompanyFactsReader(self.config)
        self._submissions: dict = {}

    # ------------------------------------------------------------------ plumbing
    def _require_user_agent(self) -> str:
        if not self.user_agent:
            raise AdapterError(
                f"{self.config.get('user_agent_env', 'SEC_USER_AGENT')} is not set; "
                'SEC fair access requires a contact in the User-Agent and the harness '
                'never invents one')
        return self.user_agent

    def _opener(self):
        """Adapt this client's transport to the signature harness fetch expects."""
        def opener(url, user_agent, timeout=30):
            return self.client.get(url, headers={'User-Agent': user_agent})
        return opener

    # ------------------------------------------------------------------- issuer
    def resolve_issuer(self, identifier: str) -> Issuer:
        user_agent = self._require_user_agent()
        text = str(identifier).strip()
        try:
            if text.isdigit():
                cik, title = int(text), None
            else:
                cik, title = edgar_fetch.resolve_cik(text, user_agent, self._opener())
        except edgar_fetch.FetchError as error:
            raise AdapterError(str(error)) from error
        try:
            rows, name = edgar_fetch.recent_filings(cik, user_agent, self._opener())
            self._submissions[cik] = rows
        except edgar_fetch.FetchError as error:
            raise AdapterError(str(error)) from error
        return Issuer(jurisdiction='US', regulator='SEC', regulator_issuer_id=f'{cik:010d}',
                      legal_name=name or title or text.upper(),
                      extra={'cik': cik, 'ticker': text.upper() if not text.isdigit() else None})

    @staticmethod
    def _cik(issuer: Issuer) -> int:
        return int((issuer.extra or {}).get('cik') or issuer.regulator_issuer_id)

    # ------------------------------------------------------------------ filings
    def _all_filings(self, issuer: Issuer, as_of_date: str, **kwargs) -> list:
        cik = self._cik(issuer)
        rows = self._submissions.get(cik)
        if rows is None:
            rows, _name = edgar_fetch.recent_filings(cik, self._require_user_agent(), self._opener())
            self._submissions[cik] = rows
        return [Filing(
            issuer_key=issuer.issuer_key, regulator='SEC',
            form_type=str(row.get('form') or ''), filing_date=str(row.get('filingDate') or ''),
            accession=str(row.get('accessionNumber') or ''),
            title=row.get('primaryDocDescription'), period_end=row.get('reportDate'),
            is_amendment=str(row.get('form') or '').endswith('/A'),
            document_url=(edgar_fetch.document_url(cik, row) if row.get('primaryDocument') else None),
            extra={'primary_document': row.get('primaryDocument')}) for row in rows]

    def plan_downloads(self, issuer: Issuer, as_of_date: str) -> dict:
        """Which filings the Stage 0 checklist wants. Reuses the harness's planner."""
        cik = self._cik(issuer)
        rows = self._submissions.get(cik) or []
        return edgar_fetch.plan(rows, self.intake_policy, as_of_date)

    def fetch_raw_filing(self, filing: Filing) -> bytes:
        if not filing.document_url:
            raise AdapterError(f'{filing.accession}: no primary document url')
        return self.client.get(filing.document_url,
                               headers={'User-Agent': self._require_user_agent()})

    # ------------------------------------------------------- structured financials
    def company_facts(self, issuer: Issuer) -> dict:
        url = self.config['api_base'].rstrip('/') + \
            self.config['endpoints']['company_facts'].format(cik=self._cik(issuer))
        try:
            return self.client.get_json(url, headers={'User-Agent': self._require_user_agent()})
        except TransportError as error:
            raise AdapterError(str(error)) from error

    def fetch_structured_financials(self, issuer: Issuer, as_of_date: str,
                                    filings_by_accession: Optional[dict] = None,
                                    result: Optional[IngestionResult] = None, **kwargs) -> list:
        payload = self.company_facts(issuer)
        reader = self.facts_reader
        entries = reader.deduplicate(reader.entries(payload, as_of_date))
        statements = self.config['metric_statements']
        filings_by_accession = filings_by_accession or {}
        facts, restated = [], 0

        for entry, superseded in entries:
            mapped = reader.metric_for(entry.taxonomy, entry.tag)
            metric, detail, review, reason = mapped
            kind, kind_review, kind_reason = period_kind_for(
                entry.start, entry.end, self.config['period_spans'])
            filing = filings_by_accession.get(entry.accession)
            source_document = (document_name(filing, 'htm') if filing else
                               f'{entry.form or "filing"}_{entry.filed}_{entry.accession or "unknown"}.htm')
            reasons = [r for r in (reason, kind_reason) if r]
            if superseded:
                restated += 1
                reasons.append('superseded values from earlier filings: ' +
                               ', '.join(f"{row['value']:g} ({row['filed']})" for row in superseded[:3]))
            quarter = reader.fiscal_quarter(entry)
            facts.append(FinancialFact(
                issuer_key=issuer.issuer_key, metric=metric, metric_detail=detail,
                reported_label=entry.tag, value=entry.value, period_kind=kind,
                statement=statements.get(metric, 'other'),
                consolidation_basis=self.config.get('consolidation_basis', 'CFS'),
                unit_kind=reader.unit_kind(entry.unit),
                currency=entry.unit if entry.unit.startswith('USD') and entry.unit == 'USD' else None,
                scale_multiplier=1.0, period_start=entry.start, period_end=entry.end,
                fiscal_year=entry.fiscal_year,
                fiscal_quarter=quarter if kind in ('quarter', 'ytd', 'instant') else None,
                filing_date=entry.filed, source_document=source_document,
                source_section=entry.form, source_locator=f'{entry.taxonomy}:{entry.tag}/{entry.unit}',
                gaap_status='gaap' if entry.taxonomy == 'us-gaap' else 'not_applicable',
                is_restated=bool(superseded), confidence=0.97 if not review else 0.85,
                requires_review=bool(review or kind_review),
                review_reason='; '.join(reasons) or None,
                mapping_stage='tag_map' if not review else 'review_required_tags',
                extra={'accession': entry.accession, 'form': entry.form,
                       'superseded': superseded}))
        if result is not None and restated:
            result.warn('low', f'{restated} fact(s) were restated by a later filing at or before the '
                               'cutoff; the superseded values are preserved on each fact.')
        return facts

    # --------------------------------------------------------------- share data
    def fetch_share_data(self, issuer: Issuer, as_of_date: str,
                         result: Optional[IngestionResult] = None, **kwargs) -> dict:
        """Share counts come from the same company facts; there is no separate feed.

        The revised dilution Hard Veto is untouched: these are observables.
        """
        facts = [f for f in self.fetch_structured_financials(issuer, as_of_date, result=result)
                 if f.statement == 'shares']
        return {'facts': [], 'events': [], 'share_facts_in_structured': len(facts)}

    # ---------------------------------------------------------------- universe
    def list_universe(self, **kwargs) -> list:
        index = self.client.get_json(self.config['endpoints']['ticker_exchange_index'],
                                     headers={'User-Agent': self._require_user_agent()})
        fields = [str(f) for f in (index.get('fields') or [])]
        rows = index.get('data') or []
        universe = self.config['universe']
        aliases = universe.get('exchange_aliases') or {}
        allowed = set(universe['exchanges'])
        excluded_markets = set(universe.get('excluded_exchanges') or [])
        ticker_rules = [(re.compile(r['pattern']), r) for r in universe.get('ticker_exclusions') or []]
        name_rules = [(re.compile(r['pattern'], re.I), r) for r in universe.get('name_exclusions') or []]

        securities = []
        for row in rows:
            record = dict(zip(fields, row))
            ticker = str(record.get('ticker') or '').strip().upper()
            if not ticker:
                continue
            name = str(record.get('name') or '').strip()
            exchange = str(record.get('exchange') or '').strip()
            exchange = aliases.get(exchange, exchange)

            security_type, excluded_reason, requires_review = 'common', None, False
            for pattern, rule in ticker_rules:
                if pattern.search(ticker):
                    security_type, excluded_reason = rule['security_type'], rule['reason']
                    break
            if excluded_reason is None:
                for pattern, rule in name_rules:
                    if pattern.search(name):
                        security_type, excluded_reason = rule['security_type'], rule['reason']
                        break
            if exchange in excluded_markets or not exchange:
                excluded_reason = excluded_reason or f'{exchange or "no exchange"} is excluded by config'
            elif exchange not in allowed:
                excluded_reason = excluded_reason or f'{exchange} is not a configured exchange'
                requires_review = True

            securities.append(Security(
                issuer_key=f"SEC:{int(record.get('cik') or 0):010d}", ticker=ticker,
                exchange=exchange or 'UNKNOWN', currency='USD', security_type=security_type,
                active=True, name=name, excluded_reason=excluded_reason,
                requires_review=requires_review))
        return securities

    @staticmethod
    def _synthetic_filings(issuer: Issuer, facts, declared) -> list:
        """Filings a fact cited that the submissions index did not list."""
        rows, seen = [], set()
        for fact in facts:
            name = fact.source_document
            if name in declared or name in seen:
                continue
            seen.add(name)
            stem = name.rsplit('.', 1)[0]
            parts = stem.split('_')
            rows.append(Filing(
                issuer_key=issuer.issuer_key, regulator='SEC',
                form_type=parts[0], filing_date=parts[1] if len(parts) > 1 else '',
                accession='_'.join(parts[2:]) or stem, title=stem,
                extra={'synthetic': True}))
        return rows

    # ------------------------------------------------------------------- pack
    def build_financial_pack(self, identifier: str, as_of_date: str, **kwargs) -> dict:
        issuer = self.resolve_issuer(identifier)
        result = IngestionResult(issuer=issuer)
        listing = self.list_filings(issuer, as_of_date)
        result.filings = listing['filings']
        result.excluded_post_cutoff = listing['excluded_post_cutoff']
        by_accession = {f.accession: f for f in listing['filings']}

        facts = self.fetch_structured_financials(
            issuer, as_of_date, filings_by_accession=by_accession, result=result)
        result.facts = facts

        cited = {f.source_document for f in facts}
        documents = [f for f in listing['filings'] if document_name(f, 'htm') in cited]
        # A restated figure cites the filing that revised it, which may be older
        # than the submissions index window. Declaring it keeps the fact instead
        # of dropping it as an orphan.
        documents += self._synthetic_filings(issuer, facts,
                                             {document_name(f, 'htm') for f in documents})
        builder = FinancialPackBuilder(
            ticker=(issuer.extra or {}).get('ticker') or identifier.upper(),
            as_of_date=as_of_date, issuer=issuer, reporting_currency='USD',
            consolidation_preference=('CFS',), document_extension='htm',
            document_type_map=self.config['document_type_map'])
        pack = builder.build(documents, facts, extra_warnings=result.warnings)
        pack['ingestion'] = {
            'regulator': 'SEC', 'jurisdiction': 'US',
            'consolidation_basis': pack.get('consolidation_basis'),
            'excluded_post_cutoff': len(result.excluded_post_cutoff),
            'download_plan': self.plan_downloads(issuer, as_of_date),
            'restated_facts': sum(1 for f in facts if f.is_restated),
            'live_api_verified': False,
        }
        return pack
