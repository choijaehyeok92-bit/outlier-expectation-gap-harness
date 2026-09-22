"""An offline provider that exercises the pipeline without pretending to analyse.

A fixture for this layer had a choice: canned prose that reads like research,
or something obviously not research that still satisfies every contract. This
is the second. Its thesis says in plain words that it contains no analysis, its
evidence cites the placeholder itself, and it leaves every Hard Veto it owns at
`candidate` — which the gate reads as UNRESOLVED and which therefore can never
produce a buy.

That last property is the important one. A placeholder that cleared a veto
would let a test suite show a green run that no analyst had looked at. Here the
harness's own gate refuses, and a test pins it.

What this provider is for: proving that the orchestrator sequences the agents,
retries a rejected document, skips work already done, and never writes
something the harness would refuse. It establishes nothing whatsoever about
whether an analysis is any good.
"""
from typing import Optional

from . import contracts

PLACEHOLDER_THESIS = (
    '[PLACEHOLDER — 분석 아님] 이 보고서는 오케스트레이션 배선을 검증하기 위한 자리표시자다. '
    '점수는 루브릭 가중평균이 성립하도록 계산된 상수이며 이 기업에 대한 판단이 아니다. '
    '실제 분석은 지정된 provider와 실제 자료로만 만들어진다.')
PLACEHOLDER_CASE = '[PLACEHOLDER] 실제 분석이 아니다. 배선 검증용 자리표시자다.'


class ProviderFailure(RuntimeError):
    """A simulated provider outage, for exercising the retry path."""


def _evidence(agent_id: str, count: int, as_of_date: str) -> list:
    return [{
        'evidence_id': f'PLACEHOLDER-{agent_id}-{index:02d}',
        'economic_driver': 'placeholder',
        'claim': f'[PLACEHOLDER] {agent_id} 자리표시자 증거 {index}. 실제 관측이 아니다.',
        'source_type': 'other',
        'source': 'packages/orchestration/fixtures.py (placeholder provider)',
        'period': 'n/a', 'as_of_date': as_of_date, 'value': None,
        'fact_or_estimate': 'interpretation',
    } for index in range(1, count + 1)]


def placeholder_report(agent_id: str, ticker: str, as_of_date: str,
                       subscore: int = 60, invalid: bool = False) -> dict:
    """A report the harness accepts, containing no analysis.

    `invalid=True` breaks the rubric arithmetic on purpose, so a test can watch
    the validator reject it and the orchestrator retry.
    """
    runtime = contracts.harness()
    agent = next((a for a in runtime.MANIFEST if a['agent_id'] == agent_id), None)
    if agent is None:
        raise ValueError(f'unknown agent {agent_id}')
    domain = agent['domain']
    limits = runtime.EXEC['report_limits']
    rubric = runtime.rubric_for(domain)

    report = {
        'agent_id': agent_id, 'ticker': ticker, 'as_of_date': as_of_date,
        'domain': domain, 'role': agent['role'], 'analysis_status': 'complete',
        'confidence_0_1': 0.2,
        'thesis': PLACEHOLDER_THESIS[:limits['thesis_chars']],
        'evidence': _evidence(agent_id, limits['evidence'][0], as_of_date),
        'counterevidence': ['[PLACEHOLDER] 반대 증거 자리표시자.'],
        'unknowns': ['[PLACEHOLDER] 이 자리표시자는 아무것도 조사하지 않았다.'],
        'falsifiers': ['[PLACEHOLDER] 실제 분석으로 교체되면 이 보고서는 폐기된다.'],
        'key_kpis': [{'name': 'placeholder', 'direction': 'flat', 'threshold': 'n/a',
                      'cadence': 'quarterly'}],
        'next_checks': ['[PLACEHOLDER] 실제 provider로 재실행한다.'],
        'verdict': 'neutral',
        'score_0_100': float(subscore),
    }

    if runtime.is_scored(domain) and rubric:
        report['subscores'] = [{'criterion_id': c['id'], 'score_0_100': subscore,
                                'rationale': '[PLACEHOLDER] 판정 근거 없음.'}
                               for c in rubric['criteria']]
        # `critical` on every criterion is the truthful severity for a document
        # that evaluated nothing, and it travels into the harness's own
        # uncertainty summary rather than being hidden.
        report['uncertainties'] = [{'criterion_id': c['id'], 'severity': 'critical',
                                    'rationale': '[PLACEHOLDER] 평가되지 않았다.'}
                                   for c in rubric['criteria']]
        weighted = runtime.rubric_score(report)
        # A broken document on purpose: the score no longer equals the rubric.
        report['score_0_100'] = float(weighted) + 15.0 if invalid else float(weighted)
        report['bull_score'] = min(100.0, report['score_0_100'] + 5)
        report['bear_score'] = max(0.0, report['score_0_100'] - 5)
        report['bull_case'] = PLACEHOLDER_CASE
        report['bear_case'] = PLACEHOLDER_CASE

    # Every veto this agent owns stays `candidate`: unevaluated, which the gate
    # reads as UNRESOLVED. A placeholder must never be able to clear one.
    owned = [v for v, ids in runtime.VETO_REVIEWERS.items() if agent_id in ids]
    report['hard_veto_flags'] = [
        {'veto': veto, 'status': 'candidate',
         'rationale': '[PLACEHOLDER] 평가하지 않았다. 자리표시자는 Veto를 해소할 수 없다.'}
        for veto in owned]

    if domain == runtime.SIGNAL_DOMAIN:
        years = int(runtime.VAL_POLICY['horizon_years'])
        report['valuation_inputs'] = {
            'valuation_percentile_5y': None, 'revenue_cagr_next_3y': None,
            'scenarios': {case: {'owner_fcf_per_share': [0.0] * years}
                          for case in ('bear', 'base', 'bull')}}
        report['archetype_signals'] = {'price_to_base_value': None,
                                       'valuation_percentile_5y': None,
                                       'revenue_cagr_next_3y': None}
    return report


