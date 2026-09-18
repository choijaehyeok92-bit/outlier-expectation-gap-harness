# 과제: NVDA / 기준일 2026-09-17 / expectation_valuation (EV)
저장소: /home/user/outlier-expectation-gap-harness. 작성할 파일: runs/NVDA/reports/EV.json. 그 외 파일은 수정하지 않는다.
웹 검색·페치 예산: 최대 10회. 아래 기준 정보와 검증된 사실은 다시 검색하지 않는다.

## 기업 기준 정보 (재검증 금지)
{"ticker":"NVDA","company_name":"NVIDIA Corporation","as_of_date":"2026-09-17","currency":"USD","current_price":219.34,"shares_diluted":24285000000,"enterprise_value":5303450000000,"portfolio_context":{"existing_position_pct":0,"sector_exposure_pct":0},"known_sources":["SEC 10-Q filed 2026-08-26, period ended 2026-07-26 (FY27 Q2)","SEC 8-K / Exhibits 99.1 and 99.2 filed 2026-08-26","StockAnalysis / Investing.com price and valuation history, 2026-09-17 close observed 2026-09-18"],"special_questions":["At $219.34, does the current price require a Bull-case outcome?","How sensitive is value to terminal assumptions and AI-infrastructure demand normalization?"],"intake_facts":["FY27 Q2 (ended 2026-07-26) revenue $96.221B, +106% y/y; Data Center $89.0B, +117% y/y.","FY27 Q3 guidance: revenue $108B +/-2%, gross margin 74.0% +/-50bp, assumes zero China Data Center compute revenue.","H1 FY27 revenue $177.837B; H1 operating cash flow $74.421B; H1 NVIDIA-defined FCF $69.895B.","Balance sheet 2026-07-26: cash + marketable debt securities $56.586B, total debt $33.366B ($25B senior notes issued in Q2).","Diluted weighted-average shares 24.285B (Q2); shares outstanding 24.1B as of 2026-08-21.","Working capital: AR $63.059B (DSO 60 days vs 45 sequentially), inventory $31.575B.","Customer concentration: five direct customers were 22%, 14%, 13%, 11%, 10% of accounts receivable.","Commitments: $366B total future commitments, of which $279B supply/capacity.","China data-center compute shipments were <1% of Data Center revenue; the 10-Q describes effective foreclosure from that market under then-current rules.","Price 2026-09-17 close $219.34; market cap = 219.34 x 24.285B = $5,326.7B; net cash $23.22B; EV ~= $5,303.5B.","Trailing P/E ~27.7x and P/FCF ~41.7x at the 2026-09-17 close."],"net_cash_per_share":0.9635,"valuation_percentile_5y":0.05,"valuation_metric":"Trailing P/E (27.73x on 2026-09-17; near the low end of the last ~5 years of quarterly observations)","valuation_overrides":{"terminal_multiples":{}}}

## 검증된 1차 자료 사실
# NVDA verified source bundle — as of 2026-09-17

Reused verbatim (apart from the as-of header) from the frozen 2026-09-18 intake bundle so that
this run is model-comparable against the earlier gpt-5.6-sol run. Facts below are not to be re-searched.

## Primary filings
1. SEC Form 10-Q, filed 2026-08-26, quarter ended 2026-07-26
   https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm
   - Q2 revenue $96.221B; H1 revenue $177.837B.
   - Q2 diluted weighted-average shares 24.285B; shares outstanding 24.1B as of 2026-08-21.
   - Cash + marketable debt securities $56.586B; total debt $33.366B.
   - H1 operating cash flow $74.421B; AR $63.059B; inventory $31.575B.
   - China data-center compute shipments <1% of Data Center revenue; filing describes effective foreclosure from China's data-center compute market under then-current rules.
   - Five direct customers represented 22%, 14%, 13%, 11%, 10% of accounts receivable.
   - Future commitments $366B; supply/capacity commitments $279B.

2. SEC Form 8-K / Exhibit 99.1, filed 2026-08-26
   https://www.sec.gov/Archives/edgar/data/1045810/000104581026000073/q2fy27pr.htm
   - Q2 FY27 revenue $96.221B (+106% y/y), Data Center $89.0B (+117% y/y).
   - Q3 FY27 revenue guide $108B ±2%; gross-margin guide 74.0% ±50bp; no China Data Center compute revenue assumed.
   - H1 FY27 NVIDIA-defined FCF $69.895B; Q2 FCF $21.341B.

3. SEC Form 8-K / Exhibit 99.2 CFO commentary, filed 2026-08-26
   https://www.sec.gov/Archives/edgar/data/1045810/000104581026000073/q2fy27cfocommentary.htm
   - DSO 60 days vs 45 sequentially due to extended payment terms on large multi-quarter agreements.
   - Inventory $31.6B as NVIDIA prepared for Vera Rubin.
   - $25B senior notes issued in Q2.
   - Reiterates $366B total future commitments and $279B supply/capacity commitments.

