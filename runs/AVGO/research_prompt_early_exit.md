# Research Orchestrator

Harness asks. Research retrieves. Verified evidence stays frozen. Domain reviewers decide.
각 질문은 existing_files부터 확인한다. 답이 있으면 웹 검색하지 않는다. 공백만 규제 공시 → IR → 공식 산업자료 → 2차 자료 순서로 검색한다.
evidence_available_for_review는 research/result-*.json에 답이 이미 수용되어 reviewer 검토가 필요한 질문이다. 같은 질문을 다시 검색하지 않는다.
publication_date와 period를 구분하고 마감일 이후 자료는 excluded_post_cutoff로 분리한다. 검색하지 않은 내용을 보충하지 않는다.
fact / estimate / interpretation을 분리한다. 계산값·maintenance capex·경제적 ROIC는 직접 공시가 아니면 fact가 아니다.
수치 비교는 verified_fact_refs에 normalized:FACT-ID 또는 context:key를 기록한다. README 주장 비교는 readme:원문 구절을 사용한다.
충돌은 verified_value/new_value/possible_reason 및 requires_refreeze로 기록한다. 수정공시도 원본을 덮어쓰지 않는다.
동일 사실은 같은 evidence_id/economic_driver, 동일 원 보도자료는 같은 source_origin을 유지한다.
Hard Veto 지지·반박 evidence ID와 remaining_unknowns만 제공한다. 점수·등급·veto 판정·포지션은 작성하지 않는다.
경제적 조정은 possible_adjustment로만 표시한다. 충분한 답을 얻으면 검색을 멈춘다.
resolved는 충분한 증거, partial은 일부 증거, unresolved는 합리적 검색 후 미확보다. search_log에 실제 조회 경로와 결과를 기록한다.
출력 계약: schemas/research_packet.schema.json. 모든 새 evidence에 공개일·대상기간·마감일 적격성을 기록한다.

