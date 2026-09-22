"""ScreeningSpec: build, validate and normalise.

The spec is the boundary. Above it a language model may work in prose; below it
everything is deterministic. So every spec — hand-written, API-supplied or
model-produced — passes through here before it can touch data: JSON Schema
first, then the registry allowlist, then unit normalisation.

Normalisation is where a mistake would be silent, so it is explicit. A ratio
field takes a decimal fraction and a value above 1 is rejected rather than
divided by 100. A currency threshold is converted only with a rate the caller
supplied for the as-of date; with no rate the clause becomes an unresolved
condition and stops filtering, because a screen that quietly used last year's
exchange rate is worse than one that admits it cannot answer.
"""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .fields import Registry, ROOT
from .units import UnitError, convert

SCHEMA_PATH = ROOT / 'schemas' / 'screening_spec.schema.json'
NUMERIC_OPERATORS = {'<', '<=', '>', '>=', 'between'}
EQUALITY_OPERATORS = {'=', '==', '!='}
SET_OPERATORS = {'in', 'not_in'}
DEFAULT_LIMIT = 50


class SpecError(ValueError):
    """A spec that cannot be executed as written. Never silently repaired."""


def load_schema(path=None):
    return json.loads(Path(path or SCHEMA_PATH).read_text(encoding='utf-8'))


# What makes two screens the same screen: the question, not the moment it was
# asked. Parser metadata carries a wall-clock timestamp, so hashing it would
# give the same query a new identity on every call and defeat the immutable
# store's deduplication.
IDENTITY_FIELDS = ('as_of_date', 'universe', 'filters', 'sort', 'limit',
                   'missing_policy', 'requires_harness_run', 'unresolved_conditions', 'fx_rates')


def spec_id(spec):
    payload = {k: spec.get(k) for k in IDENTITY_FIELDS}
    source = spec.get('source') or {}
    payload['source'] = {'kind': source.get('kind'), 'text': source.get('text')}
    return 'SPEC-' + hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()[:16].upper()


def empty(as_of_date, source_kind='manual'):
    return {'schema_version': '1.0', 'as_of_date': as_of_date,
            'source': {'kind': source_kind},
            'universe': {}, 'filters': {'op': 'and', 'clauses': []},
            'sort': [], 'limit': DEFAULT_LIMIT, 'missing_policy': 'exclude',
            'requires_harness_run': False, 'unresolved_conditions': []}


def validate_schema(spec, schema=None):
    import jsonschema
    jsonschema.validate(spec, schema or load_schema())
    return spec


def _walk(group):
    """Yield (parent_group, index, clause) for every leaf filter in the tree."""
    for index, clause in enumerate(group.get('clauses') or []):
        if 'op' in clause:
            yield from _walk(clause)
        else:
            yield group, index, clause


def iter_filters(spec):
    return [clause for _, _, clause in _walk(spec.get('filters') or {'op': 'and', 'clauses': []})]


_DROP = object()


def _normalise_value(field_id, clause, registry, fx_rates, unresolved):
    """Bring one clause's value into the field's own unit, or return _DROP.

    _DROP means the clause could not be made executable and has been recorded
    as an unresolved condition. It is never turned into a default value.
    """
    unit = registry.unit(field_id)
    dtype = registry.dtype(field_id)
    value = clause.get('value')

    if dtype == 'number' and unit == 'ratio':
        for item in (value if isinstance(value, list) else [value]):
            if isinstance(item, (int, float)) and not isinstance(item, bool) and abs(item) > 1.5:
                raise SpecError(
                    f'{field_id}: ratio fields take a decimal fraction; {item} looks like a percent. '
                    'Write 0.15 for 15%.')
        return value

    if dtype == 'number' and unit == 'usd':
        currency = (clause.get('currency') or '').upper() or None
        if currency and currency != 'USD':
            try:
                converted = ([convert(v, currency, 'USD', fx_rates) for v in value]
                             if isinstance(value, list)
                             else convert(value, currency, 'USD', fx_rates))
            except UnitError as error:
                unresolved.append({
                    'text': clause.get('origin_text') or f"{field_id} {clause['operator']} {value} {currency}",
                    'reason': 'missing_fx_rate', 'suggested_field': field_id,
                    'detail': (f'{error}. Supply fx_rates["{currency}"].per_usd for the run\'s as-of date, '
                               'or restate the threshold in USD.')})
                return _DROP
            clause['currency'] = 'USD'
            clause['converted_from'] = currency
            return converted
    return value