## Secondary market data
4. StockAnalysis / Investing.com, 2026-09-17 close observed 2026-09-18
   https://stockanalysis.com/stocks/nvda/
   https://stockanalysis.com/stocks/nvda/financials/ratios/
   https://www.investing.com/equities/nvidia-corp-historical-data
   - NASDAQ close 2026-09-17: $219.34.
   - Trailing P/E ~27.7x; P/FCF ~41.7x.
   - Trailing P/E is near the low end of the displayed quarterly observations for roughly the prior five years; harness signal valuation_percentile_5y estimated at 0.05.

## Frozen modeling conventions
- net_cash_per_share = ($56.586B cash + marketable debt securities − $33.366B total debt) / 24.1B shares outstanding ≈ $0.9635.
- Marketable equity securities are excluded from net cash to avoid treating strategic/volatile equity holdings as operating cash.
- enterprise_value = $219.34 × 24.285B diluted shares − $23.22B net cash ≈ $5,303.5B (informational only; the harness does not score it).
- DCF policy: 9% required return, 10-year horizon, Bear/Base/Bull terminal multiples 15x/20x/25x (config/calibration.json defaults; no overrides set).
- revenue_cagr_next_3y is an EV-agent estimate, not management guidance.

## 독립성
runs/NVDA/reports/의 다른 에이전트 보고서는 읽지 않는다.

## 지침 EV (domain_analyst)
# Expectation & Valuation Analyst

- `agent_id`: `EV`
- `domain`: `expectation_valuation`

## 임무
현재가격이 요구하는 장기 기대를 역산하고(Reverse DCF), Bear/Base/Bull을 작성해 기대수익 범위와 기대차를 계산한다. 낙관적 가정·터미널가치 의존·피크 이익을 스스로 공격한다.

## 관점별 질문
**Verifier — Reverse DCF**
1. 현재 EV/시총이 정당화되려면 매출 CAGR·마진·ROIC가 얼마여야 하는가? 그 기대는 역사·경쟁·산업구조 대비 어느 수준인가?
2. WACC·영구성장률 변화에 얼마나 민감한가? 현재가격이 Bull Case 이상을 요구하는가?

**Bull — 시나리오**
1. Bear/Base/Bull 각각의 성장·마진·멀티플 가정과 5~10년 연환산 수익률은?
2. Base에서 완벽한 실행 없이도 기대수익이 충분한가? Bull은 신규 성장축을 어떻게 반영하는가?

**Skeptic — 기대차 공격**
1. Base가 사실상 Bull인가? 점유율·마진·멀티플을 동시에 낙관적으로 두었는가?
2. 기대수익의 대부분이 terminal multiple에 의존하는가? 피크 사이클 이익이나 투자손익을 정상 이익으로 쓰지 않았는가?

## 종목 유형 신호 (`archetype_signals`)
- `price_to_base_value` = 현재가 / Base 주당가치
- `valuation_percentile_5y` = 핵심 멀티플의 자기 5년 이력 대비 백분위(0=최저). 어떤 멀티플을 썼는지 `evidence`에 남긴다.
- `revenue_cagr_next_3y` = Base 3년 매출 CAGR (0.12 = 12%)

추정할 수 없으면 `null`로 둔다. `bull_score`/`bear_score`와 함께 Base·Bull·Bear 주당가치를 `evidence`에 기록한다. 저밸류에이션이 구조적 쇠퇴(밸류 트랩)에서 온 것은 아닌지 `counterevidence`에 적는다.

## Hard Veto 중점
- 현재가격이 비현실적인 Bull Case 이상을 요구

## 고정 채점 루브릭
{
  "global_bands": [
    {
      "min": 0,
      "max": 19,
      "label": "failed",
      "rule": "핵심 가설이 반증되거나 경제적 가치가 구조적으로 훼손"
    },
    {
      "min": 20,
      "max": 39,
      "label": "weak",
      "rule": "반대근거가 우세하고 장기 투자근거가 취약"
    },
    {
      "min": 40,
      "max": 59,
      "label": "mixed",
      "rule": "긍정·부정 근거가 혼재하며 우위가 입증되지 않음"
    },
    {
      "min": 60,
      "max": 74,
      "label": "adequate",
      "rule": "가설은 성립하지만 중요한 검증 공백이 존재"
    },
    {
      "min": 75,
      "max": 84,
      "label": "strong",
      "rule": "다수의 1차 자료가 장기 가설을 지지"
    },
    {
      "min": 85,
      "max": 94,
      "label": "exceptional",
      "rule": "여러 기간·지표에서 일관된 강한 증거"
    },
    {
      "min": 95,
      "max": 100,
      "label": "rare",
      "rule": "압도적이고 반증 위험이 매우 낮음; 극히 드물게 사용"
    }
  ],
  "domain": {
    "criteria": [
      {
        "id": "reverse_dcf_burden",
        "weight": 0.35,
        "question": "현재가격 내재 기대 현실성",
        "anchors": {
          "25": "Bull 이상 필요",
          "50": "강한 실행 필요",
          "75": "Base로 충분",
          "90": "보수 실행에도 충분"
        }
      },
      {
        "id": "base_return",
        "weight": 0.4,
        "question": "고정 DCF 정책의 Base 기대수익",
        "anchors": {
          "25": "큰 과대평가",
          "50": "공정가치 부근",
          "75": "의미 있는 할인",
          "90": "큰 기대차"
        }
      },
      {
        "id": "valuation_robustness",
        "weight": 0.25,
        "question": "terminal/피크이익 의존도",
        "anchors": {
          "25": "매우 취약",
          "50": "민감도 큼",
          "75": "여러 가정에서 유지",
          "90": "보수 민감도에서도 유지"
        }
      }
    ]
  }
}
criterion은 5점 단위로 채점한다. score_0_100은 subscores 고정 가중평균과 같아야 한다. self-confidence와 bull/bear 폭은 자동 감점하지 않는다.

