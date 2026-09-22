#!/usr/bin/env python3
"""Put a credential into .env without it touching the shell's history.

Written in Python rather than PowerShell on purpose. A key typed as part of a
command is recorded by PSReadLine in a plain text file that persists across
reboots, and "paste your key on the command line" is advice that quietly
creates that file. Here the command carries only the variable's *name*; the
value is typed at a prompt, is not echoed, and is never printed back.

    python scripts/set_key.py OPENDART_API_KEY
    python scripts/set_key.py POLYGON_API_KEY
    python scripts/set_key.py --list

The file is updated in place: an existing line keeps its position among the
comments that explain it, and a variable the template does not mention is
appended. Restart the launcher afterwards — .env is read at startup.
"""
import argparse
import getpass
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / '.env'
TEMPLATE = ROOT / '.env.example'

# The variables this app actually reads, so a typo becomes a refusal rather
# than a line nothing will ever look at.
KNOWN = {
    'SEC_USER_AGENT': 'SEC 공정이용 연락처 (키가 아니다). 예: 홍길동 hong@example.com',
    'OPENDART_API_KEY': 'OpenDART 인증키 — https://opendart.fss.or.kr/',
    'POLYGON_API_KEY': '미국 시세 — https://polygon.io/dashboard/api-keys',
    'EODHD_API_KEY': 'polygon 대신 쓸 때만 — https://eodhd.com/cp/dashboard',
    'OPENAI_API_KEY': '유료 단계용 모델',
    'ANTHROPIC_API_KEY': '유료 단계용 모델',
    'HARNESS_DATABASE_URL': '작업 큐를 쓸 때만',
}
NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def read(path: Path) -> tuple:
    """(lines, newline). A BOM is dropped; the file's own line ending is kept."""
    if not path.exists():
        return [], os.linesep
    raw = path.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    text = raw.decode('utf-8', errors='replace')
    newline = '\r\n' if '\r\n' in text else '\n'
    return text.replace('\r\n', '\n').split('\n'), newline


def current(lines) -> dict:
    found = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            continue
        name, _, value = stripped.partition('=')
        if NAME.match(name.strip()):
            found[name.strip()] = value.strip().strip('"').strip("'")
    return found


def put(lines, name: str, value: str) -> list:
    """Replace the variable's line where it already is, or append it."""
    pattern = re.compile(rf'^\s*{re.escape(name)}\s*=')
    updated, replaced = [], False
    for line in lines:
        if not replaced and pattern.match(line) and not line.strip().startswith('#'):
            updated.append(f'{name}={value}')
            replaced = True
        else:
            updated.append(line)
    if replaced:
        return updated
    while updated and not updated[-1].strip():
        updated.pop()
    return updated + ['', f'{name}={value}']


def show(lines) -> int:
    """Which variables are set. Never what they are set to."""
    # With no .env yet, `lines` is the template — whose placeholders are not
    # values. Reporting them as set would send somebody looking for a key they
    # have not actually supplied.
    found = current(lines) if ENV.exists() else {}
    width = max(len(n) for n in KNOWN)
    print(f'{ENV if ENV.exists() else str(ENV) + " (아직 없다)"}\n')
    for name, note in KNOWN.items():
        state = '설정됨' if found.get(name) else '없음  '
        print(f'  {state}  {name:<{width}}  {note}')
    extra = sorted(set(found) - set(KNOWN))
    if extra:
        print(f'\n  이 앱이 읽지 않는 변수도 있다: {", ".join(extra)}')
    print('\n  값은 표시하지 않는다. 변경 후에는 런처를 다시 시작한다.')
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('name', nargs='?', help=f'변수 이름 ({", ".join(KNOWN)})')
    parser.add_argument('--list', action='store_true', help='무엇이 설정됐는지만 본다')
    parser.add_argument('--stdin', action='store_true',
                        help='값을 표준입력에서 읽는다 (자동화용). 명령줄로는 받지 않는다 — '
                             '명령줄에 적힌 값은 셸 기록에 남는다')
    args = parser.parse_args(argv)

    lines, newline = read(ENV)
    if not ENV.exists() and TEMPLATE.exists():
        lines, newline = read(TEMPLATE)

    if args.list or not args.name:
        return show(lines)

    name = args.name.strip()
    if name not in KNOWN:
        print(f'{name!r}은 이 앱이 읽는 변수가 아니다. 가능한 값: {", ".join(KNOWN)}',
              file=sys.stderr)
        return 2

    if args.stdin:
        value = sys.stdin.read().strip()
    else:
        print(f'{name} — {KNOWN[name]}')
        # getpass keeps the value off the screen and out of the shell's history.
        value = getpass.getpass('값 (붙여넣고 Enter, 화면에 보이지 않는다): ').strip()

    if not value:
        print('빈 값이다. 아무것도 바꾸지 않았다.', file=sys.stderr)
        return 1
    if '\n' in value or '\r' in value:
        print('값에 줄바꿈이 있다. 한 줄로 붙여넣는다.', file=sys.stderr)
        return 1

    ENV.write_text(newline.join(put(lines, name, value)) + newline, encoding='utf-8')
    print(f'\n{name} 저장됨 → {ENV}')
    print('런처를 다시 시작하면 반영된다. (.env는 커밋되지 않는다)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
