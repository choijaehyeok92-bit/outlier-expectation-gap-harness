"""Korean account line → normalized metric, deterministically.

The chain is ordered and every step records which rung matched, so a reviewer
can see whether a number arrived by an exact XBRL element id or by a substring
guess. The last rung is not a guess at all: an unmatched line becomes
`metric=other` with the filer's own label preserved and `requires_review=true`.

No language model is consulted. The temptation is real — a model reads
"영업수익" and says "revenue" immediately — but a mapping that is re-derived on
every run is a mapping that can change without anyone editing a file, and the
whole series silently moves with it. A YAML file with a version does not do
that.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = ROOT / 'config' / 'account_mappings_kr.yaml'
STAGES = ('account_id', 'label', 'statement_label', 'heuristic', 'review_required', 'unmapped')
_PAREN = str.maketrans({'（': '(', '）': ')', '［': '[', '］': ']'})
# OpenDART writes an absent detail as a literal dash rather than leaving it out.
_ABSENT = {'', '-', '–', '—', 'N/A', 'null', 'None'}


@dataclass(frozen=True)
class Resolution:
    metric: str
    stage: str
    metric_detail: Optional[str] = None
    requires_review: bool = False
    review_reason: Optional[str] = None
    confidence: Optional[float] = None


def load_mapping(path=None) -> dict:
    try:
        import yaml
    except ImportError as error:                    # pragma: no cover - dependency guard
        raise RuntimeError(
            'The Korean account map is YAML; install PyYAML '
            '(pip install -r data_adapters/requirements.txt)') from error
    return yaml.safe_load(Path(path or MAPPING_PATH).read_text(encoding='utf-8'))


def normalize_label(label: str, rules: Optional[dict] = None) -> str:
    """Fold the cosmetic differences between filers, and nothing more."""
    rules = rules or {}
    text = str(label or '')
    if rules.get('fold_parentheses', True):
        text = text.translate(_PAREN)
    for suffix in rules.get('drop_suffixes') or []:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    if rules.get('strip_whitespace', True):
        text = re.sub(r'\s+', '', text)
    return text.strip()


class AccountResolver:
    """Resolve one disclosure line. Stateless apart from the loaded map."""

    def __init__(self, mapping: Optional[dict] = None):
        self.mapping = mapping or load_mapping()
        self.version = self.mapping.get('version')
        self._normalization = self.mapping.get('normalization') or {}
        self._by_account_id = self.mapping.get('by_account_id') or {}
        self._by_label = {normalize_label(k, self._normalization): v
                          for k, v in (self.mapping.get('by_label') or {}).items()}
        self._by_statement_label = {
            statement: {normalize_label(k, self._normalization): v for k, v in rows.items()}
            for statement, rows in (self.mapping.get('by_statement_label') or {}).items()}
        self._heuristics = self.mapping.get('heuristics') or []
        self._review = {normalize_label(k, self._normalization): v
                        for k, v in (self.mapping.get('review_required') or {}).items()}

    def resolve(self, account_id: Optional[str], label: Optional[str],
                statement: str, detail: Optional[str] = None) -> Resolution:
        normalized = normalize_label(label, self._normalization)

        # An explicit review escalation outranks a convenient mapping: these are
        # the lines a tidy answer would quietly distort.
        escalation = self._review.get(normalized)
        if escalation:
            return Resolution(escalation.get('metric', 'other'), 'review_required',
                              metric_detail=escalation.get('metric_detail') or normalized,
                              requires_review=True,
                              review_reason=' '.join(str(escalation.get('reason', '')).split()),
                              confidence=0.9)

        if account_id and account_id in self._by_account_id:
            return Resolution(self._by_account_id[account_id], 'account_id', confidence=0.98)

        scoped = self._by_statement_label.get(statement, {})
        if normalized in scoped:
            metric = scoped[normalized]
            return Resolution(metric, 'statement_label',
                              metric_detail=normalized if metric == 'other' else None,
                              requires_review=metric == 'other', confidence=0.92)

        if normalized in self._by_label:
            metric = self._by_label[normalized]
            return Resolution(metric, 'label',
                              metric_detail=normalized if metric == 'other' else None,
                              requires_review=metric == 'other', confidence=0.9)

        for rule in self._heuristics:
            statements = rule.get('statements')
            if statements and statement not in statements:
                continue
            if all(token in normalized for token in (rule.get('contains') or [])):
                return Resolution(rule['metric'], 'heuristic', confidence=0.7,
                                  review_reason='matched by substring heuristic, not an exact account id')

        detail_text = str(detail or '').strip()
        if detail_text in _ABSENT:
            detail_text = ''
        return Resolution('other', 'unmapped',
                          metric_detail=(detail_text or normalized or 'unlabelled line'),
                          requires_review=True, confidence=0.4,
                          review_reason=f'no mapping for account_id={account_id or "-"} '
                                        f'label={normalized or "-"} in {statement}')
