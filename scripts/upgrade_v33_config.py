#!/usr/bin/env python3
"""Upgrade executable policy/config metadata from v3.2 to v3.3.

Run AFTER the v3.3 code change. The script is idempotent and never touches
runs/**: it rewrites config only, and every rule it depends on is asserted
before anything is written, so a config it cannot upgrade safely is left alone.

What it changes:
  * strategy version markers -> 3.3
  * archetype ranking -> `fit_axes`, with `fit_weight` removed from the
    eligibility conditions so a detailed gate list cannot outvote a terse one
  * a research question budget that can only ever defer non-blocking questions
  * deterministic DCF sanity thresholds

What it deliberately does not change: eligibility thresholds, core score
weights, state bands, Hard Veto definitions and ownership.
"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def dump(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")


# Each axis must name one of that archetype's own eligibility conditions, and the
# weights say what the archetype IS, not how many gates happen to mention it.
FIT_AXES = {
    "compounder": [
        {"field": "domain.moat_trajectory", "weight": 0.30},
        {"field": "criterion.reinvestment_fcf.incremental_roic", "weight": 0.30},
        {"field": "criterion.reinvestment_fcf.reinvestment_runway", "weight": 0.25},
        {"field": "domain.management_allocation", "weight": 0.15},
    ],
    "outlier_growth": [
        {"field": "domain.long_term_growth", "weight": 0.35},
        {"field": "domain.moat_trajectory", "weight": 0.20},
        {"field": "domain.customer_product", "weight": 0.15},
        {"field": "criterion.asymmetry.upside_path", "weight": 0.20},
        {"field": "domain.management_allocation", "weight": 0.10},
    ],
    "growth": [
        {"field": "signal.revenue_cagr_next_3y", "weight": 0.20,
         "normalization": {"kind": "linear", "min": 0.10, "max": 0.30, "direction": "higher"}},
        {"field": "domain.customer_product", "weight": 0.25},
        {"field": "domain.structural_leadership", "weight": 0.20},
        {"field": "domain.reinvestment_fcf", "weight": 0.20},
        {"field": "domain.moat_trajectory", "weight": 0.15},
    ],
    "buffett_value": [
        {"field": "criterion.reinvestment_fcf.fcf_per_share_quality", "weight": 0.30},
        {"field": "domain.financial_survival", "weight": 0.25},
        {"field": "domain.management_allocation", "weight": 0.20},
        {"field": "domain.moat_trajectory", "weight": 0.15},
        {"field": "domain.asymmetry", "weight": 0.10},
    ],
    "moonshot": [
        {"field": "domain.disruptive_innovation", "weight": 0.40},
        {"field": "domain.asymmetry", "weight": 0.25},
        {"field": "domain.structural_leadership", "weight": 0.20},
        {"field": "domain.financial_survival", "weight": 0.15},
    ],
}

FIT_NOTE = ("Eligibility conditions are mandatory gates. Ranking among eligible archetypes uses "
            "fit_axes only, so the number of gates an archetype declares cannot give it extra votes. "
            "Score fields normalize as value/100; other fields declare an explicit normalization. "
            "A missing axis contributes zero to fit and never relaxes a gate.")

RESEARCH_POLICY = {
    "trigger_classes": {
        "hard_veto": "decision_blocking",
        "missing_observable": "decision_blocking",
        "missing_valuation_input": "decision_blocking",
        "valuation_sanity_blocking": "decision_blocking",
        "structural_geopolitical_event": "decision_blocking",
        "unknowns": "thesis_monitor",
        "valuation_sanity_review": "thesis_monitor",
        "next_checks": "optional",
    },
    "question_budget": {
        "max_active_questions": 24,
        "max_monitoring_questions": 12,
        "max_optional_questions": 4,
        "max_nonblocking_per_domain": 4,
        "note": ("예산은 비차단 질문에만 적용한다. decision_blocking 질문은 cap을 넘겨도 숨기지 않으며 "
                 "blocking_overflow로 기록한다. 보류된 질문은 deferred_questions에 이유와 함께 남는다."),
    },
}

SANITY_POLICY = {
    "yearly_scenario_crossing": "review",
    "terminal_fraction_review": 0.80,
    "terminal_fraction_high": 0.90,
    "price_above_bull_review": True,
    "note": ("연도별 Bear/Base/Bull 경로 교차는 재투자 가정 차이로 정당할 수 있어 REVIEW다. "
             "최종 내재가치 순서 위반만 blocking이다. terminal 집중도와 price > Bull은 review 신호이며 "
             "기존 Hard Veto를 자동으로 confirmed 처리하지 않는다. 판정은 지정 owner가 한다."),
}


def upgrade_strategy():
    path = "config/strategy.json"
    s = load(path)
    prior = str(s.get("strategy_version"))
    if prior not in {"3.2", "3.3"}:
        raise SystemExit(f"Expected strategy_version 3.2/3.3, got {prior}")
    s["name"] = "Long Outlier Expectation Gap Strategy v3.3"
    for key in ("strategy_version", "schema_version", "decision_policy_version"):
        s[key] = "3.3"

    by_id = {row["id"]: row for row in s["archetypes"]["types"]}
    if set(by_id) != set(FIT_AXES):
        raise SystemExit(f"Unexpected archetype set: {sorted(by_id)}")
    for aid, axes in FIT_AXES.items():
        t = by_id[aid]
        condition_fields = {c["field"] for c in t["conditions"]}
        for c in t["conditions"]:
            c.pop("fit_weight", None)
        missing = {a["field"] for a in axes} - condition_fields
        if missing:
            raise SystemExit(f"{aid}: fit axes not backed by eligibility gates: {sorted(missing)}")
        if abs(sum(a["weight"] for a in axes) - 1.0) > 1e-12:
            raise SystemExit(f"{aid}: fit-axis weights must sum to 1")
        t["fit_axes"] = json.loads(json.dumps(axes))

    fp = s["archetypes"]["fit_policy"]
    fp["method"] = "weighted_fit_axes"
    fp["note"] = FIT_NOTE
    if sorted(fp["tie_breaker"]) != sorted(by_id):
        raise SystemExit("Tie-breaker must name each investable archetype exactly once")
    dump(path, s)
    return path


def upgrade_workflow():
    path = "config/workflow.json"
    w = load(path)
    policy = w["execution"].setdefault("research_policy", {})
    policy.update(RESEARCH_POLICY)
    dump(path, w)
    return path


def upgrade_calibration():
    path = "config/calibration.json"
    c = load(path)
    c["valuation"]["sanity_policy"] = SANITY_POLICY
    dump(path, c)
    return path


def main():
    for path in (upgrade_strategy(), upgrade_workflow(), upgrade_calibration()):
        print(f"upgraded {path}")
    print("runs/** untouched; thresholds, weights, state bands and Hard Vetoes unchanged")


if __name__ == "__main__":
    main()
