# 과제: 000660 / 기준일 2026-09-17 / evidence_quality (ED)
저장소: /home/runner/work/outlier-expectation-gap-harness/outlier-expectation-gap-harness. 작성할 파일: runs/000660/reports/ED.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 15회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.
자료 공백은 수동적으로 남기지 않는다. 점수·Veto·밸류에이션에 직접 영향을 주는 항목이 기준 정보와 1차 자료에 없으면 예산 내에서 웹 검색·IR·2차 자료로 보완을 시도한 뒤, 그래도 확보하지 못한 것만 unknowns에 남기고 무엇을 어디서 찾으려 했는지 함께 적는다. 확보한 자료는 evidence에 source_type과 함께 기록하고 EVIDENCE_POLICY.md의 출처 위계를 지킨다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"000660","company_name":"SK hynix Inc.","as_of_date":"2026-09-17","currency":"KRW","current_price":1745000,"shares_diluted":711075500,"market_cap_usd":899019524344.3,"enterprise_value":1171455458500000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["User-uploaded SK hynix FY2025 annual report filed 2026-03-17","User-uploaded SK hynix H1 2026 half-year report filed 2026-08-14","2026-09-17 closing price KRW 1,745,000 verified from historical market data","2026-09-17 USD/KRW 1,380.2 used only to translate market cap for archetype cap"],"special_questions":["How durable are HBM-led margins and cash flow once supply expands and the memory cycle normalizes?","Does AI/HBM structural demand offset traditional DRAM/NAND cyclicality enough to justify a Compounder classification?","How much of the 2026 H1 extraordinary earnings and financial income should be excluded from normalized owner FCF?"],"net_cash_per_share":97558.2607,"valuation_metric":"No reproducible 5-year valuation percentile frozen; valuation is handled by the locked owner-FCF/share DCF.","valuation_overrides":{"terminal_multiples":{}}}

## 검증된 1차 자료 사실
# 000660 frozen source bundle — as of 2026-09-17

Primary evidence:
- SK hynix FY2025 annual report, filed 2026-03-17.
- SK hynix H1 2026 half-year report, filed 2026-08-14.
- 2026-09-17 close: KRW 1,745,000 (StockAnalysis / Investing historical data).
- USD/KRW 1,380.2 on 2026-09-17 for USD market-cap translation only.

## H1 2026 key financials
- Revenue: KRW 131.895T.
- Operating profit: KRW 98.153T.
- Net income: KRW 134.269T.
- Operating cash flow: KRW 91.743T.
- Purchases of PP&E: KRW 18.329T.
- Cash and cash equivalents: KRW 26.836T.
- Short-term financial instruments: KRW 22.398T.
- Short-term investments: KRW 38.724T.
- Current + long-term borrowings: KRW 18.587T.
- Frozen liquid net cash: KRW 69.371T.
- Shares outstanding / circulating shares: 711.0755M.
- Frozen net cash per share: KRW 97,558.

## H1 2026 business mix
- DRAM revenue: KRW 97.641T.
- NAND Flash revenue: KRW 33.534T.
- Other: KRW 0.720T.
- Q2 revenue: KRW 79.319T.
- Q2 operating profit: KRW 60.543T.
- H1 2025 revenue / operating profit: KRW 39.871T / KRW 16.653T.
- 2026 milestones disclosed in the half-year report include SOCAMM2 192GB mass production, iHBM technology disclosure, and HBM4E 12-high sample supply.
- Company states AI-agent commercialization should support continuing data-center and server memory demand growth.

## Capital / balance sheet
- H1 2026 debt/equity is materially stronger than year-end 2025.
- Domestic ratings AA+; Moody's upgraded to A3 on 2026-08-03; S&P and Fitch BBB+.
- 15.3M treasury shares were retired in February 2026; circulating shares increased to 711.1M after treasury-stock transactions but the issued share count fell.
- Major borrowing covenants were in compliance at H1 end.

## Valuation policy
- Required return: 9%.
- Horizon: 10 years.
- Terminal multiples: 15x / 20x / 25x.
- Owner-FCF/share paths (KRW):
  - Bear: 90k, 80k, 75k, 80k, 85k, 90k, 95k, 100k, 105k, 110k.
  - Base: 160k, 175k, 190k, 205k, 220k, 235k, 250k, 265k, 280k, 295k.
  - Bull: 190k, 220k, 250k, 285k, 320k, 355k, 390k, 425k, 460k, 500k.
- Locked DCF values: Bear ~KRW 1.365M, Base ~KRW 3.982M, Bull ~KRW 7.401M.
- price/Base ~0.438.

공시 원문: runs/000660/sources/*.txt — runs/000660/sources/INDEX.md의 섹션 줄번호로 grep·부분 읽기만 한다.

## 입력
runs/000660/digest.md (없으면 `python harness.py aggregate 000660` 후 `digest 000660` 실행). 다른 에이전트의 원 보고서는 특정 주장을 검증할 때만 해당 파일 하나를 연다.

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
- 작성 후 `python harness.py validate <TICKER> <AGENT_ID>`로 검증한다. 스키마 파일을 직접 읽지 않아도 된다.

## 재현성
- agent 실행 전 `python harness.py freeze TICKER --provider ... --model ...`로 company_context와 sources를 해시 고정한다.
- freeze 이후 입력이 바뀌면 prompt 생성을 중단한다. 모델 비교는 동일 `input_snapshot_sha256`에서만 유효하다.
- EV는 고정된 할인율·terminal multiple·현재가격·순현금을 사용하며 LLM은 연도별 owner FCF/share 경로만 제안한다.

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
      "elements": [
        "희석이 장기간 지속될 것",
        "그 폭이 과도할 것"
      ],
      "cleared_if": [
        "희석주식수가 보합 또는 감소",
        "자사주 매입이 SBC를 상쇄"
      ],
      "not_covered": "SBC 존재 자체는 요건이 아니다."
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
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "thesis": "≤600자", "evidence": [{"claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose"}
작성 후 `python harness.py validate 000660 ED`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
