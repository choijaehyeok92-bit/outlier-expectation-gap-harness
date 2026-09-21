"""Natural language to ScreeningSpec.

Two parsers, one contract. `LexiconParser` is deterministic: it resolves only
the phrases declared in `config/screening_lexicon.json`, so "해자가 강함" becomes
a harness moat-trajectory threshold and nothing else becomes anything at all.
`LLMParser` asks a model for the same document and then puts it through exactly
the same validation. Neither one may invent a field, a threshold or a unit, and
neither one writes SQL.

What a parser cannot resolve, it must say out loud. Everything unmapped lands
in `unresolved_conditions`, including the case that matters most here: a
qualitative judgement like "moat가 강하다" for a company the harness has not
analysed. The screener does not estimate a moat. It marks the spec
`requires_harness_run` and leaves the judgement to the harness.
"""
import hashlib
import json
import re

from . import spec as spec_module
from .fields import Registry, load_lexicon
from .units import UnitError, parse_currency_amount, parse_number, parse_percent

SEGMENT_SPLIT = re.compile(r'[,;·]|\s+그리고\s+|\s+및\s+|\s+and\s+|이며|이고|하고\s|면서', re.I)
STOP_SEGMENT = re.compile(r'^[\s가-힣a-z0-9]{0,3}$|^(기업|종목|회사|중|찾아줘|찾아|알려줘|보여줘|주세요|중에서|가운데)\S*$', re.I)


