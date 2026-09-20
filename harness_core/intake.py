"""Stage 0: document coverage and financial-pack invariants.

Nothing here scores, ranks or normalises anything. It answers two questions the
reasoning stages cannot answer for themselves: whether the raw documents the
strategy needs are actually present, and whether the preprocessed pack is
internally consistent enough to be trusted as frozen primary input.
"""
import re

from .conditions import number

# Metrics recorded as a positive cost / outflow magnitude regardless of how the
# filing signs them. Everything else keeps the sign the document used.
POSITIVE_COST_METRICS = {
    'capex', 'r_and_d', 's_and_m', 'g_and_a', 'sbc', 'd_and_a',
    'interest_expense', 'tax_expense', 'acquisitions', 'stock_repurchases', 'debt_repayment',
}
DIRECTION_PRESERVED_METRICS = {
    'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow',
    'net_income', 'operating_income', 'asset_sales', 'stock_issuance', 'debt_issuance',
}


def _matches(document, requirement):
    if document.get('document_type') in (requirement.get('document_types') or []):
        return True
    pattern = requirement.get('source_regex')
    if not pattern:
        return False
    return bool(re.search(pattern, str(document.get('source_document') or ''), re.I))


def coverage(pack, policy):
    """Per-requirement document counts, with the blocking gaps separated out."""
    documents = (pack or {}).get('documents') or []
    blocking_levels = set(policy.get('blocking_levels') or [])
    rows, blocking, advisory, conditional = [], [], [], []
    for requirement in policy['requirements']:
        matched = [d['source_document'] for d in documents if _matches(d, requirement)]
        needed = int(requirement.get('min_count', 1))
        met = len(matched) >= needed
        row = {
            'id': requirement['id'], 'importance': requirement['importance'],
            'needed': needed, 'found': len(matched), 'met': met,
            'purpose': requirement['purpose'], 'us': requirement.get('us'), 'kr': requirement.get('kr'),
            'condition': requirement.get('condition'),
            'examples': matched[:3],
        }
        row['conditional'] = bool(requirement.get('condition'))
        rows.append(row)
        if not met:
            if row['conditional']:
                conditional.append(row)   # the condition itself cannot be checked from the pack
            elif requirement['importance'] in blocking_levels:
                blocking.append(row)
            else:
                advisory.append(row)
    return {'requirements': rows, 'blocking_gaps': blocking, 'advisory_gaps': advisory,
            'conditional_unverified': conditional,
            'documents_present': len(documents),
            'satisfied': sum(1 for r in rows if r['met']), 'total': len(rows)}


def pack_invariants(pack):
    """Checks the JSON schema cannot express. Returns a list of error strings."""
    errors = []
    facts = pack.get('facts') or []
    documents = pack.get('documents') or []

    fact_ids = [f.get('fact_id') for f in facts]
    if len(fact_ids) != len(set(fact_ids)):
        errors.append('duplicate fact_id')
    adjustments = pack.get('adjustment_candidates') or []
    adjustment_ids = [a.get('adjustment_id') for a in adjustments]
    if len(adjustment_ids) != len(set(adjustment_ids)):
        errors.append('duplicate adjustment_id')
    document_ids = [d.get('document_id') for d in documents]
    if len(document_ids) != len(set(document_ids)):
        errors.append('duplicate document_id')

    known_facts = set(fact_ids)
    for adjustment in adjustments:
        reference = adjustment.get('amount_fact_id')
        if reference and reference not in known_facts:
            errors.append(f"{adjustment.get('adjustment_id')}: amount_fact_id {reference} does not exist")

    declared_sources = {d.get('source_document') for d in documents}
    for fact in facts:
        fid = fact.get('fact_id')
        if fact.get('metric') == 'other' and not fact.get('metric_detail'):
            errors.append(f'{fid}: metric=other requires metric_detail')
        value = fact.get('value_reported')
        if fact.get('metric') in POSITIVE_COST_METRICS and number(value) and value < 0:
            errors.append(f"{fid}: {fact['metric']} must be a positive cost magnitude, got {value}")
        kind, quarter = fact.get('period_kind'), fact.get('fiscal_quarter')
        # An instant may sit at a quarter end, so it may carry the quarter. A full
        # fiscal year cannot be one quarter.
        if kind == 'fy' and quarter is not None:
            errors.append(f'{fid}: period_kind=fy cannot carry fiscal_quarter={quarter}')
        if kind == 'quarter' and quarter is None:
            errors.append(f'{fid}: period_kind=quarter requires fiscal_quarter')
        if fact.get('unit_kind') == 'percent' and number(value) and abs(value) > 1.5:
            errors.append(f'{fid}: percent values are recorded as decimals, got {value}')
        if fact.get('source_document') not in declared_sources:
            errors.append(f"{fid}: source_document is not listed in documents[]")
    return errors


def pack_summary(pack):
    facts = pack.get('facts') or []
    by_status = {}
    for fact in facts:
        by_status[fact.get('gaap_status')] = by_status.get(fact.get('gaap_status'), 0) + 1
    return {
        'documents': len(pack.get('documents') or []),
        'facts': len(facts),
        'adjustment_candidates': len(pack.get('adjustment_candidates') or []),
        'extraction_warnings': len(pack.get('extraction_warnings') or []),
        'facts_requiring_review': sum(1 for f in facts if f.get('requires_review')),
        'restated_facts': sum(1 for f in facts if f.get('is_restated')),
        'facts_by_gaap_status': by_status,
    }
