"""The .env file: what the app reads from it, and how a value gets in.

One implementation, shared by the CLI (`scripts/set_key.py`) and the settings
page. Two descriptions of "write a credential" would drift, and the first sign
of that is a key that looks saved and is not.

Three rules the whole module is built around.

**A value goes in; it never comes out.** `describe()` reports whether a
variable is set and nothing else — not the value, not its length, not a prefix.
The only reader of the actual value is the provider class that needs it.

**Writing is separate from reading.** The catalogue can be served to a browser.
Setting a value cannot, without the caller proving it is local — that check
lives in the API layer, because it is about the request, not the file.

**A missing credential blocks its own step and nothing else.** So the catalogue
carries which step each one unblocks: "이 키가 없으면 무엇을 못 하는가"는
설정 화면이 답해야 하는 질문이다.
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / '.env'
TEMPLATE = ROOT / '.env.example'
NAME = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
# Keeping credentials outside the checkout is a reasonable thing to want, and
# resolving the path per call rather than at import also means a test can point
# the whole module somewhere scratch.
ENV_OVERRIDE = 'HARNESS_ENV_FILE'


def env_path(path=None) -> Path:
    if path:
        return Path(path)
    override = (os.environ.get(ENV_OVERRIDE) or '').strip()
    return Path(override) if override else ENV

# Every variable this application reads, what it is for, and which pipeline
# step stops without it. A name that is not here cannot be written: a typo
# would otherwise become a line nothing will ever look at.
KNOWN = [
    {'name': 'SEC_USER_AGENT', 'group': 'regulator', 'secret': False,
     'label': 'SEC 연락처', 'unblocks': '0·1단계 — 미국 명단·적재',
     'note': '키가 아니라 연락처다. SEC 공정이용 정책이 User-Agent에 연락처를 요구하고, '
             '하네스는 당신이 설정하지 않은 연락처를 보내지 않는다.',
     'placeholder': '홍길동 hong@example.com',
     'signup': 'https://www.sec.gov/os/webmaster-faq#developers'},
    {'name': 'OPENDART_API_KEY', 'group': 'regulator', 'secret': True,
     'label': 'OpenDART 인증키', 'unblocks': '0·1단계 — 한국 명단·적재',
     'note': '발급 무료. 키당 일일 호출 한도가 있어 하루에 적재할 수 있는 기업 수를 정한다.',
     'signup': 'https://opendart.fss.or.kr/'},
    {'name': 'POLYGON_API_KEY', 'group': 'market', 'secret': True,
     'label': 'Polygon.io', 'unblocks': '2단계 — 미국 시세',
     'note': '무료 티어로도 기준일 하나는 충분하다 — 한 세션이 호출 1회다.',
     'signup': 'https://polygon.io/dashboard/api-keys'},
    {'name': 'EODHD_API_KEY', 'group': 'market', 'secret': True,
     'label': 'EOD Historical Data', 'unblocks': '2단계 — 미국 시세 (polygon 대안)',
     'note': 'polygon이 막히거나 미국 외 거래소가 필요할 때만.',
     'signup': 'https://eodhd.com/cp/dashboard'},
    {'name': 'OPENAI_API_KEY', 'group': 'model', 'secret': True,
     'label': 'OpenAI', 'unblocks': '5~7단계 — triage·full harness·심층 보고서',
     'note': '실제 모델. 기업당 호출 수만큼 과금된다. 비워 두면 유료 단계가 '
             '오프라인 스텁으로만 돌아 돈이 나가지 않는다.',
     'signup': 'https://platform.openai.com/api-keys'},
    {'name': 'ANTHROPIC_API_KEY', 'group': 'model', 'secret': True,
     'label': 'Anthropic', 'unblocks': '5~7단계 — triage·full harness·심층 보고서',
     'note': '실제 모델. 기업당 호출 수만큼 과금된다.',
     'signup': 'https://console.anthropic.com/settings/keys'},
    {'name': 'HARNESS_DATABASE_URL', 'group': 'optional', 'secret': True,
     'label': '데이터베이스', 'unblocks': '작업 큐·야간 스케줄 (선택)',
     'note': '비우면 파일만으로 동작한다. 큐를 쓸 때만 필요하다.',
     'placeholder': 'postgresql+psycopg://user:pass@host/harness', 'signup': None},
]
BY_NAME = {row['name']: row for row in KNOWN}


def read(path=None) -> tuple:
    """(lines, newline). A BOM is dropped; the file's own line ending is kept."""
    target = env_path(path)
    if not target.exists():
        return [], os.linesep
    raw = target.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    text = raw.decode('utf-8', errors='replace')
    newline = '\r\n' if '\r\n' in text else '\n'
    return text.replace('\r\n', '\n').split('\n'), newline


def values(lines) -> dict:
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
    """Replace the variable's line where it already sits, or append it.

    In place, so the comment explaining a key stays beside it — that comment is
    what somebody reads when the key stops working.
    """
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


def clear(lines, name: str) -> list:
    """Empty the value, keeping the line and its comment."""
    return put(lines, name, '')


def save(lines, newline: str, path=None) -> Path:
    target = env_path(path)
    target.write_text(newline.join(lines) + newline, encoding='utf-8')
    return target


def write(name: str, value: str, *, path=None, apply_to_process: bool = True) -> Path:
    """Set one variable, and make it take effect without a restart.

    The file is the record; `os.environ` is what the provider classes read.
    Writing only the file would mean a key that is saved and does not work
    until somebody restarts — a difference nobody should have to know about.
    """
    if name not in BY_NAME:
        raise ValueError(f'{name!r}은 이 앱이 읽는 변수가 아니다')
    if not NAME.match(name):
        raise ValueError(f'{name!r} is not a valid variable name')
    value = (value or '').strip()
    if '\n' in value or '\r' in value:
        raise ValueError('값에 줄바꿈이 있다. 한 줄로 입력한다.')
    target = env_path(path)
    lines, newline = read(target)
    if not target.exists() and TEMPLATE.exists():
        lines, newline = read(TEMPLATE)
    saved = save(put(lines, name, value), newline, target)
    if apply_to_process:
        if value:
            os.environ[name] = value
        else:
            os.environ.pop(name, None)
    return saved


def describe(environ=None, path=None) -> list:
    """Each known variable and whether it is set. Never what it is set to.

    Two facts, kept apart because they can disagree and the difference is what
    somebody needs to know:

    `configured` — live in *this* process, which is what a provider will read
    right now. `in_file` — present in .env, which is what it will read after a
    restart. A CLI that just wrote the file sees `in_file` without
    `configured`; a value exported in the shell is the reverse. Collapsing them
    into one flag means either a key that reads as set and fails, or one that
    reads as missing and works.
    """
    env = environ if environ is not None else os.environ
    target = env_path(path)
    on_disk = values(read(target)[0]) if target.exists() else {}
    rows = []
    for row in KNOWN:
        name = row['name']
        live = bool((env.get(name) or '').strip())
        stored = bool((on_disk.get(name) or '').strip())
        rows.append({**row, 'configured': live, 'in_file': stored,
                     'needs_restart': stored and not live,
                     'source': 'process' if live and not stored
                               else 'file' if live and stored
                               else 'file_pending' if stored else None})
    return rows
