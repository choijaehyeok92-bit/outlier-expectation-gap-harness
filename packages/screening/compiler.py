"""The deterministic compiler: a validated ScreeningSpec becomes a predicate.

No language model reaches this file. It takes a spec that already passed the
schema and the registry allowlist and evaluates it against normalised rows.

The one idea worth stating plainly is that a filter has three outcomes, not
two. A row can pass, fail, or be *unknown* because the company has no value for
that field. Unknown is not false and it is certainly not zero: a company that
never disclosed net cash has not thereby reported zero net cash. So clauses
evaluate in three-valued (Kleene) logic — `and` is false if any clause is
false, unknown if any is unknown, true otherwise — and only at the very end
does `missing_policy` decide what an unknown row deserves:

  exclude        the row does not appear in results (the default, and the only
                 one that cannot mislead)
  require_review the row appears in a separate `needs_review` bucket, never
                 mixed into the ranked list
  include        the row is treated as passing; an explicit, recorded choice

The same three-valued rule is why `!=` on a missing value is unknown rather
than true.
"""
UNKNOWN = None
_MISSING = object()


class CompileError(ValueError):
    pass


def _value(row, field_id):
    """Field lookup. `domain.x` and `axis.x` read the row's nested maps."""
    if '.' in field_id:
        head, tail = field_id.split('.', 1)
        container = row.get({'domain': 'domain_scores', 'axis': 'axis_scores'}.get(head, head))
        if not isinstance(container, dict):
            return _MISSING
        return container.get(tail, _MISSING)
    return row.get(field_id, _MISSING)


def _comparable(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def evaluate_clause(clause, row):
    """Three-valued evaluation of a single filter. Returns True, False or None."""
    value = _value(row, clause['field'])
    if value is _MISSING or value is None:
        return UNKNOWN
    operator, target = clause['operator'], clause['value']

    if operator in ('=', '=='):
        return value == target
    if operator == '!=':
        return value != target
    if operator == 'in':
        return value in target
    if operator == 'not_in':
        return value not in target

    if operator == 'between':
        if not _comparable(value) or not all(_comparable(x) for x in target):
            return UNKNOWN
        low, high = sorted(target)
        return low <= value <= high

    if not _comparable(value) or not _comparable(target):
        return UNKNOWN
    if operator == '<':
        return value < target
    if operator == '<=':
        return value <= target
    if operator == '>':
        return value > target
    if operator == '>=':
        return value >= target
    raise CompileError(f'unknown operator {operator}')


def evaluate_group(group, row):
    """Kleene AND/OR over a clause tree."""
    results = [evaluate_group(c, row) if 'op' in c else evaluate_clause(c, row)
               for c in (group.get('clauses') or [])]
    if not results:
        return True
    if group.get('op') == 'or':
        if any(r is True for r in results):
            return True
        return UNKNOWN if any(r is UNKNOWN for r in results) else False
    if any(r is False for r in results):
        return False
    return UNKNOWN if any(r is UNKNOWN for r in results) else True


def explain(group, row):
    """Per-clause outcome, for the UI to show why a row passed or did not."""
    rows = []
    for clause in (group.get('clauses') or []):
        if 'op' in clause:
            rows.extend(explain(clause, row))
        else:
            value = _value(row, clause['field'])
            rows.append({'field': clause['field'], 'operator': clause['operator'],
                         'threshold': clause['value'],
                         'value': None if value is _MISSING else value,
                         'missing': value is _MISSING or value is None,
                         'result': evaluate_clause(clause, row)})
    return rows


def _universe_ok(spec, row):
    universe = spec.get('universe') or {}
    for key, field in (('jurisdictions', 'jurisdiction'), ('exchanges', 'exchange'),
                       ('industries', 'industry'), ('sectors', 'sector'), ('tickers', 'ticker')):
        wanted = universe.get(key)
        if not wanted:
            continue
        value = row.get(field)
        if value is None or value not in wanted:
            return False
    return True


def _sort_key(spec, row):
    keys = []
    for order in spec.get('sort') or []:
        value = _value(row, order['field'])
        missing = value is _MISSING or value is None
        # Missing always sorts last, whichever direction was asked for.
        if missing:
            keys.append((1, 0))
        else:
            numeric = value if _comparable(value) else 0
            keys.append((0, -numeric if order['direction'] == 'desc' else numeric))
    keys.append((0, row.get('ticker') or ''))
    return keys


def run(spec, rows):
    """Execute a normalised spec over normalised rows.

    Returns a result document: matched rows (ranked), rows held for review, the
    rows excluded for a missing value, and the per-clause explanation for every
    row that was considered.
    """
    as_of = spec.get('as_of_date')
    policy = spec.get('missing_policy', 'exclude')
    matched, review, excluded_missing, post_cutoff = [], [], [], []

    for row in rows:
        # The as-of date is an absolute cutoff: a run dated after it cannot be
        # used to answer a question asked as of an earlier date.
        if as_of and (row.get('as_of_date') or '') > as_of:
            post_cutoff.append({'ticker': row.get('ticker'), 'run_id': row.get('run_id'),
                                'as_of_date': row.get('as_of_date')})
            continue
        if not _universe_ok(spec, row):
            continue
        verdict = evaluate_group(spec.get('filters') or {'op': 'and', 'clauses': []}, row)
        record = {**row, 'match_explain': explain(spec.get('filters') or {'op': 'and', 'clauses': []}, row)}
        if verdict is True:
            matched.append(record)
        elif verdict is UNKNOWN:
            if policy == 'include':
                matched.append({**record, 'included_on_missing_data': True})
            elif policy == 'require_review':
                review.append(record)
            else:
                excluded_missing.append(record)

    matched.sort(key=lambda r: _sort_key(spec, r))
    review.sort(key=lambda r: _sort_key(spec, r))
    limit = int(spec.get('limit') or len(matched))
    return {'spec_id': spec.get('spec_id'), 'as_of_date': as_of,
            'missing_policy': policy,
            'considered': len(rows), 'matched_count': len(matched),
            'results': matched[:limit],
            'needs_review': review,
            'excluded_missing_data': [{'ticker': r.get('ticker'), 'run_id': r.get('run_id'),
                                       'missing_fields': [c['field'] for c in r['match_explain'] if c['missing']]}
                                      for r in excluded_missing],
            'excluded_post_cutoff': post_cutoff,
            'unresolved_conditions': spec.get('unresolved_conditions') or [],
            'requires_harness_run': bool(spec.get('requires_harness_run'))}