def _check_clause(clause, registry, fx_rates, unresolved, active):
    """True when the clause is executable; it is recorded as unresolved otherwise."""
    field_id = clause['field']
    if field_id not in registry:
        unresolved.append({'text': clause.get('origin_text') or field_id,
                           'reason': 'no_mapped_field', 'suggested_field': None,
                           'detail': f'{field_id} is not declared in config/screening_fields.json'})
        return False

    operator, dtype = clause['operator'], registry.dtype(field_id)
    if dtype == 'string' and operator in NUMERIC_OPERATORS:
        unresolved.append({'text': clause.get('origin_text') or field_id,
                           'reason': 'unsupported_operator', 'suggested_field': field_id,
                           'detail': f'{operator} is not defined on a {dtype} field'})
        return False
    if operator in SET_OPERATORS and not isinstance(clause['value'], list):
        raise SpecError(f'{field_id}: operator {operator} requires a list value')
    if operator == 'between' and (not isinstance(clause['value'], list) or len(clause['value']) != 2):
        raise SpecError(f'{field_id}: between requires a two-element list')
    if not any(backend in active for backend in (registry.get(field_id).get('backends') or [])):
        unresolved.append({'text': clause.get('origin_text') or field_id,
                           'reason': 'backend_unavailable', 'suggested_field': field_id,
                           'detail': f'{field_id} needs a backend that is not active yet: '
                                     f"{registry.get(field_id).get('backends')}"})
        return False

    normalised = _normalise_value(field_id, clause, registry, fx_rates, unresolved)
    if normalised is _DROP:
        return False
    clause['value'] = normalised
    return True


def _prune(group, registry, fx_rates, unresolved, active):
    """Depth-first rebuild keeping only executable clauses. An emptied group is dropped."""
    clauses = []
    for clause in group.get('clauses') or []:
        if 'op' in clause:
            child = _prune(clause, registry, fx_rates, unresolved, active)
            if child['clauses']:
                clauses.append(child)
        elif _check_clause(clause, registry, fx_rates, unresolved, active):
            clauses.append(clause)
    return {'op': group.get('op', 'and'), 'clauses': clauses}


def normalise(spec, registry=None, schema=None):
    """Validate against schema and registry, normalise units, compute derived flags.

    Returns a new spec; the input is not mutated. Clauses that cannot be made
    executable are moved into `unresolved_conditions` rather than dropped
    silently, so a screen always says what it did not apply.
    """
    registry = registry or Registry()
    schema = schema or load_schema()
    spec = copy.deepcopy(spec)
    spec.setdefault('schema_version', '1.0')
    spec.setdefault('universe', {})
    spec.setdefault('filters', {'op': 'and', 'clauses': []})
    spec.setdefault('missing_policy', 'exclude')
    spec.setdefault('unresolved_conditions', [])
    spec.setdefault('sort', [])
    spec.setdefault('limit', DEFAULT_LIMIT)
    validate_schema(spec, schema)

    unresolved = list(spec['unresolved_conditions'])
    spec['filters'] = _prune(spec['filters'], registry, spec.get('fx_rates') or {},
                             unresolved, registry.active_backends())
    spec['unresolved_conditions'] = unresolved
    spec['requires_harness_run'] = bool(spec.get('requires_harness_run')) or any(
        registry.requires_harness_run(clause['field']) for clause in iter_filters(spec))
    for row in spec.get('sort') or []:
        if row['field'] not in registry:
            raise SpecError(f"sort field {row['field']} is not in the registry")
    spec['spec_id'] = spec_id(spec)
    validate_schema(spec, schema)
    return spec


def stamp_parser(spec, provider, model, lexicon_sha256=None):
    source = spec.setdefault('source', {'kind': 'natural_language'})
    source['parser'] = {'provider': provider, 'model': model,
                        'parsed_at_utc': datetime.now(timezone.utc).isoformat(),
                        'lexicon_sha256': lexicon_sha256}
    return spec
