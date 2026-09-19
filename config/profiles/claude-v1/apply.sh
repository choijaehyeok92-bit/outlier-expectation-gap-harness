#!/usr/bin/env bash
set -euo pipefail
echo "This is a historical v2 profile. Use its original harness commit in a separate checkout."
echo "Refusing to overwrite v3 strategy, workflow or calibration configuration."
exit 1