{
  "schema_version": "1.0",
  "ticker": "AVGO",
  "as_of_date": "2026-09-18",
  "inputs": [
    {
      "path": "company_context.json",
      "exists": true,
      "sha256": "08ce0a61f4ed57c31a5051574c301a33276377022fdd6c4cc7d562a1afe4307f"
    },
    {
      "path": "run_manifest.json",
      "exists": true,
      "sha256": "f6f4ea1a0f1e625e7757b36ba8648bce73df7fe1ff623b55ff0d4d6750f3529c"
    },
    {
      "path": "sources/README.md",
      "exists": false,
      "sha256": null
    },
    {
      "path": "sources/financials/normalized_financials.json",
      "exists": true,
      "sha256": "e0339615dcc272fa8f83031dc995ad1e0479ecbdf44e7c9275e2ad694542dfd0"
    },
    {
      "path": "sources/financials/derived_metrics.json",
      "exists": false,
      "sha256": null
    },
    {
      "path": "sources/financials/adjustment_candidates.json",
      "exists": false,
      "sha256": null
    },
    {
      "path": "sources/financials/qa_report.json",
      "exists": false,
      "sha256": null
    },
    {
      "path": "reports/AS.json",
      "exists": true,
      "sha256": "ebd5588994e9732bfe7c6bf716ab23c4d649610a695d8a424b8db3a575d5314b"
    },
    {
      "path": "reports/DI.json",
      "exists": true,
      "sha256": "15eafd95f97687918e5874f55bf929e581214c54884ecb7879b988eaa074c6b9"
    },
    {
      "path": "reports/EV.json",
      "exists": true,
      "sha256": "7e41d1d53b30ca8c4e0f6364402a19da66bd5af5f9aec6433aeafe4eb88794c5"
    },
    {
      "path": "reports/FS.json",
      "exists": true,
      "sha256": "2789770c9b2c9f85464e502b1f134cff40ed4ddc236b839eec27b9ae2b66891a"
    },
    {
      "path": "digest.md",
      "exists": true,
      "sha256": "e7713a0564d113745adb8c1d20e365a62092b7871a91d6bd01fb841498179b46"
    },
    {
      "path": "aggregate.json",
      "exists": true,
      "sha256": "749dc7263ed09144f1f4e46c23b16f0be368619bdb0a5fe637ebb99c1bc958b3"
    }
  ],
  "input_snapshot_sha256": "c78f8129703115d4f9b154161cb1dc65764a6988507b1fb8413660712b7a2d05",
  "harness_plan": {
    "stage": "early_exit",
    "agents": {},
    "early_exit_record": {
      "stage": "triage",
      "last_reachable_archetypes": [
        "growth"
      ],
      "reachability_history_method": "Deterministic replay in manifest order; not a claim about wall-clock execution order.",
      "eliminated_archetypes": {
        "compounder": {
          "failed_conditions": [
            {
              "field": "domain.financial_survival",
              "op": ">=",
              "value": 72,
              "fit_weight": 1.0
            }
          ],
          "missing_conditions": [
            "domain.moat_trajectory",
            "domain.reinvestment_fcf",
            "domain.management_allocation",
            "criterion.reinvestment_fcf.incremental_roic",
            "criterion.reinvestment_fcf.reinvestment_runway"
          ],
          "gate_failed": false,
          "blocking_vetoes": []
        },
        "growth": {
          "failed_conditions": [
            {
              "field": "domain.asymmetry",
              "op": ">=",
              "value": 65,
              "fit_weight": 1.0
            }
          ],
          "missing_conditions": [
            "domain.structural_leadership",
            "domain.customer_product",
            "domain.moat_trajectory",
            "domain.reinvestment_fcf",
            "domain.management_allocation",
            "criterion.reinvestment_fcf.fcf_per_share_quality"
          ],
          "gate_failed": true,
          "blocking_vetoes": []
        },
        "buffett_value": {
          "failed_conditions": [
            {
              "field": "signal.price_to_base_value",
              "op": "<=",
              "value": 0.85,
              "fit_weight": 1.0
            },
            {
              "field": "domain.financial_survival",
              "op": ">=",
              "value": 75,
              "fit_weight": 1.0
            },
            {
              "field": "domain.asymmetry",
              "op": ">=",
              "value": 65,
              "fit_weight": 1.0
            }
          ],
          "missing_conditions": [
            "criterion.reinvestment_fcf.fcf_per_share_quality",
            "domain.management_allocation",
            "domain.moat_trajectory"
          ],
          "gate_failed": false,
          "blocking_vetoes": []
        },
        "moonshot": {
          "failed_conditions": [
            {
              "field": "signal.market_cap_usd",
              "op": "<=",
              "value": 50000000000,
              "fit_weight": 1.0
            },
            {
              "field": "domain.disruptive_innovation",
              "op": ">=",
              "value": 78,
              "fit_weight": 1.0
            },
            {
              "field": "domain.asymmetry",
              "op": ">=",
              "value": 72,
              "fit_weight": 1.0
            }
          ],
          "missing_conditions": [
            "domain.structural_leadership"
          ],
          "gate_failed": false,
          "blocking_vetoes": []
        }
      },
      "confirmed_vetoes": [],
      "unresolved_vetoes": [],
      "pending_vetoes": [
        {
          "veto": "경영진 정직성 또는 회계 신뢰성 훼손",
          "status": "PENDING_REVIEW",
          "owners": [
            "MA",
            "RT"
          ],
          "assessments": [],
          "missing_reports": [
            "MA",
            "RT"
          ],
          "missing_assessments": []
        },
        {
          "veto": "구조적으로 과도한 외부자본 조달 의존",
          "status": "PENDING_REVIEW",
          "owners": [
            "FS",
            "RT"
          ],
          "assessments": [
            {
              "agent_id": "FS",
              "owner": true,
              "status": "cleared",
              "rationale": "Broadcom's own operations generate cash far above ordinary capex and near-term debt maturities, so the company does not require repeated external financing to operate. XPV financing supports customers and is routed to off-balance risk rather than this veto."
            }
          ],
          "missing_reports": [
            "RT"
          ],
          "missing_assessments": []
        },
        {
          "veto": "장기간 지속되는 과도한 희석",
          "status": "PENDING_REVIEW",
          "owners": [
            "RF",
            "FS"
          ],
          "assessments": [
            {
              "agent_id": "FS",
              "owner": true,
              "status": "cleared",
              "rationale": "Q3 diluted shares increased only about 0.56% y/y while Broadcom repurchased $8.45B of stock in 9M. The 'excessive' element is not supported even though SBC remains material."
            }
          ],
          "missing_reports": [
            "RF"
          ],
          "missing_assessments": []
        },
        {
          "veto": "고객가치 없이 마케팅·보조금에 의존하는 성장",
          "status": "PENDING_REVIEW",
          "owners": [
            "CP",
            "RT"
          ],
          "assessments": [],
          "missing_reports": [
            "CP",
            "RT"
          ],
          "missing_assessments": []
        },
        {
          "veto": "증분 ROIC의 구조적 붕괴",
          "status": "PENDING_REVIEW",
          "owners": [
            "RF",
            "RT"
          ],
          "assessments": [],
          "missing_reports": [
            "RF",
            "RT"
          ],
          "missing_assessments": []
        },
        {
          "veto": "해자의 지속적인 축소",
          "status": "PENDING_REVIEW",
          "owners": [
            "MT",
            "RT"
          ],
          "assessments": [],
          "missing_reports": [
            "MT",
            "RT"
          ],
          "missing_assessments": []
        },
        {
          "veto": "현재가격이 비현실적인 Bull Case 이상을 요구",
          "status": "PENDING_REVIEW",
          "owners": [
            "EV",
            "AS",
            "RT"
          ],
          "assessments": [
            {
              "agent_id": "AS",
              "owner": true,
              "status": "cleared",
              "rationale": "Frozen price $357.61 is far below locked Bull value $797.84; the veto's sole element is not met."
            },
            {
              "agent_id": "EV",
              "owner": true,
              "status": "cleared",
              "rationale": "Frozen price $357.61 is below locked-policy Bull value $797.84 and equals only 0.884x Base $404.48. The defined veto requires current price to exceed Bull value, which is not satisfied."
            }
          ],
          "missing_reports": [
            "RT"
          ],
          "missing_assessments": []
        },
        {
          "veto": "단일 제품·단일 고객·단일 규제에 대한 치명적 종속성",
          "status": "PENDING_REVIEW",
          "owners": [
            "CP",
            "RT"
          ],
          "assessments": [],
          "missing_reports": [
            "CP",
            "RT"
          ],
          "missing_assessments": []
        }
      ],
      "future_reentry": {
        "required_conditions": {
          "compounder": {
            "failed_conditions": [
              {
                "field": "domain.financial_survival",
                "op": ">=",
                "value": 72,
                "fit_weight": 1.0
              }
            ],
            "missing_conditions": [
              "domain.moat_trajectory",
              "domain.reinvestment_fcf",
              "domain.management_allocation",
              "criterion.reinvestment_fcf.incremental_roic",
              "criterion.reinvestment_fcf.reinvestment_runway"
            ],
            "gate_failed": false,
            "blocking_vetoes": []
          },
          "growth": {
            "failed_conditions": [
              {
                "field": "domain.asymmetry",
                "op": ">=",
                "value": 65,
                "fit_weight": 1.0
              }
            ],
            "missing_conditions": [
              "domain.structural_leadership",
              "domain.customer_product",
              "domain.moat_trajectory",
              "domain.reinvestment_fcf",
              "domain.management_allocation",
              "criterion.reinvestment_fcf.fcf_per_share_quality"
            ],
            "gate_failed": true,
            "blocking_vetoes": []
          },
          "buffett_value": {
            "failed_conditions": [
              {
                "field": "signal.price_to_base_value",
                "op": "<=",
                "value": 0.85,
                "fit_weight": 1.0
              },
              {
                "field": "domain.financial_survival",
                "op": ">=",
                "value": 75,
                "fit_weight": 1.0
              },
              {
                "field": "domain.asymmetry",
                "op": ">=",
                "value": 65,
                "fit_weight": 1.0
              }
            ],
            "missing_conditions": [
              "criterion.reinvestment_fcf.fcf_per_share_quality",
              "domain.management_allocation",
              "domain.moat_trajectory"
            ],
            "gate_failed": false,
            "blocking_vetoes": []
          },
          "moonshot": {
            "failed_conditions": [
              {
                "field": "signal.market_cap_usd",
                "op": "<=",
                "value": 50000000000,
                "fit_weight": 1.0
              },
              {
                "field": "domain.disruptive_innovation",
                "op": ">=",
                "value": 78,
                "fit_weight": 1.0
              },
              {
                "field": "domain.asymmetry",
                "op": ">=",
                "value": 72,
                "fit_weight": 1.0
              }
            ],
            "missing_conditions": [
              "domain.structural_leadership"
            ],
            "gate_failed": false,
            "blocking_vetoes": []
          }
        },
        "requirements": [
          "New evidence must satisfy all gates for at least one archetype.",
          "Complete core coverage, deterministic valuation and all veto ownership before any buy."
        ]
      },
      "ic_intentionally_not_run": true,
      "statement": "IC was intentionally not run because no investable archetype remains reachable."
    },
    "stage_0": {
      "stage_0": "ready",
      "enforced": true,
      "pack_present": true,
      "advisory_gaps": [
        "historical_annuals",
        "earnings_release",
        "insider_ownership",
        "investor_materials"
      ]
    }
  },
  "questions": [
    {
      "research_question_id": "RQ-RF-4CDA2DE093",
      "question": "criterion.reinvestment_fcf.fcf_per_share_quality 평가에 필요한 누락 관측값은 무엇인가?",
      "agent_id": "RF",
      "domain": "reinvestment_fcf",
      "triggers": [
        "missing_observable"
      ],
      "priority": 1,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-RF-76E6A7CC08",
      "question": "criterion.reinvestment_fcf.incremental_roic 평가에 필요한 누락 관측값은 무엇인가?",
      "agent_id": "RF",
      "domain": "reinvestment_fcf",
      "triggers": [
        "missing_observable"
      ],
      "priority": 1,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-RF-D323B05CAF",
      "question": "criterion.reinvestment_fcf.reinvestment_runway 평가에 필요한 누락 관측값은 무엇인가?",
      "agent_id": "RF",
      "domain": "reinvestment_fcf",
      "triggers": [
        "missing_observable"
      ],
      "priority": 1,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-AS-262A7C280A",
      "question": "The probability and funding mechanics of up to $42B of conditional customer convertible notes are not quantified.",
      "agent_id": "AS",
      "domain": "asymmetry",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-AS-2F4788EE27",
      "question": "Recompute Bear/current and Bull/current after FY2027 guidance and any backstop funding.",
      "agent_id": "AS",
      "domain": "asymmetry",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-AS-875F8C9985",
      "question": "Quantify the customer and contract split of AI RPO and XPV-supported deployments.",
      "agent_id": "AS",
      "domain": "asymmetry",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-AS-C431FFF54A",
      "question": "How much of the $179.2B RPO is cancellable, low-margin or tied to AI XPV-supported deployments is not separately disclosed.",
      "agent_id": "AS",
      "domain": "asymmetry",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-AS-E0789591AF",
      "question": "No empirical comparable-company base-rate dataset was available before the cutoff for assigning objective Bear/Base/Bull probabilities.",
      "agent_id": "AS",
      "domain": "asymmetry",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-AS-E34D29684E",
      "question": "Build a comparable-company base-rate table before assigning explicit scenario probabilities.",
      "agent_id": "AS",
      "domain": "asymmetry",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-AS-FBE26FBE0E",
      "question": "Economic terms and customer identities behind the largest custom-AI contracts remain undisclosed.",
      "agent_id": "AS",
      "domain": "asymmetry",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-DI-1ED3D033B8",
      "question": "Verify whether VMware/private-AI software becomes a measurable attach revenue stream to AI infrastructure.",
      "agent_id": "DI",
      "domain": "disruptive_innovation",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-DI-3EEC746289",
      "question": "Track customer diversification and accelerator/networking mix separately.",
      "agent_id": "DI",
      "domain": "disruptive_innovation",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-DI-43181C0261",
      "question": "Long-run software attach or private-AI monetization to custom AI silicon deployments is not quantified.",
      "agent_id": "DI",
      "domain": "disruptive_innovation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-DI-84F53E841F",
      "question": "The share of AI revenue attributable to accelerators versus networking is not separately disclosed.",
      "agent_id": "DI",
      "domain": "disruptive_innovation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-DI-B8422C2231",
      "question": "Obtain independent Jalapeño/XPU benchmark and TCO evidence when published.",
      "agent_id": "DI",
      "domain": "disruptive_innovation",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-DI-D225F92CD0",
      "question": "Per-customer XPU gross margin and lifetime economics are undisclosed.",
      "agent_id": "DI",
      "domain": "disruptive_innovation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-DI-F75ECBFFFE",
      "question": "Independent third-party benchmark data for Jalapeño performance, total cost of ownership and utilization was unavailable before the cutoff.",
      "agent_id": "DI",
      "domain": "disruptive_innovation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-EV-12DD0FF427",
      "question": "Reconcile VMware software cash conversion and acquisition-amortization treatment in RF before using EV as a portfolio-sizing input.",
      "agent_id": "EV",
      "domain": "expectation_valuation",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-EV-2572FD6D9F",
      "question": "How much of the $179.2B RPO is custom AI silicon versus software, and its recognition/margin profile beyond the next 12 months.",
      "agent_id": "EV",
      "domain": "expectation_valuation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-EV-563DC09723",
      "question": "Separate custom-AI RPO, customer concentration and gross-margin evolution in the next 10-Q.",
      "agent_id": "EV",
      "domain": "expectation_valuation",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-EV-71849D3A44",
      "question": "Long-run share of hyperscaler accelerator spend won by Broadcom versus internally designed or competing custom silicon.",
      "agent_id": "EV",
      "domain": "expectation_valuation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-EV-B44262CAD3",
      "question": "Update the Base revenue path when FY2027 company guidance is available; do not substitute external consensus for company evidence.",
      "agent_id": "EV",
      "domain": "expectation_valuation",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-EV-C8ACAB2393",
      "question": "Individual revenue shares, contract economics and cancellation/volume-flex terms for the largest custom AI accelerator customers.",
      "agent_id": "EV",
      "domain": "expectation_valuation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-EV-E6F65C2C92",
      "question": "Sustainable owner-FCF margin after the current AI capacity buildout and VMware integration matures.",
      "agent_id": "EV",
      "domain": "expectation_valuation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-EV-F57C7A8AA2",
      "question": "No frozen 5-year valuation percentile is available; EV relies on the locked DCF rather than a historical percentile signal.",
      "agent_id": "EV",
      "domain": "expectation_valuation",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-FS-19ED20D455",
      "question": "The fraction of $126.8B purchase commitments matched to non-cancellable customer RPO is not disclosed.",
      "agent_id": "FS",
      "domain": "financial_survival",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-FS-5D8AC2B4EF",
      "question": "The binding funding obligation, if any, associated with the up-to-$42B customer convertible-note capacity is unclear.",
      "agent_id": "FS",
      "domain": "financial_survival",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-FS-68CE89B3FF",
      "question": "Track actual XPV backstop funding, customer-note issuance and recoveries separately from headline AI revenue.",
      "agent_id": "FS",
      "domain": "financial_survival",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-FS-79670809C0",
      "question": "Debt maturity detail beyond the next 12 months was not reconstructed into a year-by-year stress table in this pass.",
      "agent_id": "FS",
      "domain": "financial_survival",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-FS-83F6C2F2AB",
      "question": "Adjust cash-conversion analysis for receivables factoring and working-capital timing.",
      "agent_id": "FS",
      "domain": "financial_survival",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-FS-96769F3647",
      "question": "The probability-weighted loss distribution and phase-by-phase funded amount of the $29B backstop are not disclosed.",
      "agent_id": "FS",
      "domain": "financial_survival",
      "triggers": [
        "unknowns"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    },
    {
      "research_question_id": "RQ-FS-CC46F2B250",
      "question": "Reconstruct debt maturities and fixed/floating interest burden by fiscal year.",
      "agent_id": "FS",
      "domain": "financial_survival",
      "triggers": [
        "next_checks"
      ],
      "priority": 2,
      "search_order": [
        "existing_files",
        "regulatory_filings",
        "company_ir",
        "official_industry",
        "secondary"
      ],
      "status": "pending"
    }
  ]
}

