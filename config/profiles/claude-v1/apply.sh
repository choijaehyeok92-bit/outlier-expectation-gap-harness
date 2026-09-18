#!/usr/bin/env bash
# Apply the claude-v1 calibration profile to config/.
# Originals are preserved in config/profiles/_original/ — run revert.sh to restore.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
for f in strategy.json calibration.json workflow.json; do
  cp "$ROOT/config/profiles/claude-v1/$f" "$ROOT/config/$f"
done
echo "claude-v1 profile applied (this is the repo default as of this commit)."
echo "WARNING: config hashes changed. run_manifest.input_snapshot/config_files of existing runs no longer match;"
echo "re-freeze before comparing any run scored under a different profile."
