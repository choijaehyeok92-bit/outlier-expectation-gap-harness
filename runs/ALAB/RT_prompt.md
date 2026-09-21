# 과제: ALAB / 기준일 2026-09-18 / red_team (RT)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/ALAB/reports/RT.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"ALAB","company_name":"Astera Labs, Inc.","as_of_date":"2026-09-18","currency":"USD","current_price":303.25,"shares_diluted":185000000,"market_cap_usd":56101250000,"enterprise_value":54848292000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["SEC Form 10-K FY2025 filed 2026-02-20","SEC Form 10-Q Q1 2026 filed 2026-05-06","SEC Form 10-Q Q2 2026 filed 2026-08-05","SEC 2026 DEF 14A filed 2026-04-23","SEC 8-K/Q2 2026 earnings release filed 2026-08-04","SEC 8-K filed 2026-02-10 for Amazon customer warrant","Astera Labs IR release dated 2026-09-15 for Leo X-Series","StockAnalysis historical close 2026-09-18: $303.25"],"special_questions":["How much of Astera Labs' current valuation already capitalizes a multi-year AI interconnect supercycle?","Can Scorpio, Aries, Taurus, Leo and custom connectivity expand from point products into a durable rack-scale AI fabric platform?","Does customer concentration, including the Amazon warrant structure, create a single-customer dependency risk despite product diversification?"],"intake_facts":["Q2 2026 revenue $392.4M, +27% QoQ and +104% YoY; H1 2026 revenue $700.761M.","Q2 2026 GAAP gross margin 73.3%, operating income $89.248M, net income $153.088M.","H1 2026 operating cash flow $162.276M and capex $28.054M.","2026-06-30 cash $111.453M plus marketable securities $1.141505B; no material funded debt identified.","Q3 2026 revenue guidance $540M-$560M and diluted share guidance approximately 185M.","Q2/H1 2026 top direct-customer revenue concentrations were 29%, 25%, 15%, 13% for the quarter and 29%, 21%, 17%, 13% for H1; some are manufacturing partners rather than end customers.","A February 2026 Amazon customer warrant permits up to 3,262,299 shares at $142.82, contingent on specified purchase-performance conditions.","June 2026 outstanding common shares were 173.485M versus 170.186M at 2025 year-end; H1 SBC was $112.905M in the cash-flow reconciliation."],"net_cash_per_share":6.772745945945946,"valuation_metric":"Locked owner-FCF/share DCF. Astera Labs has less than five years of public trading history, so valuation_percentile_5y is left null. Net cash/share uses June 30 cash plus marketable securities divided by Q3 guided diluted shares.","valuation_overrides":{"terminal_multiples":{}},"diagnostics":{"turnaround_candidate":false},"geo_exposure":{"revenue_by_region":{"China":0.34571986740129657,"Singapore":0.2923564524852268,"Taiwan":0.28386711018449945,"United States":0.029251057065104936,"Other":0.048805512863872275},"production_by_region":{"Taiwan":0.67,"United States":0.26,"Other":0.07},"critical_supplier_regions":["Taiwan"],"export_control_dependencies":["U.S.-China semiconductor export controls","Advanced AI infrastructure trade restrictions"]}}

## 검증된 1차 자료 사실
# ALAB Stage 0 source bundle — as of 2026-09-18

Primary sources are SEC filings and Astera Labs investor relations. The GitHub runner still attempts the harness-native EDGAR fetch first; this bundle is the documented manual fallback if the SEC endpoint rejects the runner.

## Primary SEC sources
- FY2025 10-K filed 2026-02-20: https://www.sec.gov/Archives/edgar/data/1736297/000173629726000010/alab-20251231.htm
- Q1 2026 10-Q filed 2026-05-06: https://www.sec.gov/Archives/edgar/data/1736297/000173629726000020/alab-20260331.htm
- Q2 2026 10-Q filed 2026-08-05: https://www.sec.gov/Archives/edgar/data/1736297/000173629726000035/alab-20260630.htm
- 2026 DEF 14A filed 2026-04-23: https://www.sec.gov/Archives/edgar/data/1736297/000114036126016359/ny20065212x1_def14a.htm
- Q2 2026 earnings release: https://www.sec.gov/Archives/edgar/data/1736297/000173629726000033/q226exhibit991.htm
- Amazon customer warrant 8-K: https://www.sec.gov/Archives/edgar/data/1736297/000110465926012606/tm265461d1_8k.htm

