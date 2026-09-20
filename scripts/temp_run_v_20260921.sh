#!/usr/bin/env bash
set -u
set -o pipefail

mkdir -p runlogs
exec > >(tee runlogs/continuation_macro_v33.log) 2>&1

echo "=== replace MO with v3.3 global-components report ==="
cp automation_inputs/V_MO.json runs/V/reports/MO.json

echo "=== validate MO ==="
python harness.py validate V MO
echo "validate_MO_exit=$?"

echo "=== cache macro ==="
python harness.py cache-macro V
echo "cache_macro_exit=$?"

echo "=== aggregate after v3.3 macro ==="
python harness.py aggregate V | tee runlogs/aggregate_after_macro_v33.json
echo "aggregate_exit=${PIPESTATUS[0]}"

echo "=== digest ==="
python harness.py digest V
echo "digest_exit=$?"

echo "=== plan ==="
python harness.py plan V | tee runlogs/plan_after_macro_v33.txt
echo "plan_exit=${PIPESTATUS[0]}"
