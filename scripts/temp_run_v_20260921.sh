#!/usr/bin/env bash
set -u
set -o pipefail

mkdir -p runlogs
exec > >(tee runlogs/continuation_domain.log) 2>&1

echo "=== continue V domain analysis ==="
for A in CP MA MT RF SL; do
  echo "=== prompt $A ==="
  python harness.py prompt V "$A" --out "runs/V/${A}_prompt.md"
  echo "prompt_${A}_exit=$?"

  echo "=== response handoff $A ==="
  cp "automation_inputs/V_${A}.json" "runs/V/reports/${A}.json"

  echo "=== validate $A ==="
  python harness.py validate V "$A"
  echo "validate_${A}_exit=$?"
done

echo "=== aggregate after domain analysis ==="
python harness.py aggregate V | tee runlogs/aggregate_after_domain.json
echo "aggregate_exit=${PIPESTATUS[0]}"

echo "=== digest after domain analysis ==="
python harness.py digest V
echo "digest_exit=$?"
cat runs/V/digest.md

echo "=== plan after domain analysis ==="
python harness.py plan V | tee runlogs/plan_after_domain.txt
echo "plan_exit=${PIPESTATUS[0]}"