def lexicon_sha256(lexicon):
    return hashlib.sha256(json.dumps(lexicon, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def _segments(text):
    return [s.strip() for s in SEGMENT_SPLIT.split(text or '') if s and s.strip()]


def _comparator(segment, lexicon):
    """The comparator word in a segment, longest match first. None when absent."""
    lowered = segment.lower()
    best = None
    for token, operator in (lexicon.get('comparators') or {}).items():
        if token.lower() in lowered and (best is None or len(token) > len(best[0])):
            best = (token, operator)
    return best[1] if best else None


def _value_for(phrase, segment, lexicon):
    kind = phrase.get('value_kind')
    if kind == 'ratio':
        return parse_percent(segment), None
    if kind == 'currency':
        return parse_currency_amount(segment, lexicon)
    return parse_number(segment, lexicon), None


class LexiconParser:
    """Deterministic phrase resolution. The offline default and the reference behaviour."""

    name = 'lexicon'
    model = None

    def __init__(self, lexicon=None, registry=None):
        self.lexicon = lexicon or load_lexicon()
        self.registry = registry or Registry()

    def parse(self, text, as_of_date):
        spec = spec_module.empty(as_of_date, 'natural_language')
        spec['source']['text'] = text
        clauses, unresolved = [], []
        universe = {}
        sort = []

        for segment in _segments(text):
            matched = False
            lowered = segment.lower()

            for token, code in (self.lexicon.get('jurisdiction_tokens') or {}).items():
                if token.lower() in lowered:
                    universe.setdefault('jurisdictions', [])
                    if code not in universe['jurisdictions']:
                        universe['jurisdictions'].append(code)
                    matched = True

            for phrase in self.lexicon.get('qualitative_phrases') or []:
                if any(p.lower() in lowered for p in phrase['patterns']):
                    for template in phrase['filters']:
                        clauses.append({**template, 'origin_text': segment,
                                        'rationale': phrase.get('rationale')})
                    matched = True

            for phrase in self.lexicon.get('metric_phrases') or []:
                if not any(p.lower() in lowered for p in phrase['patterns']):
                    continue
                matched = True
                operator = _comparator(segment, self.lexicon)
                if operator is None:
                    unresolved.append({'text': segment, 'reason': 'ambiguous_threshold',
                                       'suggested_field': phrase['field'],
                                       'detail': '비교 방향(이상/이하 등)을 읽을 수 없어 필터로 만들지 않았다.'})
                    continue
                try:
                    value, currency = _value_for(phrase, segment, self.lexicon)
                except UnitError as error:
                    unresolved.append({'text': segment, 'reason': 'ambiguous_threshold',
                                       'suggested_field': phrase['field'], 'detail': str(error)})
                    continue
                clause = {'field': phrase['field'], 'operator': operator, 'value': value,
                          'unit': phrase.get('field_unit'), 'origin_text': segment}
                if currency:
                    clause['currency'] = currency
                clauses.append(clause)

            for phrase in self.lexicon.get('sort_phrases') or []:
                if any(p.lower() in lowered for p in phrase['patterns']):
                    sort.append({'field': phrase['field'], 'direction': phrase['direction']})
                    matched = True

            if not matched and not STOP_SEGMENT.match(segment):
                unresolved.append({'text': segment, 'reason': 'unparsed_remainder',
                                   'suggested_field': None,
                                   'detail': '사전에 선언된 표현이 아니어서 필터로 변환하지 않았다.'})

        spec['universe'] = universe
        spec['filters'] = {'op': 'and', 'clauses': clauses}
        spec['sort'] = sort or [{'field': 'core_score', 'direction': 'desc'}]
        spec['unresolved_conditions'] = unresolved
        return spec_module.stamp_parser(spec, self.name, self.model, lexicon_sha256(self.lexicon))


PROMPT = """\
아래 자연어 요청을 ScreeningSpec JSON 하나로 변환한다.

절대 규칙:
- SQL을 작성하지 않는다.
- 재무지표를 계산하지 않는다.
- 점수·archetype·Hard Veto·밸류에이션·포지션을 만들어내지 않는다.
- 아래 허용된 field 식별자만 사용한다. 없는 field는 만들지 않는다.
- 비율 field의 값은 소수다. 15%는 0.15이며 15가 아니다.
- 통화 임계값에는 currency를 명시한다. 환율은 직접 정하지 않는다.
- 매핑할 수 없는 조건은 버리지 말고 unresolved_conditions에 원문 그대로 남긴다.
- 하네스 실행 결과가 있어야만 판단 가능한 조건(해자, veto 등)은 requires_harness_run을 true로 둔다.

as_of_date: {as_of_date}

허용 field:
{fields}

출력 JSON Schema:
{schema}

요청:
{text}
"""


class LLMParser:
    """A model produces the spec; this class validates it exactly like any other spec."""

    def __init__(self, provider, lexicon=None, registry=None, schema=None):
        self.provider = provider
        self.lexicon = lexicon or load_lexicon()
        self.registry = registry or Registry()
        self.schema = schema or spec_module.load_schema()

    @property
    def name(self):
        return self.provider.name

    @property
    def model(self):
        return self.provider.model

    def prompt(self, text, as_of_date):
        fields = '\n'.join(
            f"- {f['id']} ({f['dtype']}, unit={f['unit']}"
            + (', requires_harness_run' if f['requires_harness_run'] else '')
            + (', backend not yet available' if not f['available'] else '') + ')'
            for f in self.registry.describe())
        return PROMPT.format(as_of_date=as_of_date, fields=fields,
                             schema=json.dumps(self.schema, ensure_ascii=False), text=text)

    def parse(self, text, as_of_date):
        candidate = self.provider.complete_json(
            stage='screening_spec', prompt=self.prompt(text, as_of_date), schema=self.schema)
        candidate = dict(candidate)
        candidate['as_of_date'] = as_of_date
        candidate.setdefault('source', {'kind': 'natural_language'})
        candidate['source']['kind'] = 'natural_language'
        candidate['source']['text'] = text
        candidate.pop('spec_id', None)
        return spec_module.stamp_parser(candidate, self.provider.name, self.provider.model,
                                        lexicon_sha256(self.lexicon))


def parse(text, as_of_date, provider=None, lexicon=None, registry=None, fx_rates=None):
    """Parse and normalise in one step. Returns an executable, audited spec."""
    registry = registry or Registry()
    lexicon = lexicon or load_lexicon()
    parser = LLMParser(provider, lexicon, registry) if provider is not None else LexiconParser(lexicon, registry)
    spec = parser.parse(text, as_of_date)
    if fx_rates:
        spec['fx_rates'] = fx_rates
    return spec_module.normalise(spec, registry)
