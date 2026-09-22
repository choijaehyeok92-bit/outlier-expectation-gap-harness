# 과제: META_REVIEW_20260921 / 기준일 2026-09-21 / evidence_quality (ED)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/META_REVIEW_20260921/reports/ED.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"META","company_name":"Meta Platforms, Inc.","as_of_date":"2026-09-21","currency":"USD","current_price":741.25,"shares_diluted":2566000000,"market_cap_usd":1902047500000,"enterprise_value":1895451500000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm","https://www.sec.gov/Archives/edgar/data/1326801/000132680125000017/meta-20241231.htm","https://www.sec.gov/Archives/edgar/data/1326801/000132680124000012/meta-20231231.htm","https://www.sec.gov/Archives/edgar/data/1326801/000132680124000081/meta-20240930.htm","https://www.sec.gov/Archives/edgar/data/1326801/000132680125000054/meta-20250331.htm","https://www.sec.gov/Archives/edgar/data/1326801/000162828025036791/meta-20250630.htm","https://www.sec.gov/Archives/edgar/data/1326801/000162828025047240/meta-20250930.htm","https://www.sec.gov/Archives/edgar/data/1326801/000162828026028526/meta-20260331.htm","https://www.sec.gov/Archives/edgar/data/1326801/000162828026050705/meta-20260630.htm","https://finance.yahoo.com/quote/META/history/","META 2026-09-21 closing price $741.25"],"special_questions":["Separate structural AI-driven monetization upside from expectations already embedded in the 2026-09-18 price.","Stress-test the return path against sharply higher AI infrastructure capex and Reality Labs losses.","Treat the Q3 2025 OBBBA tax charge as a normalization candidate, not an automatically excluded expense."],"net_cash_per_share":2.570538,"valuation_overrides":{"terminal_multiples":{}},"diagnostics":{"turnaround_candidate":false},"geo_exposure":{"revenue_by_region":{"United States and Canada":0.392435,"Europe":0.231726,"Asia-Pacific":0.267792,"Rest of World":0.108048}}}

## 입력
runs/META_REVIEW_20260921/digest.md (없으면 `python harness.py aggregate META_REVIEW_20260921` 후 `digest META_REVIEW_20260921` 실행). 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다.

## 지침 ED (evidence_auditor)
# Evidence Auditor

- `agent_id`: `ED`
- `domain`: `evidence_quality`

## 임무
Phase 1 분석의 핵심 증거가 신뢰할 수 있는 출처·정의·기간에 기반하는지 감리하고, 투자가설을 검증할 최소 KPI 세트와 반증조건을 확정한다. 투자가설이 반증 불가능한 서사로 변하는 것을 막는다.

## 과제
**출처 감리**
1. 점수나 Veto 판정을 좌우하는 수치에 1차 자료가 있는가? 2차 자료가 원자료를 왜곡했는가?
2. 비교기간·회계기준·지표정의가 일관적인가? 회사가 KPI 정의를 바꿨는가?

**KPI 추적**
3. 핵심 선행 KPI 3개와 각 KPI가 검증하는 가설, 비중 확대·축소 임계값은? 분기 노이즈와 구조적 변화를 어떻게 구분하는가?

**반증조건**
4. 무엇이 나오면 가설이 틀렸다고 인정해야 하는가? 그 조건은 관측 가능하고 시한이 있는가?
5. 비중 확대 조건과 매도 조건이 대칭적으로 명확한가? 실적 악화를 외부요인으로 끝없이 합리화할 여지는?

## 입력
`digest.md`. 특정 주장을 검증할 때만 해당 보고서와 공시 원문을 부분적으로 연다.

