"""Condition resolution from numeric, validated inputs; unknown is never zero."""
import math


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def resolve(field, domains, signals, key='score'):
    parts = field.split('.')
    if parts[0] == 'domain' and len(parts) == 2:
        value = (domains.get(parts[1]) or {}).get(key)
    elif parts[0] == 'criterion' and len(parts) == 3:
        value = (domains.get(parts[1]) or {}).get('criteria', {}).get(parts[2])
    elif parts[0] == 'signal' and len(parts) == 2:
        value = signals.get(parts[1])
    else:
        raise ValueError(f'Unknown condition field: {field}')
    return float(value) if number(value) else None


def check_condition(condition, domains, signals, key='score'):
    value = resolve(condition['field'], domains, signals, key)
    if value is None:
        return None
    op, target = condition['op'], condition['value']
    if op == '>=':
        return value >= target
    if op == '<=':
        return value <= target
    if op == 'between':
        return target[0] <= value <= target[1]
    raise ValueError(f'Unknown condition operator: {op}')
