#!/usr/bin/env bash
set -u
set -o pipefail

mkdir -p runlogs
exec > >(tee runlogs/continuation_phase3.log) 2>&1

echo "=== continue V phase 3 ==="
for A in ED RT; do
  echo "=== prompt $A ==="
  python harness.py prompt V "$A" --out "runs/V/${A}_prompt.md"
  echo "prompt_${A}_exit=$?"

  echo "=== response handoff $A ==="
  cp "automation_inputs/V_${A}.json" "runs/V/reports/${A}.json"

  echo "=== validate $A ==="
  python harness.py validate V "$A"
  echo "validate_${A}_exit=$?"
done

echo "=== aggregate after phase 3 ==="
python harness.py aggregate V | tee runlogs/aggregate_after_phase3.json
echo "aggregate_exit=${PIPESTATUS[0]}"

echo "=== digest after phase 3 ==="
python harness.py digest V
echo "digest_exit=$?"
cat runs/V/digest.md

echo "=== plan after phase 3 ==="
python harness.py plan V | tee runlogs/plan_after_phase3.txt
echo "plan_exit=${PIPESTATUS[0]}"
