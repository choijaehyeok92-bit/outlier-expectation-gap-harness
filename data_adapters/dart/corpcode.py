"""corpCode cache: stock_code ↔ corp_code ↔ corp_name.

OpenDART keys everything on an eight-digit `corp_code` that appears nowhere a
person would look. The mapping arrives as one zipped XML of every registered
corporation — tens of thousands of rows — so it is fetched once, written to
disk, and read from there.

`stock_code` is the listing signal: a row carrying one is a listed company, a
row without one is not. What the file does *not* carry is the market segment,
so this module never claims to know whether a listing is KOSPI or KOSDAQ. That
comes from the KRX-compatible market provider, and until it does the exchange
stays `KRX` with a review flag.
"""
import io
import json
import re
import xml.etree.ElementTree as ElementTree
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / 'data' / 'dart' / 'corp_codes.json'
STOCK_CODE = re.compile(r'^\d{6}$')


@dataclass(frozen=True)
class CorpCodeEntry:
    corp_code: str
    corp_name: str
    stock_code: Optional[str]
    modify_date: Optional[str]

    @property
    def listed(self) -> bool:
        return bool(self.stock_code and STOCK_CODE.match(self.stock_code))

    def to_dict(self) -> dict:
        return {'corp_code': self.corp_code, 'corp_name': self.corp_name,
                'stock_code': self.stock_code, 'modify_date': self.modify_date}


def parse_corp_code_zip(payload: bytes) -> list:
    """The API returns a zip holding one XML. Tolerate a bare XML too."""
    raw = payload
    if payload[:2] == b'PK':
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith('.xml')]
            if not names:
                raise ValueError('corpCode archive holds no XML')
            raw = archive.read(names[0])
    root = ElementTree.fromstring(raw)
    rows = []
    for node in root.iter('list'):
        code = (node.findtext('corp_code') or '').strip()
        if not code:
            continue
        stock = (node.findtext('stock_code') or '').strip() or None
        rows.append(CorpCodeEntry(
            corp_code=code,
            corp_name=(node.findtext('corp_name') or '').strip(),
            stock_code=stock,
            modify_date=(node.findtext('modify_date') or '').strip() or None))
    return rows


class CorpCodeCache:
    """Load from disk, refresh from the API, resolve in either direction."""

    def __init__(self, path=None, entries: Optional[Iterable[CorpCodeEntry]] = None):
        self.path = Path(path or DEFAULT_CACHE)
        self.fetched_at: Optional[str] = None
        self.entries: list = list(entries or [])
        self._by_corp: dict = {}
        self._by_stock: dict = {}
        self._by_name: dict = {}
        if self.entries:
            self._index()
        elif self.path.exists():
            self.load()

    def _index(self) -> None:
        self._by_corp = {e.corp_code: e for e in self.entries}
        self._by_stock = {e.stock_code: e for e in self.entries if e.stock_code}
        self._by_name = {}
        for entry in self.entries:
            self._by_name.setdefault(entry.corp_name.strip(), entry)

    def load(self) -> 'CorpCodeCache':
        payload = json.loads(self.path.read_text(encoding='utf-8'))
        self.fetched_at = payload.get('fetched_at')
        self.entries = [CorpCodeEntry(**row) for row in payload.get('entries', [])]
        self._index()
        return self

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(
            {'fetched_at': self.fetched_at or date.today().isoformat(),
             'count': len(self.entries),
             'entries': [e.to_dict() for e in self.entries]},
            ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        return self.path

    def refresh(self, payload: bytes, fetched_at: Optional[str] = None) -> 'CorpCodeCache':
        self.entries = parse_corp_code_zip(payload)
        self.fetched_at = fetched_at or date.today().isoformat()
        self._index()
        return self

    @property
    def listed(self) -> list:
        return [e for e in self.entries if e.listed]

    def by_stock_code(self, stock_code: str) -> Optional[CorpCodeEntry]:
        return self._by_stock.get(str(stock_code).strip().zfill(6))

    def by_corp_code(self, corp_code: str) -> Optional[CorpCodeEntry]:
        return self._by_corp.get(str(corp_code).strip().zfill(8))

    def by_name(self, name: str) -> Optional[CorpCodeEntry]:
        return self._by_name.get(str(name).strip())

    def resolve(self, identifier: str) -> Optional[CorpCodeEntry]:
        """Six digits is a 종목코드, eight is a corp_code, anything else is a name."""
        text = str(identifier).strip()
        if STOCK_CODE.match(text):
            return self.by_stock_code(text)
        if re.fullmatch(r'\d{8}', text):
            return self.by_corp_code(text)
        return self.by_name(text)
