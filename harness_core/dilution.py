"""Dilution watch: the layer between a score penalty and a Hard Veto.

The harness handled dilution at two altitudes only — a score penalty in
financial_survival / reinvestment_fcf, and the 장기간 지속되는 과도한 희석 Hard
Veto. Anything the analyst found worrying but could not establish as a veto had
nowhere to go, so it went into the veto as `conditional`, which reads as
UNRESOLVED and blocks an automatic buy. An early-stage company with two years of
history was therefore eliminated for lack of a long record rather than for
anything its numbers said.

This module is the missing middle. It classifies declared dilution observables
into a watch band and, where the policy says so, tightens the position cap. It
never produces a veto status, never removes an archetype and never changes a
score: a band is an input to sizing and to the IC, not a verdict.

Thresholds live in `config/calibration.json` under `dilution_policy`; nothing
here hardcodes a number.
"""
from .conditions import number

METRIC_FIELDS = ('annualized_dilution', 'three_year_diluted_share_cagr',
                 'three_year_cumulative_dilution', 'per_share_value_proxy',
                 'per_share_value_growth', 'structural_financing_need',
                 'consecutive_years_material_dilution', 'rationale')


def declared_metrics(reports, owners):
    """The dilution observables an owner declared, if any.

    Owners are read in their configured order so the primary reviewer wins when
    two of them declare metrics; a report that declares none is skipped rather
    than treated as zero dilution.
    """
    by_id = {r.get('agent_id'): r for r in reports if r.get('analysis_status') == 'complete'}
    for agent_id in owners:
        metrics = (by_id.get(agent_id) or {}).get('dilution_metrics')
        if isinstance(metrics, dict) and number(metrics.get('annualized_dilution')):
            return agent_id, {k: metrics.get(k) for k in METRIC_FIELDS}
    return None, None


def _band_index(bands, value):
    for index, band in enumerate(bands):
        if band.get('min') is None or value >= float(band['min']):
            return index
    return len(bands) - 1


def watch(reports, owners, policy):
    """Classify declared dilution into a band. Returns None when nothing was declared."""
    if not policy:
        return None
    agent_id, metrics = declared_metrics(reports, owners)
    if not metrics:
        return None
    # Bands are declared tightest-first; an open-ended band closes the list.
    bands = sorted(policy['bands'], key=lambda b: (b.get('min') is None, -(b.get('min') or 0)))
    value = float(metrics['annualized_dilution'])
    index = _band_index(bands, value)
    escalated = [flag for flag in policy.get('escalate_one_band_if', []) if metrics.get(flag) is True]
    if escalated and index > 0:
        index -= 1                      # a structural cause moves the band one step tighter
    band = bands[index]
    return {'metric': policy['metric'], 'status': band['status'], 'declared_by': agent_id,
            'position_cap': band.get('position_cap'), 'band_note': band.get('note'),
            'escalated_by': escalated, 'is_hard_veto': False,
            **{k: metrics.get(k) for k in METRIC_FIELDS}}
