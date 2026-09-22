"""Build a Stage 0 financial pack from adapter output.

The pack is the existing contract (`schemas/financial_pack.schema.json`), so
this module is where a US and a Korean filing stop looking different. It does
no economic work: it does not compute TTM, it does not normalise owner FCF, it
does not decide anything. It arranges disclosed facts into the shape Stage 0
already reads, and it refuses to emit a pack that would mislead.

Two refusals matter.

**Consolidation.** A pack carries one basis. CFS is preferred and OFS is the
fallback, exactly as the Korean policy says, but the choice is made once for
the whole pack and facts on the other basis are dropped with a warning. Mixing
them would produce a revenue series that switches between two different
economic entities partway through, and nothing downstream could see it.

**Sign convention.** `harness_core/intake.py` records costs and outflows as
positive magnitudes whatever sign the filing used, and its invariants reject a
pack that does otherwise. So the builder applies that convention and reports
how many values it flipped, rather than flipping them silently.
"""
import json
import re
from pathlib import Path
from typing import Iterable, Optional

from .base import ConsolidationMixError
from .types import Filing, FinancialFact, Issuer

ROOT = Path(__file__).resolve().parents[1]
PACK_SCHEMA = ROOT / 'schemas' / 'financial_pack.schema.json'
SCHEMA_VERSION = '1.0'

# Mirrors harness_core.intake.POSITIVE_COST_METRICS. Kept as a literal rather
# than imported so the adapters never reach into the harness runtime.
POSITIVE_COST_METRICS = {
    'capex', 'r_and_d', 's_and_m', 'g_and_a', 'sbc', 'd_and_a',
    'interest_expense', 'tax_expense', 'acquisitions', 'stock_repurchases', 'debt_repayment',
}
DOCUMENT_TYPES = ('10-K', '10-Q', '20-F', 'annual_report', 'earnings_release', 'proxy', 'other')
STATEMENTS = ('income', 'balance_sheet', 'cash_flow', 'shares', 'commitments', 'segment', 'other')
PACK_FACT_FIELDS = (
    'fact_id', 'metric', 'metric_detail', 'reported_label', 'statement', 'gaap_status',
    'value_reported', 'unit_kind', 'currency', 'scale_multiplier', 'period_start', 'period_end',
    'period_kind', 'fiscal_year', 'fiscal_quarter', 'segment', 'filing_date', 'source_document',
    'source_page', 'source_section', 'source_locator', 'source_quote', 'is_amended',
    'is_restated', 'confidence', 'requires_review', 'review_reason')


def load_pack_schema(path=None) -> dict:
    return json.loads(Path(path or PACK_SCHEMA).read_text(encoding='utf-8'))


def safe_filename(text: str) -> str:
    """A document name that survives a filesystem and still reads in Korean."""
    cleaned = re.sub(r'[\\/:*?"<>|\s]+', '_', str(text or '')).strip('_')
    return cleaned or 'document'


def document_name(filing: Filing, extension: str = 'xml') -> str:
    """`분기보고서_2026-05-15_20260515000123.xml` — the form name leads on purpose.

    `config/intake.json` matches requirements on `document_type` OR a regex over
    `source_document`, and its regexes already name 사업보고서·분기보고서·반기보고서.
    Putting the Korean form name first therefore makes the existing Stage 0
    checklist count Korean filings with no config change at all.
    """
    return f'{safe_filename(filing.form_type)}_{filing.filing_date}_{filing.accession}.{extension}'


def choose_consolidation(facts: Iterable[FinancialFact], preference=('CFS', 'OFS')) -> Optional[str]:
    """The one basis this pack will use. Preference order is config, not taste."""
    present = {f.consolidation_basis for f in facts if f.consolidation_basis}
    for basis in preference:
        if basis in present:
            return basis
    return None


