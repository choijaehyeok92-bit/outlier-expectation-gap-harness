#!/usr/bin/env bash
# macOS double-click entry point. Finder runs a .command in Terminal; this just
# hands off to start.sh so there is one launcher, not two that drift.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start.sh" "$@"