class PlaceholderAgentProvider:
    """Answers any agent prompt with a valid placeholder report.

    `mode` selects what the pipeline is being asked to survive:

        valid          every call succeeds
        invalid        every call returns a document the harness rejects
        flaky          the first `fail_times` calls per agent raise, then success
        flaky_invalid  the first `fail_times` calls return a rejected document
        error          every call raises, as an outage would
    """

    name = 'placeholder'

    def __init__(self, ticker: Optional[str] = None, as_of_date: Optional[str] = None,
                 mode: str = 'valid', fail_times: int = 1, model: str = 'placeholder-v1',
                 subscore: int = 60):
        # Identity is optional: a batch hands one provider to many companies,
        # so the run's own context decides who the report is about.
        self.ticker = ticker
        self.as_of_date = as_of_date
        self.mode = mode
        self.fail_times = fail_times
        self.model = model
        self.subscore = subscore
        self.calls: list = []

    def _identity(self, context: Optional[dict]) -> tuple:
        if self.ticker and self.as_of_date:
            return self.ticker, self.as_of_date
        run_id = (context or {}).get('run_id')
        if not run_id:
            raise ProviderFailure('no run identity: bind the provider or pass run_id in context')
        runtime = contracts.harness()
        record = runtime.load_json(runtime.run_dir(run_id) / 'company_context.json')
        return record.get('ticker') or run_id, record.get('as_of_date')

    def _agent_id(self, stage: str) -> str:
        return str(stage).split(':', 1)[-1]

    def complete_json(self, *, stage, prompt, schema=None, context=None):
        agent_id = self._agent_id(stage)
        run_id = (context or {}).get('run_id') or self.ticker or '-'
        key = f'{run_id}:{agent_id}'
        seen = sum(1 for call in self.calls if call == key)
        self.calls.append(key)

        if self.mode == 'error':
            raise ProviderFailure(f'{agent_id}: simulated provider outage')
        if self.mode == 'flaky' and seen < self.fail_times:
            raise ProviderFailure(f'{agent_id}: simulated transient failure {seen + 1}')
        invalid = self.mode == 'invalid' or (self.mode == 'flaky_invalid'
                                             and seen < self.fail_times)
        ticker, as_of_date = self._identity(context)
        return placeholder_report(agent_id, ticker, as_of_date,
                                  subscore=self.subscore, invalid=invalid)

    def metadata(self, stage) -> dict:
        return {'stage': stage, 'provider': self.name, 'model': self.model,
                'analysis': 'none — placeholder'}


def provider_for(run_id: str, mode: str = 'valid', **kwargs) -> PlaceholderAgentProvider:
    """A placeholder provider bound to one run's identity and cutoff."""
    runtime = contracts.harness()
    context = runtime.load_json(runtime.run_dir(run_id) / 'company_context.json')
    return PlaceholderAgentProvider(ticker=context.get('ticker') or run_id,
                                    as_of_date=context.get('as_of_date'), mode=mode, **kwargs)
