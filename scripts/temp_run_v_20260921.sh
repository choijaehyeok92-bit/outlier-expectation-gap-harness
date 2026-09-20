#!/usr/bin/env bash
set -u
set -o pipefail

mkdir -p runlogs
exec > >(tee runlogs/continuation_triage.log) 2>&1

echo "=== continue frozen V run ==="
python - <<'PY'
import json
from pathlib import Path
m=json.loads(Path("runs/V/run_manifest.json").read_text())
print(json.dumps({
  "ticker":m.get("ticker"),
  "as_of_date":m.get("as_of_date"),
  "frozen":m.get("frozen"),
  "strategy_version":m.get("strategy_version"),
  "input_snapshot_sha256":m.get("input_snapshot_sha256"),
  "runner":m.get("runner")
},ensure_ascii=False,indent=2))
PY

for A in AS DI FS; do
  echo "=== prompt $A ==="
  python harness.py prompt V "$A" --out "runs/V/${A}_prompt.md"
  echo "prompt_${A}_exit=$?"

  echo "=== response handoff $A ==="
  cp "automation_inputs/V_${A}.json" "runs/V/reports/${A}.json"

  echo "=== validate $A ==="
  python harness.py validate V "$A"
  echo "validate_${A}_exit=$?"
done

echo "=== aggregate after universal triage ==="
python harness.py aggregate V | tee runlogs/aggregate_after_triage.json
echo "aggregate_exit=${PIPESTATUS[0]}"

echo "=== digest after universal triage ==="
python harness.py digest V
echo "digest_exit=$?"
cat runs/V/digest.md

echo "=== plan after universal triage ==="
python harness.py plan V | tee runlogs/plan_after_triage.txt
echo "plan_exit=${PIPESTATUS[0]}"