## Hard Veto 중점
증거 품질 때문에 Veto 판정의 신뢰도가 달라질 때만 보고한다.

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
- **`conditional`은 정보 부족 상태가 아니다.** 구성요건이 거의 모두 1차 자료로 확인되었고 결정적 자료 하나만 미확보인 "거의 confirmed" 상태다. 자료가 없어 판단할 수 없으면 `conditional`이 아니라, 구성요건이 반증되었으면 `cleared`, 평가 자체를 못 했으면 `candidate`다. "아직 장기 이력이 없다", "앞으로 나빠질 수 있다"는 `conditional`의 사유가 될 수 없다. 그런 우려는 점수·`uncertainties`·`key_kpis`로 보낸다.
- `requires_element_assessment`가 선언된 veto에 `confirmed`·`conditional`을 쓰려면 `elements_met`에 구성요건 전부를 참/거짓으로 답해야 한다. `confirmed`는 전부 참, `conditional`은 정확히 하나만 거짓이며 `decisive_missing_evidence`에 그 자료와 해소 조건을 적는다. `validate`가 이를 검사한다.
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
    "장기간 지속되는 과도한 희석": {
      "requires_element_assessment": true,
      "elements": [
        "희석이 장기간 지속될 것",
        "그 폭이 과도할 것",
        "희석을 감안한 주당 경제가치가 충분히 증가하지 않을 것",
        "향후에도 반복될 구조적 자금조달 또는 SBC 원인이 있을 것"
      ],
      "element_tests": {
        "희석이 장기간 지속될 것": "다음 중 하나가 1차 자료로 확인될 때만 충족: (1) multi_year_min_years 이상 연속 회계연도에서 의미 있는 순희석 반복, (2) 최근 3년 희석주식수 CAGR ≥ three_year_diluted_share_cagr, (3) 최근 3년 누적 희석 ≥ three_year_cumulative_dilution. 한 분기 또는 한 번의 ATM·M&A 자금조달은 이 요건을 충족하지 못한다. 상장 이력이 짧아 장기 자료가 없는 것은 '충족되지 않음'이지 '미확인'이 아니다.",
        "그 폭이 과도할 것": "희석률 자체가 아니라 아래 주당 경제가치 요건과 함께 판단한다. 단일 연도 희석률이 높다는 사실만으로는 충족하지 않는다.",
        "희석을 감안한 주당 경제가치가 충분히 증가하지 않을 것": "per_share_value_proxies의 우선순위에 따라 선택한 proxy가 희석 기간 동안 정체·감소해야 충족된다. 주식수 +7%에 gross profit +50%처럼 주당 proxy가 크게 증가하면 이 요건은 반증되고 veto는 cleared다.",
        "향후에도 반복될 구조적 자금조달 또는 SBC 원인이 있을 것": "사업 유지에 반복 ATM이 필요하거나, runway가 짧아 FCF breakeven 전 추가 증자가 불가피하거나, SBC가 장기간 매출·GP 성장보다 빠르게 증가하거나, 자본계획상 반복 equity issuance가 불가피할 때 충족된다. 일회성 M&A·일시적 증자이고 현재 runway가 충분하면 충족되지 않는다."
      },
      "thresholds": {
        "multi_year_min_years": 2,
        "three_year_diluted_share_cagr": 0.08,
        "three_year_cumulative_dilution": 0.25
      },
      "per_share_value_proxies": [
        {
          "priority": 1,
          "proxy": "owner_fcf_per_share",
          "use_when": "기본. FCF가 구조적으로 의미 있는 단계"
        },
        {
          "priority": 2,
          "proxy": "gross_profit_per_share",
          "use_when": "FCF가 아직 구조적으로 음수인 초기 성장기업"
        },
        {
          "priority": 3,
          "proxy": "arr_per_share",
          "use_when": "SaaS 등 ARR이 검증 가능하게 공시되는 경우"
        },
        {
          "priority": 4,
          "proxy": "economic_value_per_share_proxy",
          "use_when": "위 셋이 부적절한 사업. 선택 이유를 명시한다"
        }
      ],
      "cleared_if": [
        "희석주식수가 보합 또는 감소",
        "자사주 매입이 SBC를 상쇄",
        "희석 기간 동안 선택한 주당 경제가치 proxy가 충분히 증가",
        "장기간 지속 요건의 세 가지 임계값 중 어느 것도 충족되지 않음 (상장 이력이 짧아 자료가 없는 경우 포함)",
        "희석 원인이 일회성이고 현재 runway로 추가 증자 필요성이 확인되지 않음"
      ],
      "watch_triggers": [
        "연환산 희석률이 dilution_policy의 monitor 밴드 이상",
        "SBC가 매출 또는 gross profit 성장보다 빠르게 증가",
        "전환증권·ATM 잔여 한도가 유의미"
      ],
      "not_covered": "SBC 존재 자체는 요건이 아니다. 단일 연도의 높은 희석, 상장 이력이 짧아 장기 자료가 없는 것, 장래 희석 가능성에 대한 우려도 요건이 아니다. 이들은 FS·RF 점수와 dilution_watch로 보낸다."
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
    },
    "파산 또는 영구손실 확률이 기대수익에 비해 지나치게 높음": {
      "elements": [
        "파산 또는 사업가치의 영구적 소멸 확률이 유의미할 것",
        "그 확률이 기대수익에 비해 과도할 것"
      ],
      "definition": "여기서 영구손실은 사업가치의 영구적 소멸을 뜻하며, 매수가 대비 가격 하락(valuation drawdown)은 포함하지 않는다. 가격 위험은 EV와 AS 점수가 이미 온전히 반영하므로 여기서 다시 세우면 중복이다.",
      "cleared_if": [
        "순현금이고 영업현금흐름이 차입을 상회하여 파산 확률이 사실상 0",
        "Bear 시나리오에서도 사업이 유의미한 owner FCF를 창출"
      ],
      "not_covered": "Bear 주당가치가 현재가를 크게 밑도는 것은 가격 위험이며 AS의 permanent_loss 점수가 반영한다."
    }
  }
}

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "thesis": "≤600자", "evidence": [{"evidence_id": "stable fact identifier", "economic_driver": "optional shared economic driver", "claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose"}
작성 후 `python harness.py validate META_REVIEW_20260921 ED`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
