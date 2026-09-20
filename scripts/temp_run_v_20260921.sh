#!/usr/bin/env bash
set -u
set -o pipefail

mkdir -p runlogs
exec > >(tee runlogs/continuation_ic_final.log) 2>&1

echo "=== prompt IC ==="
python harness.py prompt V IC --out runs/V/IC_prompt.md
echo "prompt_IC_exit=$?"

echo "=== response handoff IC ==="
cp automation_inputs/V_IC.json runs/V/reports/IC.json

echo "=== validate IC ==="
python harness.py validate V IC
echo "validate_IC_exit=$?"

echo "=== validate all completed reports ==="
python harness.py validate V
echo "validate_all_exit=$?"

echo "=== aggregate final ==="
python harness.py aggregate V | tee runlogs/aggregate_final_v33.json
echo "aggregate_exit=${PIPESTATUS[0]}"

echo "=== digest final ==="
python harness.py digest V
echo "digest_exit=$?"

echo "=== plan final ==="
python harness.py plan V | tee runlogs/plan_final_v33.txt
echo "plan_exit=${PIPESTATUS[0]}"

echo "=== write one-page record ==="
cat > runs/V/one_page_investment_record.md <<'EOF'
# Visa (V) — One-page Investment Record

- As of: 2026-09-18
- Strategy / schema / decision policy: v3.3
- Primary archetype: Compounder
- Core score: 78.39
- Ex-valuation score: 83.31
- Hard Veto: CLEARED
- IC state: STARTER
- Position range: 1-2%
- Macro purchase pacing: 0.5x

## Thesis
Visa's network moat, customer value, reinvestment economics, management execution and financial survival clear the deterministic Compounder gates. The limiting factor is entry valuation and asymmetry, not franchise quality.

## Valuation
Frozen price $368.29 versus locked Bear/Base/Bull values of $133.34 / $328.59 / $467.20. Price/Base is 1.1208x.

## Main risks
Long-run routing/interchange regulation, alternative payment rails, client-incentive intensity, and paying above Base value.

## Increase evidence
Owner FCF/share tracks or exceeds Base, moat remains strong, Visa Direct/VAS economics strengthen, and refrozen price/Base improves.

## Falsifiers
Compounder thresholds fail, owner FCF/share persistently misses Base, or price/Base exceeds 1.2 without a higher refrozen intrinsic value.
EOF

echo "=== report / final verdict ==="
python harness.py report V
echo "report_exit=$?"

echo "=== final_verdict.json ==="
cat runs/V/final_verdict.json

echo "=== easy_report.md ==="
cat runs/V/easy_report.md