## Cutoff market data
- ALAB close 2026-09-18: $303.25 — https://stockanalysis.com/stocks/alab/history/

## Frozen context conventions
- June 30 common shares outstanding: 173.485M.
- Q3 2026 guidance uses approximately 185M diluted shares; this is used for frozen diluted share count and conservative market cap.
- June 30 cash + marketable securities: $1.252958B.
- No material funded debt was identified in the Q2 balance sheet; net cash/share = $6.7727 on the 185M diluted-share convention.
- Revenue geography is billing-location based and should not be treated as end-demand geography.

## 입력
runs/ALAB/digest.md (없으면 `python harness.py aggregate ALAB` 후 `digest ALAB` 실행). 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다.

## 지침 RT (red_team)
# Red Team

- `agent_id`: `RT`
- `domain`: `red_team`

## 임무
Bull case의 가장 약한 고리를 네 가지 렌즈로 공격하고, 하나의 일관된 공매도 논리로 묶는다. Red Team 결과는 점수에 더하지 않고 Hard Veto와 IC 반론의 증거로만 쓴다.

## 렌즈별 질문
**포렌식 회계**
1. 현금흐름과 손익의 괴리는? 조정 이익·FCF가 경제적 비용을 제외하는가?
2. 매출인식·자본화·충당금·투자손익에 공격적 가정이 있는가? 감사·내부통제·재작성 이슈는?

**공매도 논리**
3. 시장이 낙관적으로 오해하는 핵심과 가장 취약한 가정(TAM·점유율·마진)은? 주가 60~80% 하락을 설명할 현실적 시나리오는?

**기술 대체**
4. 대체기술의 비용곡선은 얼마나 빨리 개선되며, 고객 전환비용이 기술전환 앞에서 실제 방어벽이 되는가? 기존 수익원이 자기잠식될 위험은?

**규제·집중**
5. 매출·이익·공급자·지역의 집중도와 단일 이벤트 리스크(규제승인·수출통제·반독점)는? 대체경로와 완충장치가 있는가?

마지막으로 공매도 논리를 반증할 증거를 적는다.

## 입력
`digest.md`와 공시 원문(색인 기준 부분 읽기).

## Hard Veto 중점
- 경영진 정직성 또는 회계 신뢰성 훼손
- 해자의 지속적인 축소
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성
- 그 밖에 증거가 확인한 모든 Veto

`confirmed`는 증거가 결정적일 때만 쓴다.

## 필수 Hard Veto 판정
아래 항목은 생략하면 clear가 아니다. cleared|conditional|confirmed 중 하나를 기록한다. 근거 부족이면 candidate로 남겨 WATCH를 유발한다.
- 경영진 정직성 또는 회계 신뢰성 훼손
- 구조적으로 과도한 외부자본 조달 의존
- 고객가치 없이 마케팅·보조금에 의존하는 성장
- 증분 ROIC의 구조적 붕괴
- 해자의 지속적인 축소
- 현재가격이 비현실적인 Bull Case 이상을 요구
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성

## 공통 규칙
## 분석
- 기준일을 먼저 선언한다. 기준일 이후 정보는 사용하지 않는다.
- 최소 3개의 독립 근거를 확보하고, 가능한 한 1차 자료를 우선한다.
- 근거와 반대근거를 모두 제시한다.
- `사실 / 추정 / 해석`을 구분한다.
- 자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면, 예산 내에서 웹 검색·IR 자료·신뢰 가능한 2차 자료로 **먼저 보완을 시도한다**.
- 보완 시도 후에도 확보하지 못한 것만 `unknowns`에 남기고, 무엇을 어디서 찾으려 했는지 함께 적는다.
- 2차 자료로 채운 값은 `fact_or_estimate`를 `estimate` 또는 `interpretation`으로 표기하고 `EVIDENCE_POLICY.md`의 출처 위계를 지킨다.
- 결론보다 먼저 반증조건을 작성한다.

