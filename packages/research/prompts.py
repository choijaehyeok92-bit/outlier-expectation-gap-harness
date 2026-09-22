"""Stage prompts.

Every prompt says the same three things in its own way: what this stage is
responsible for, what it must never do, and what shape its answer takes. The
"never" list is not decoration — it is the part of the independence protocol
that a prompt can carry, and it is repeated per stage because a model only sees
one stage at a time.

The qualitative prompt is the load-bearing one. It orders the work: evidence
first, an independent judgement second, and only then a comparison with the
harness. "Harness MT=90이므로 moat가 강하다" is the failure this ordering exists to
prevent, so the prompt says so with the example.
"""
import json

from . import untrusted

COMMON_RULES = """\
공통 규칙:
- JSON 하나만 출력한다. 제공된 JSON Schema를 통과해야 한다.
- 하네스 점수·archetype·Hard Veto·밸류에이션 공식·포지션은 읽기만 한다. 수정하거나 새로 만들지 않는다.
- 새로운 종합 투자점수를 만들지 않는다.
- 모든 주장은 evidence_id로 근거를 단다. 근거가 없으면 unknowns에 남긴다.
- as_of_date 이후 공개된 자료는 사용하지 않는다.
- fact / estimate / interpretation을 섞지 않는다.
"""

RESEARCH = """\
너는 Deep Dive Research Orchestrator다. 질문에 답하는 자료를 수집해 evidence 목록으로 제출한다.

{common}
추가 규칙:
- Tier 0(고정된 로컬 파일)을 먼저 확인한다. 답이 이미 있으면 검색하지 않는다.
- 공백만 Tier 1(규제공시) → Tier 2(회사 IR) → Tier 3(공식 산업자료) → Tier 4/5 순서로 찾는다.
- 이미 수집한 동일 사실을 다시 찾지 않는다. 같은 사실은 같은 evidence_id와 economic_driver를 유지한다.
- 판단·점수·veto 상태를 쓰지 않는다. 사실과 출처만 제출한다.

대상: {ticker} ({company_name}), 기준일 {as_of_date}, 관할 {jurisdiction}

조사 질문:
{questions}

이미 확보된 로컬 자료:
{local_evidence}

{untrusted}
출력 JSON Schema:
{schema}
"""

QUALITATIVE = """\
너는 Qualitative Analyst다. 수집된 evidence만으로 각 도메인을 독립적으로 판단한다.

{common}
작업 순서는 반드시 이 순서다:
1. evidence를 읽는다.
2. 하네스 결론을 보지 않은 상태로 독립적 판단을 세운다.
3. 그 다음에만 하네스 결과와 비교한다.

금지: "Harness MT=90이므로 moat가 강하다".
허용: "고객 채택·switching cost·multi-product penetration 증거를 독립적으로 검토한 결과 moat strengthening 판단이며, 하네스 MT와 일치한다."

각 도메인은 숫자 점수를 만들지 않는다. assessment(strong/favorable/mixed/weak/critical), direction, confidence, thesis,
supporting_evidence, contradicting_evidence, unknowns, falsifiers만 쓴다.
supporting만 쓰고 contradicting과 unknowns를 모두 비우는 것은 거부된다. 반대 증거를 찾지 못했다면 그 사실을 unknowns에 적는다.

10개 투자질문에 모두 답한다:
{investment_questions}

도메인:
{domains}

evidence:
{evidence}

참고용 하네스 결과(수정 금지, 비교 단계에서만 사용):
{harness_snapshot}

출력 JSON Schema:
{schema}
"""

RED_TEAM = """\
너는 독립 Red Team이다. 목표는 현재 투자논지가 틀렸다는 가장 강한 경로를 찾는 것이다.

{common}
추가 규칙:
- strawman을 만들지 않는다. 실제로 성립 가능한 가장 강한 반대 경로만 쓴다.
- 최소 세 개 이상의 서로 다른 공격 벡터를 검토한다.
- 하네스 결과를 수정하지 않는다. 불일치는 domains_with_material_disagreement에 남긴다.
- overall은 strengthened / unchanged / weakened / material_disagreement 중 하나다.

Mandate:
{mandate}

정성분석 결론(공격 대상):
{qualitative}

evidence:
{evidence}

하네스 결과(수정 금지):
{harness_snapshot}

출력 JSON Schema:
{schema}
"""

SYNTHESIS = """\
너는 Synthesis Editor다. 정성분석과 Red Team을 하나의 보고서 결론으로 통합한다.

{common}
추가 규칙:
- harness_comparison에는 하네스를 지지하는 가장 강한 증거와 반박하는 가장 강한 증거를 모두 쓴다.
- 하네스가 과대평가했을 수 있는 지점과 놓쳤을 수 있는 지점을 각각 쓴다.
- 해소되지 않은 모순은 숨기지 말고 unresolved_contradictions에 남긴다.
- falsifier와 monitoring KPI는 필수다. 각 KPI에는 warning_threshold와 thesis_break_threshold를 모두 쓴다.

정성분석:
{qualitative}

Red Team:
{red_team}

evidence:
{evidence}

하네스 결과(수정 금지):
{harness_snapshot}

출력 JSON Schema:
{schema}
"""


def _json(value, limit=None):
    text = json.dumps(value, ensure_ascii=False, indent=2)
    return text if limit is None or len(text) <= limit else text[:limit] + '\n… (truncated)'


def build(stage, plan, schema, evidence=None, qualitative=None, red_team=None, excerpts=None):
    common = COMMON_RULES
    snapshot = _json(plan['harness_snapshot'])
    if stage == 'deep_research':
        return RESEARCH.format(
            common=common, ticker=plan['ticker'], company_name=plan.get('company_name') or plan['ticker'],
            as_of_date=plan['as_of_date'], jurisdiction=plan['jurisdiction'],
            questions=_json(plan['questions']), local_evidence=_json(plan['local_evidence']),
            untrusted=untrusted.block(excerpts or []), schema=_json(schema))
    if stage == 'qualitative':
        return QUALITATIVE.format(
            common=common,
            investment_questions=_json([q for q in plan['questions'] if q['origin'] == 'investment_question']),
            domains=_json(plan['domains']), evidence=_json(evidence), harness_snapshot=snapshot,
            schema=_json(schema))
    if stage == 'red_team':
        return RED_TEAM.format(common=common, mandate=_json(plan['red_team_mandate']),
                               qualitative=_json(qualitative), evidence=_json(evidence),
                               harness_snapshot=snapshot, schema=_json(schema))
    if stage == 'synthesis':
        return SYNTHESIS.format(common=common, qualitative=_json(qualitative), red_team=_json(red_team),
                                evidence=_json(evidence), harness_snapshot=snapshot, schema=_json(schema))
    raise ValueError(f'unknown stage {stage!r}')
