#!/usr/bin/env python3
"""Put a credential into .env without it touching the shell's history.

A key typed as part of a command is recorded by PSReadLine in a plain text file
that persists across reboots, so "paste your key on the command line" is advice
that quietly creates that file. Here the command carries only the variable's
*name*; the value is typed at a prompt, is not echoed, and is never printed
back.

    python scripts/set_key.py OPENDART_API_KEY
    python scripts/set_key.py POLYGON_API_KEY
    python scripts/set_key.py --list

The same thing is available in the web app at /settings. Both go through
`packages.env_file`, because two descriptions of "write a credential" would
drift and the first sign of that is a key that looks saved and is not.
"""
import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages import env_file  # noqa: E402


def show() -> int:
    """Which variables are set. Never what they are set to."""
    rows = env_file.describe()
    width = max(len(r['name']) for r in rows)
    path = env_file.env_path()
    print(f'{path if path.exists() else str(path) + " (아직 없다)"}\n')
    for row in rows:
        # The CLI writes the file, so the file is the fact it reports; a value
        # only in this shell's environment is noted as such.
        state = ('설정됨    ' if row['in_file'] else
                 '환경변수만' if row['configured'] else '없음      ')
        print(f"  {state}  {row['name']:<{width}}  {row['unblocks']}")
    print('\n  값은 표시하지 않는다. 웹에서는 /settings 화면에서 같은 일을 한다.')
    return 0


def main(argv=None) -> int:
    names = [row['name'] for row in env_file.KNOWN]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('name', nargs='?', help=f'변수 이름 ({", ".join(names)})')
    parser.add_argument('--list', action='store_true', help='무엇이 설정됐는지만 본다')
    parser.add_argument('--stdin', action='store_true',
                        help='값을 표준입력에서 읽는다 (자동화용). 명령줄로는 받지 않는다 — '
                             '명령줄에 적힌 값은 셸 기록에 남는다')
    args = parser.parse_args(argv)

    if args.list or not args.name:
        return show()

    name = args.name.strip()
    row = env_file.BY_NAME.get(name)
    if row is None:
        print(f'{name!r}은 이 앱이 읽는 변수가 아니다. 가능한 값: {", ".join(names)}',
              file=sys.stderr)
        return 2

    if args.stdin:
        value = sys.stdin.read().strip()
    else:
        print(f"{name} — {row['note']}")
        if row.get('signup'):
            print(f"발급: {row['signup']}")
        prompt = '값 (붙여넣고 Enter, 화면에 보이지 않는다): '
        # A contact is not a secret; hiding it only makes it hard to check.
        value = (getpass.getpass(prompt) if row['secret'] else input('값: ')).strip()

    if not value:
        print('빈 값이다. 아무것도 바꾸지 않았다.', file=sys.stderr)
        return 1
    try:
        # The CLI writes the file; it does not run the app, so there is no
        # process environment worth touching.
        path = env_file.write(name, value, apply_to_process=False)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f'\n{name} 저장됨 → {path}')
    print('런처를 다시 시작하면 반영된다. (.env는 커밋되지 않는다)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
