#!/usr/bin/env bash
# One command to run the whole app: API, web, browser.
#
# Three things it exists to get right, because each has already cost an hour.
#
#   NEXT_PUBLIC_API_BASE and WEB_ORIGINS must agree. The first is baked into
#   the web bundle and the second is the API's CORS list; setting one and not
#   the other produces a page that renders and then fetches nothing, with the
#   only evidence in the browser console.
#
#   A busy port is found before anything starts, not after one process is up
#   and the other is confused.
#
#   Both processes die together. A stopped launcher that leaves uvicorn
#   holding port 8000 makes the next run fail for a reason that looks unrelated.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_PORT="${HARNESS_API_PORT:-8000}"
WEB_PORT="${HARNESS_WEB_PORT:-3000}"
OPEN_BROWSER="${HARNESS_OPEN_BROWSER:-1}"

say() { printf '%s\n' "$*" >&2; }
die() { say "오류: $*"; exit 1; }

# --- credentials -------------------------------------------------------------
# A .env beside the repository, never committed. Keys stay on this machine and
# reach the API process only; nothing here prints or forwards a value.
if [ -f .env ]; then
  say "· .env 읽는 중"
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

# --- prerequisites -----------------------------------------------------------
command -v python3 >/dev/null || die "python3가 없다. 3.10 이상이 필요하다."
python3 - <<'PY' || die "Python 3.10 이상이 필요하다."
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY

command -v node >/dev/null || die "node가 없다. 18.18 이상 또는 20 이상이 필요하다."
NODE_RAW="$(node --version)"
NODE_MAJOR="${NODE_RAW#v}"; NODE_MAJOR="${NODE_MAJOR%%.*}"
NODE_MINOR="$(printf '%s' "${NODE_RAW#v}" | cut -d. -f2)"
if [ "$NODE_MAJOR" -lt 18 ] \
   || { [ "$NODE_MAJOR" -eq 18 ] && [ "$NODE_MINOR" -lt 18 ]; } \
   || { [ "$NODE_MAJOR" -eq 19 ] && [ "$NODE_MINOR" -lt 8 ]; }; then
  die "Node $NODE_RAW는 Next.js가 받지 않는다. 20 LTS 이상을 설치한다."
fi

python3 -c 'import fastapi, uvicorn' 2>/dev/null \
  || die "API 의존성이 없다: pip install -r apps/api/requirements.txt"

if [ ! -d apps/web/node_modules ]; then
  say "· 웹 의존성 설치 (npm ci) — 처음 한 번만 걸린다"
  (cd apps/web && npm ci)
fi

# --- ports -------------------------------------------------------------------
free_port() {
  python3 - "$1" <<'PY'
import socket, sys
start = int(sys.argv[1])
for port in range(start, start + 40):
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', port))
        except OSError:
            continue
    print(port)
    raise SystemExit(0)
raise SystemExit(1)
PY
}
API_PORT="$(free_port "$API_PORT")" || die "$API_PORT 부근에 빈 포트가 없다."
WEB_PORT="$(free_port "$WEB_PORT")" || die "$WEB_PORT 부근에 빈 포트가 없다."

API_BASE="http://127.0.0.1:${API_PORT}"
WEB_URL="http://localhost:${WEB_PORT}"
# The two variables that have to agree, set in one place.
export WEB_ORIGINS="http://localhost:${WEB_PORT},http://127.0.0.1:${WEB_PORT}"
export NEXT_PUBLIC_API_BASE="$API_BASE"

# --- run ---------------------------------------------------------------------
API_PID=""; WEB_PID=""
cleanup() {
  trap - EXIT INT TERM
  say ""
  say "· 종료 중"
  [ -n "$WEB_PID" ] && kill "$WEB_PID" 2>/dev/null || true
  [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

say "· API   ${API_BASE}"
python3 -m uvicorn apps.api.main:app --host 127.0.0.1 --port "$API_PORT" &
API_PID=$!

for _ in $(seq 1 60); do
  if curl -sf --noproxy '*' "${API_BASE}/api/health" >/dev/null 2>&1; then break; fi
  kill -0 "$API_PID" 2>/dev/null || die "API가 시작하지 못했다. 위 로그를 본다."
  sleep 1
done
curl -sf --noproxy '*' "${API_BASE}/api/health" >/dev/null 2>&1 \
  || die "API가 60초 안에 응답하지 않았다."

say "· 웹    ${WEB_URL}"
(cd apps/web && exec npx next dev -p "$WEB_PORT") &
WEB_PID=$!

for _ in $(seq 1 90); do
  if curl -sf --noproxy '*' "$WEB_URL" >/dev/null 2>&1; then break; fi
  kill -0 "$WEB_PID" 2>/dev/null || die "웹이 시작하지 못했다. 위 로그를 본다."
  sleep 1
done
# Announcing a URL that never came up reads as the app being broken rather
# than as the build still failing.
curl -sf --noproxy '*' "$WEB_URL" >/dev/null 2>&1 \
  || die "웹이 90초 안에 응답하지 않았다. 위 로그를 본다."

say ""
say "  열림: ${WEB_URL}/pipeline"
say "  끄려면 이 창에서 Ctrl+C"
say ""
if [ "$OPEN_BROWSER" = "1" ]; then
  (command -v open >/dev/null && open "${WEB_URL}/pipeline") \
    || (command -v xdg-open >/dev/null && xdg-open "${WEB_URL}/pipeline" >/dev/null 2>&1) \
    || true
fi
wait
