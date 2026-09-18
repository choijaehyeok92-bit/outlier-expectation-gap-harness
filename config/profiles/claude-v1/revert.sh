#!/usr/bin/env bash
# Restore the original (gpt-5.6-sol authored) calibration.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
for f in strategy.json calibration.json workflow.json; do
  cp "$ROOT/config/profiles/_original/$f" "$ROOT/config/$f"
done
echo "original profile restored."