## 관점 분리 (점수 도메인과 독립 평가축)
에이전트는 항목당 하나지만, 지침의 Bull·Verifier·Skeptic 관점을 **각각 끝까지 밀어붙인 뒤** 결론을 낸다. 합의를 먼저 정하고 관점을 끼워 맞추지 않는다.
- `bull_case` / `bear_case`: Bull 논리와 Skeptic 논리를 각각 300자 이내로 쓴다.
- `bull_score` / `bear_score`: 각 논리가 맞을 때의 도메인 점수. `bear_score ≤ score_0_100 ≤ bull_score`.
- `subscores`: `config/calibration.json`의 criterion을 정확히 한 번씩 5점 단위로 채점한다. 이 값이 점수의 원천이다.
- `score_0_100`: subscores의 고정 가중평균과 같아야 하며 하네스가 검증한다.
- `bull_score` / `bear_score`: 시나리오 범위와 논쟁 폭을 보여주는 메타데이터다. 단일 모델의 자체 범위가 넓다는 이유만으로 자동 감점하지 않는다.
- `bull_score - bear_score`가 20 이상이면 재검토 표시를 남기되 수치 점수와 분리한다.

## 토큰 예산
- `company_context.json`의 기준 정보와 `sources/README.md`의 검증된 사실은 다시 검색하지 않는다. 오류를 발견했을 때만 근거와 함께 지적한다.
- 웹 검색·페치는 `config/workflow.json`의 `research_budget` 이내로 쓴다(기본 에이전트당 15회). 예산은 위 공백 보완에 우선 배정한다.
- 공시 원문(.txt)은 통째로 읽지 않는다. `sources/INDEX.md`의 줄번호로 grep하거나 부분만 읽는다.
- Phase 3·IC 에이전트는 다른 에이전트의 원 보고서 대신 `digest.md`를 읽는다. 원 보고서는 특정 주장을 검증할 때만 그 파일 하나를 연다.
- 보고서 분량은 `report_limits`를 지킨다(thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개, falsifiers·key_kpis·next_checks 각 3개). `unknowns`에는 핵심 가설에 직결되는 것만 쓴다.
- `config/calibration.json`에서 자신에게 배정된 Hard Veto는 반드시 `cleared / conditional / confirmed` 중 하나로 명시한다. 미기재는 clear가 아니다.
- 작성 후 `python harness.py validate <TICKER> <AGENT_ID>`로 검증한다. 스키마 파일을 직접 읽지 않아도 된다.

## 재현성
- agent 실행 전 `python harness.py freeze TICKER --provider ... --model ...`로 company_context와 sources를 해시 고정한다.
- freeze 이후 입력이 바뀌면 prompt 생성을 중단한다. 모델 비교는 동일 `input_snapshot_sha256`에서만 유효하다.
- EV는 고정된 할인율·terminal multiple·현재가격·순현금을 사용하며 LLM은 연도별 owner FCF/share 경로만 제안한다.

## v3 분석 계약
새 evidence에는 가능하면 안정적인 evidence_id와 공유 economic_driver를 기록한다. 동일 사실을 여러 긍정 도메인에 재사용한 evidence_concentration_flags는 ED/RT/IC 검토용이며 자동 감점하지 않는다. Macro/지정학은 점수를 바꾸지 않고 pacing·위험예산·모니터링 또는 회사 근거를 통한 재분석 요청만 만든다.

## Hard Veto (정확한 문자열 사용)
- 경영진 정직성 또는 회계 신뢰성 훼손
- 구조적으로 과도한 외부자본 조달 의존
- 장기간 지속되는 과도한 희석
- 고객가치 없이 마케팅·보조금에 의존하는 성장
- 증분 ROIC의 구조적 붕괴
- 해자의 지속적인 축소
- 현재가격이 비현실적인 Bull Case 이상을 요구
- 단일 제품·단일 고객·단일 규제에 대한 치명적 종속성
- 파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음

