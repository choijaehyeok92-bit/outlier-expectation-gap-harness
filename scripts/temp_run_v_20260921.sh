#!/usr/bin/env bash
set -u
set -o pipefail

mkdir -p runlogs
exec > >(tee runlogs/continuation_macro.log) 2>&1

echo "=== prompt MO ==="
python harness.py prompt V MO --out runs/V/MO_prompt.md
echo "prompt_MO_exit=$?"

echo "=== response handoff MO ==="
cp automation_inputs/V_MO.json runs/V/reports/MO.json

echo "=== validate MO ==="
python harness.py validate V MO
echo "validate_MO_exit=$?"

echo "=== aggregate after macro ==="
python harness.py aggregate V | tee runlogs/aggregate_after_macro.json
echo "aggregate_exit=${PIPESTATUS[0]}"

echo "=== digest after macro ==="
python harness.py digest V
echo "digest_exit=$?"
cat runs/V/digest.md

echo "=== plan after macro ==="
python harness.py plan V | tee runlogs/plan_after_macro.txt
echo "plan_exit=${PIPESTATUS[0]}"