class FinancialPackBuilder:
    """Assemble documents and facts into a schema-valid Stage 0 pack."""

    def __init__(self, ticker: str, as_of_date: str, issuer: Optional[Issuer] = None,
                 reporting_currency: Optional[str] = None,
                 consolidation_preference=('CFS', 'OFS'), document_extension: str = 'xml',
                 document_type_map: Optional[dict] = None):
        self.ticker = ticker
        self.as_of_date = as_of_date
        self.issuer = issuer
        self.reporting_currency = reporting_currency
        self.consolidation_preference = tuple(consolidation_preference)
        self.document_extension = document_extension
        self.document_type_map = dict(document_type_map or {})
        self.warnings: list = []

    def warn(self, severity: str, message: str, related=None) -> None:
        row = {'severity': severity, 'message': message}
        if related:
            row['related_fact_ids'] = list(related)
        self.warnings.append(row)

    def document_type_for(self, filing: Filing) -> str:
        declared = self.document_type_map.get(filing.form_type)
        if declared in DOCUMENT_TYPES:
            return declared
        if filing.form_type in DOCUMENT_TYPES:
            return filing.form_type
        return 'other'

    def build(self, filings: Iterable[Filing], facts: Iterable[FinancialFact],
              adjustment_candidates: Optional[list] = None,
              extra_warnings: Optional[list] = None) -> dict:
        filings = list(filings)
        facts = list(facts)
        for row in extra_warnings or []:
            self.warnings.append(row)

        documents, names = [], {}
        for index, filing in enumerate(sorted(filings, key=lambda f: (f.filing_date or '', f.accession)), 1):
            name = document_name(filing, self.document_extension)
            names[filing.accession] = name
            documents.append({
                'document_id': f'DOC-{index:03d}',
                'source_document': name,
                'document_type': self.document_type_for(filing),
                'filing_date': filing.filing_date,
                'period_end': filing.period_end,
                'is_amendment': bool(filing.is_amendment)})
        declared = {d['source_document'] for d in documents}

        basis = choose_consolidation(facts, self.consolidation_preference)
        kept, dropped_basis, orphans = [], 0, 0
        for fact in facts:
            if fact.consolidation_basis and basis and fact.consolidation_basis != basis:
                dropped_basis += 1
                continue
            if fact.source_document not in declared:
                orphans += 1
                continue
            kept.append(fact)
        if dropped_basis:
            other = [b for b in self.consolidation_preference if b != basis]
            self.warn('low', f'{dropped_basis} fact(s) on the {"/".join(other)} basis were dropped; '
                             f'this pack is {basis} only and never mixes the two bases.')
        if orphans:
            self.warn('high', f'{orphans} fact(s) referenced a document that is not in documents[] '
                              'and were dropped.')

        rows, flipped = [], 0
        for index, fact in enumerate(sorted(kept, key=self._fact_order), 1):
            row, was_flipped = self._fact_row(fact, index)
            flipped += int(was_flipped)
            rows.append(row)
        if flipped:
            self.warn('low', f'{flipped} cost/outflow value(s) were recorded as positive magnitudes '
                             'to match the Stage 0 sign convention; the filing reported them negative.')

        if basis is None and facts:
            self.warn('medium', 'No fact declared a consolidation basis; the pack records none.')

        pack = {
            'schema_version': SCHEMA_VERSION,
            'ticker': self.ticker,
            'company_name': self.issuer.legal_name if self.issuer else None,
            'as_of_date': self.as_of_date,
            'reporting_currency': self.reporting_currency,
            'documents': documents,
            'facts': rows,
            'adjustment_candidates': list(adjustment_candidates or []),
            'extraction_warnings': self.warnings,
        }
        pack['consolidation_basis'] = basis
        return pack

    @staticmethod
    def _fact_order(fact: FinancialFact):
        return (fact.period_end or '', fact.statement, fact.metric, fact.source_document)

    def _fact_row(self, fact: FinancialFact, index: int):
        value = fact.value
        flipped = False
        if fact.metric in POSITIVE_COST_METRICS and isinstance(value, (int, float)) and value < 0:
            value = abs(value)
            flipped = True
        statement = fact.statement if fact.statement in STATEMENTS else 'other'
        metric_detail = fact.metric_detail
        if fact.metric == 'other' and not metric_detail:
            # The schema allows metric=other, the invariants do not allow it bare.
            metric_detail = fact.reported_label or 'unmapped disclosure line'
        row = {
            'fact_id': f'FACT-{index:04d}',
            'metric': fact.metric,
            'metric_detail': metric_detail,
            'reported_label': fact.reported_label,
            'statement': statement,
            'gaap_status': fact.gaap_status,
            'value_reported': value,
            'unit_kind': fact.unit_kind,
            'currency': fact.currency,
            'scale_multiplier': float(fact.scale_multiplier or 1.0),
            'period_start': fact.period_start,
            'period_end': fact.period_end,
            'period_kind': fact.period_kind,
            'fiscal_year': fact.fiscal_year,
            'fiscal_quarter': fact.fiscal_quarter if fact.period_kind == 'quarter' else
                              (fact.fiscal_quarter if fact.period_kind in ('instant', 'ytd') else None),
            'segment': None,
            'filing_date': fact.filing_date,
            'source_document': fact.source_document,
            'source_page': None,
            'source_section': fact.source_section,
            'source_locator': fact.source_locator,
            'source_quote': None,
            'is_amended': bool(fact.is_amended),
            'is_restated': bool(fact.is_restated),
            'confidence': fact.confidence,
            'requires_review': bool(fact.requires_review),
            'review_reason': fact.review_reason,
        }
        if row['period_kind'] == 'fy':
            row['fiscal_quarter'] = None
        if row['period_kind'] == 'quarter' and row['fiscal_quarter'] is None:
            row['requires_review'] = True
            row['review_reason'] = (row['review_reason'] or
                                    'period_kind=quarter with no fiscal quarter resolved')
        return {k: row[k] for k in PACK_FACT_FIELDS}, flipped


def validate_pack(pack: dict, schema: Optional[dict] = None) -> list:
    """Schema plus the invariants Stage 0 enforces. Returns error strings."""
    import jsonschema
    payload = {k: v for k, v in pack.items() if k != 'consolidation_basis'}
    errors = []
    try:
        jsonschema.validate(payload, schema or load_pack_schema())
    except jsonschema.ValidationError as error:
        path = '/'.join(str(p) for p in error.absolute_path) or '<root>'
        errors.append(f'schema: {path}: {error.message}')
    try:
        import sys
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from harness_core import intake
        errors.extend(intake.pack_invariants(payload))
    except Exception as error:                 # harness not importable: schema check still ran
        errors.append(f'invariants: could not run harness_core.intake ({error})')
    return errors