## Hard Veto 판정 기준
Hard Veto는 "중대한 리스크"가 아니라 "이 문장이 실제로 성립하는가"로 판정한다. 문구의 모든 구성요건이 충족될 때만 성립하며, 하나라도 반증되면 cleared다. 우려는 스코어·uncertainties·모니터링으로 보내고 veto로 올리지 않는다.
도메인 점수에 이미 온전히 반영된 사실만으로는 veto를 세우지 않는다. veto는 그 자체의 구성요건이 독립적으로 충족될 때만 성립한다(anchor_policy의 중복 감점 금지를 veto 층에 확장).
{
  "status_rule": {
    "confirmed": "구성요건 전부가 1차 자료로 확인됨",
    "conditional": "구성요건 전부가 충족될 가능성이 높으나 결정적 자료 1개가 미확보. 해소 조건을 반드시 명시한다",
    "candidate": "평가하지 않았거나 판단 근거가 전혀 없음",
    "cleared": "구성요건 중 최소 하나가 증거로 반증됨"
  },
  "definitions": {
    "경영진 정직성 또는 회계 신뢰성 훼손": {
      "elements": [
        "정직성 또는 회계 신뢰성이 훼손된 사건이 발생했을 것"
      ],
      "cleared_if": [
        "재작성·감사인 이견/교체·내부통제 중대결함·미공시 관련자거래가 모두 부재"
      ],
      "not_covered": "공격적이지만 GAAP을 준수하는 평가(Level 3 등)는 감시항목이지 훼손의 증거가 아니다. 이익 품질은 RF·EV 점수가 반영한다."
    },
    "구조적으로 과도한 외부자본 조달 의존": {
      "elements": [
        "영업활동이 자체적으로 자금을 조달하지 못할 것",
        "그 결과 외부자본 조달이 구조적으로 반복될 것"
      ],
      "cleared_if": [
        "영업현금흐름이 필수지출을 상회",
        "조달이 생존용이 아니라 재량적 자본배분(자사주·투자)을 위한 것"
      ],
      "not_covered": "차입 자체가 아니라 차입 없이 사업이 성립하지 않는 구조가 요건이다."
    },
    "고객가치 없이 마케팅·보조금에 의존하는 성장": {
      "elements": [
        "고객가치가 부재할 것(필수 요건)",
        "성장이 마케팅·보조금에 의존할 것"
      ],
      "cleared_if": [
        "높은 gross margin과 낮은 판관비 비율이 동시에 관측되어 고객이 프로모션 없이 지불함을 보임",
        "고객 선수금·대기 수요 등 지불의사의 직접 증거"
      ],
      "not_covered": "벤더 금융(공급자가 고객의 구매자금을 지분투자·대출·보증으로 대는 구조)은 이 문구가 포괄하지 않는다. 고객가치 부재라는 필수 요건과 별개 사안이므로 veto가 아니라 CP unit_economics·FS dilution_offbalance·AS permanent_loss 점수와 key_kpis·uncertainties로 처리한다. out_of_scope_concerns 참조."
    },
    "증분 ROIC의 구조적 붕괴": {
      "elements": [
        "증분 ROIC가 자본비용 아래로 내려갔을 것",
        "그것이 일시적이 아니라 구조적일 것"
      ],
      "cleared_if": [
        "증분 ROIC가 자본비용을 크게 상회"
      ],
      "not_covered": "높은 수준에서의 하락(체감)은 붕괴가 아니다."
    },
    "해자의 지속적인 축소": {
      "elements": [
        "해자 지표가 실제로 축소 중일 것",
        "그 축소가 지속적일 것"
      ],
      "cleared_if": [
        "gross margin·점유율·전환비용 등 관측 지표가 유지 또는 강화"
      ],
      "not_covered": "미래의 대체 위협은 MT 점수와 모니터링 대상이지 현재 축소의 증거가 아니다."
    },
    "현재가격이 비현실적인 Bull Case 이상을 요구": {
      "elements": [
        "현재가가 Bull 시나리오 가치를 초과할 것"
      ],
      "cleared_if": [
        "price_to_base_value가 Bull/현재가 배수 안에 있음"
      ],
      "not_covered": "Base가 야심적이라는 판단은 EV 점수가 반영한다."
    },
    "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성": {
      "elements": [
        "단일 제품·고객·규제에 대한 종속이 있을 것",
        "그 종속이 치명적일 것 — 해당 요인 상실 시 사업 경제성이 회복 불가하게 훼손될 것"
      ],
      "cleared_if": [
        "해당 리스크가 실제로 현실화됐음에도 매출·이익이 유지되거나 성장한 이력"
      ],
      "watch_trigger": [
        "단일 고객이 매출의 25%를 초과",
        "제2의 관할에서 판매 제한이 발생",
        "아직 스트레스 테스트되지 않은 종속 축(고객 집중 등)은 cleared로 두되 이 임계값을 모니터링한다"
      ],
      "not_covered": "높은 집중도 자체는 요건이 아니다. SL의 durability_risks가 반영한다."
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "경영진 정직성 또는 회계 신뢰성 훼손", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "구조적으로 과도한 외부자본 조달 의존", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "고객가치 없이 마케팅·보조금에 의존하는 성장", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "증분 ROIC의 구조적 붕괴", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "해자의 지속적인 축소", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "현재가격이 비현실적인 Bull Case 이상을 요구", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}, {"veto": "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose"}
작성 후 `python harness.py validate ALAB RT`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