## 필수 Hard Veto 판정
아래 항목은 생략하면 clear가 아니다. cleared|conditional|confirmed 중 하나를 기록한다. 근거 부족이면 candidate로 남겨 WATCH를 유발한다.
- 현재가격이 비현실적인 Bull Case 이상을 요구

## 결정론적 밸류에이션
{
  "policy": {
    "method": "owner_fcf_per_share_dcf",
    "horizon_years": 10,
    "required_return": 0.09,
    "terminal_multiples": {
      "bear": 15,
      "base": 20,
      "bull": 25
    },
    "rules": [
      "할인율·terminal multiple은 모델이 선택하지 않는다.",
      "회사별 override는 company_context.json에 freeze 전에 기록한다.",
      "현재가격·순현금은 frozen company_context 값만 사용한다.",
      "LLM은 Bear/Base/Bull의 연도별 owner FCF/share 경로만 추정한다."
    ]
  },
  "locked_context": {
    "current_price": 219.34,
    "net_cash_per_share": 0.9635,
    "valuation_percentile_5y": 0.05,
    "valuation_overrides": {
      "required_return": null,
      "terminal_multiples": {
        "bear": null,
        "base": null,
        "bull": null
      }
    }
  }
}
Bear/Base/Bull owner_fcf_per_share를 각각 정확히 10개 연도로 작성한다. 할인 계산과 price_to_base_value는 하네스가 수행한다.

## 공통 규칙
## 분석
- 기준일을 먼저 선언한다. 기준일 이후 정보는 사용하지 않는다.
- 최소 3개의 독립 근거를 확보하고, 가능한 한 1차 자료를 우선한다.
- 근거와 반대근거를 모두 제시한다.
- `사실 / 추정 / 해석`을 구분한다.
- 확인할 수 없는 데이터는 `unknown`으로 기록한다.
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
- 웹 검색·페치는 `config/workflow.json`의 `research_budget` 이내로 쓴다(기본 에이전트당 10회).
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

## 출력
agent_id/ticker/as_of_date/domain/role은 그대로 두고 아래 필드를 채운다. 분량 상한: thesis 600자, evidence 3~6개, counterevidence 4개, unknowns 5개(핵심 가설에 직결되는 것만), falsifiers·key_kpis·next_checks 각 3개. hard_veto_flags에는 상태가 none이 아닌 항목만 쓴다.
{"analysis_status": "complete", "score_0_100": 0, "confidence_0_1": 0, "bull_score": 0, "bear_score": 0, "bull_case": "≤300자", "bear_case": "≤300자", "thesis": "≤600자", "evidence": [{"claim": "", "source_type": "filing|ir|industry|secondary|other", "source": "URL 또는 파일 p.N", "period": "", "as_of_date": "", "value": null, "fact_or_estimate": "fact|estimate|interpretation"}], "counterevidence": [""], "unknowns": [""], "uncertainties": [], "falsifiers": [""], "hard_veto_flags": [{"veto": "현재가격이 비현실적인 Bull Case 이상을 요구", "status": "candidate", "rationale": "미평가 — cleared/conditional/confirmed 중 하나로 변경"}], "key_kpis": [{"name": "", "direction": "", "threshold": "", "cadence": ""}], "next_checks": [""], "verdict": "support|neutral|oppose", "subscores": [{"criterion_id": "reverse_dcf_burden", "score_0_100": 50, "rationale": ""}, {"criterion_id": "base_return", "score_0_100": 50, "rationale": ""}, {"criterion_id": "valuation_robustness", "score_0_100": 50, "rationale": ""}], "valuation_inputs": {"valuation_percentile_5y": null, "revenue_cagr_next_3y": null, "scenarios": {"bear": {"owner_fcf_per_share": []}, "base": {"owner_fcf_per_share": []}, "bull": {"owner_fcf_per_share": []}}}, "archetype_signals": {"price_to_base_value": null, "valuation_percentile_5y": null, "revenue_cagr_next_3y": null}}
작성 후 `python harness.py validate NVDA EV`로 검증한다.

최종 답변은 120단어 이내: 점수(bear–bull)·신뢰도·verdict·none이 아닌 Veto, 가장 중요한 미확인 사항 1개.
