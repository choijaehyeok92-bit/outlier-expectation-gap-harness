"""Recurring work, declared here rather than scattered across a crontab.

`cron` calls one line — `harness.py worker schedule` — and this decides what is
due. The cadence then lives in a version-controlled file that can be read and
tested, instead of in a machine's crontab that nobody diffs.

There is no scheduler process. Adding a long-lived daemon means adding
something whose liveness must itself be watched; this computes what is due,
queues it, and exits.

**The queue is the scheduler's state.** Nothing records a last-fired time,
because the idempotency key names the occurrence:
`schedule:nightly_db_sync:2026-09-22T03:00Z`. A cron that fires twice, a
machine that wakes late, an operator who runs the command by hand — all
compute the same key for the same occurrence, and `enqueue` returns the row
that already exists. Double-queueing is not prevented by care; it is not
expressible.

**UTC, and only UTC.** A local-time schedule fires twice on the day the clocks
go back and not at all on the day they go forward, which is precisely the case
an idempotent scheduler must not have.

**No catch-up by default.** A scheduler that was off for three days should not
push three nights of `db_sync`; what that job needs is the current state, once.
Only the most recent occurrence inside `lookback_hours` is queued, and anything
older is reported as missed rather than silently run.

The cron reader is deliberately small: a pure matcher plus a bounded backwards
scan over minutes. Computing "the next fire time" in closed form is where cron
implementations go wrong; asking "does this minute match?" ten thousand times
is dull and correct. Syntax outside the documented subset is refused — a
misread `L` that quietly means "every day" is worse than a rejected config.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

ALIASES = {
    '@hourly': '0 * * * *',
    '@daily': '0 0 * * *',
    '@midnight': '0 0 * * *',
    '@weekly': '0 0 * * 0',
    '@monthly': '0 0 1 * *',
}
FIELD_RANGES = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7))
FIELD_NAMES = ('minute', 'hour', 'day-of-month', 'month', 'day-of-week')
_TERM = re.compile(r'^(?:\*|(\d+)(?:-(\d+))?)(?:/(\d+))?$')


class CronError(ValueError):
    """The expression was not understood, and nothing was scheduled for it."""


def _field(text: str, index: int) -> set:
    low, high = FIELD_RANGES[index]
    values: set = set()
    for term in str(text).split(','):
        term = term.strip()
        match = _TERM.match(term)
        if not match:
            raise CronError(
                f'{FIELD_NAMES[index]} field {term!r} is not supported. This reader handles '
                '*, n, a-b, a,b, */n and a-b/n — nothing else, because a misread field that '
                'quietly means "always" is worse than a refused config.')
        start, end, step = match.group(1), match.group(2), match.group(3)
        step = int(step) if step else 1
        if step < 1:
            raise CronError(f'{FIELD_NAMES[index]} step in {term!r} must be at least 1')
        if start is None:
            first, last = low, high
        else:
            first = int(start)
            last = int(end) if end is not None else (high if match.group(3) else first)
        if not (low <= first <= high) or not (low <= last <= high) or last < first:
            raise CronError(f'{FIELD_NAMES[index]} range {term!r} is outside {low}-{high}')
        values.update(range(first, last + 1, step))
    if index == 4 and 7 in values:
        values.add(0)                       # cron accepts 7 as Sunday
    return values


def parse(expression: str) -> dict:
    """A cron expression as five value sets, or `CronError`."""
    text = str(expression or '').strip()
    text = ALIASES.get(text.lower(), text)
    fields = text.split()
    if len(fields) != 5:
        raise CronError(
            f'{expression!r} has {len(fields)} fields; a schedule needs 5 '
            f'({" ".join(FIELD_NAMES)}) or one of {sorted(ALIASES)}')
    parsed = {name: _field(field, index)
              for index, (name, field) in enumerate(zip(FIELD_NAMES, fields))}
    parsed['_dom_restricted'] = fields[2].strip() != '*'
    parsed['_dow_restricted'] = fields[4].strip() != '*'
    return parsed


def matches(parsed: dict, moment: datetime) -> bool:
    """Whether this minute fires.

    The day rule is cron's own and is a famous trap: when both day-of-month and
    day-of-week are restricted they are OR-ed, not AND-ed, so `0 0 1 * 1` runs
    on the first of the month *and* on every Monday. Kept because operators
    expect cron to behave like cron, and pinned by a test so it stays
    deliberate.
    """
    if moment.minute not in parsed['minute'] or moment.hour not in parsed['hour']:
        return False
    if moment.month not in parsed['month']:
        return False
    day_of_month = moment.day in parsed['day-of-month']
    day_of_week = ((moment.weekday() + 1) % 7) in parsed['day-of-week']
    if parsed['_dom_restricted'] and parsed['_dow_restricted']:
        return day_of_month or day_of_week
    return day_of_month and day_of_week


def _floor_minute(moment: datetime) -> datetime:
    return moment.astimezone(timezone.utc).replace(second=0, microsecond=0)


def last_occurrence(expression: str, now: datetime, lookback_hours: int = 48) -> Optional[datetime]:
    """The most recent firing at or before `now`, or None within the window.

    A backwards minute scan rather than closed-form arithmetic. 48 hours is
    2,880 comparisons of five set lookups; the clarity is worth more than the
    microseconds.
    """
    parsed = parse(expression)
    moment = _floor_minute(now)
    for _ in range(int(lookback_hours) * 60 + 1):
        if matches(parsed, moment):
            return moment
        moment -= timedelta(minutes=1)
    return None


def occurrences_since(expression: str, since: datetime, now: datetime) -> list:
    """Every firing in `(since, now]`, oldest first. For catch-up and for reporting."""
    parsed = parse(expression)
    moment = _floor_minute(since) + timedelta(minutes=1)
    end = _floor_minute(now)
    found = []
    while moment <= end:
        if matches(parsed, moment):
            found.append(moment)
        moment += timedelta(minutes=1)
    return found


def stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%MZ')


def settings(config: dict) -> dict:
    return config.get('schedules') or {}


def entries(config: dict) -> list:
    return [entry for entry in (settings(config).get('entries') or [])
            if entry.get('enabled', True)]


def render_payload(payload, moment: datetime):
    """Substitute `{date}` and `{occurrence}`. Two placeholders, no expressions."""
    replacements = {'{date}': moment.astimezone(timezone.utc).strftime('%Y-%m-%d'),
                    '{occurrence}': stamp(moment)}
    if isinstance(payload, str):
        for token, value in replacements.items():
            payload = payload.replace(token, value)
        return payload
    if isinstance(payload, dict):
        return {key: render_payload(value, moment) for key, value in payload.items()}
    if isinstance(payload, list):
        return [render_payload(value, moment) for value in payload]
    return payload


def idempotency_key(schedule_id: str, moment: datetime, config: dict) -> str:
    template = settings(config).get('idempotency_key_template',
                                    'schedule:{schedule_id}:{occurrence}')
    return template.replace('{schedule_id}', schedule_id).replace('{occurrence}', stamp(moment))


def validate(config: dict) -> list:
    """Every problem in the schedule block, so a bad entry is found before it is due."""
    from . import handlers
    problems = []
    seen = set()
    declared = set((config.get('kinds') or {}))
    for entry in (settings(config).get('entries') or []):
        schedule_id = entry.get('id')
        if not schedule_id:
            problems.append('a schedule entry has no id')
            continue
        if schedule_id in seen:
            problems.append(f'{schedule_id}: duplicate schedule id; the idempotency key '
                            'would collide and one of them would never run')
        seen.add(schedule_id)
        if entry.get('kind') not in declared:
            problems.append(f'{schedule_id}: kind {entry.get("kind")!r} is not declared in '
                            f'config/workers.json kinds ({sorted(declared)})')
        try:
            parse(entry.get('cron', ''))
        except CronError as error:
            problems.append(f'{schedule_id}: {error}')
        problem = handlers.payload_is_safe(entry.get('payload') or {})
        if problem:
            problems.append(f'{schedule_id}: {problem}')
    return problems


def plan(config: dict, now: Optional[datetime] = None) -> list:
    """What each schedule would queue right now, and why — without queuing it."""
    now = now or datetime.now(timezone.utc)
    policy = settings(config)
    lookback = int(policy.get('lookback_hours', 48))
    rows = []
    for entry in entries(config):
        row = {'schedule_id': entry['id'], 'kind': entry.get('kind'),
               'cron': entry.get('cron'), 'priority': entry.get('priority', 100),
               'description': entry.get('description')}
        try:
            moment = last_occurrence(entry['cron'], now, lookback)
        except CronError as error:
            rows.append({**row, 'due': False, 'reason': f'unreadable schedule: {error}'})
            continue
        if moment is None:
            rows.append({**row, 'due': False,
                         'reason': f'no occurrence in the last {lookback}h; if the scheduler '
                                   'was off longer than that, the missed runs are not '
                                   'back-filled'})
            continue
        rows.append({**row, 'due': True, 'occurrence': stamp(moment),
                     'idempotency_key': idempotency_key(entry['id'], moment, config),
                     'payload': render_payload(entry.get('payload') or {}, moment)})
    return rows


def run(session, config: dict, now: Optional[datetime] = None,
        only: Optional[list] = None) -> dict:
    """Queue every due occurrence. Running this twice queues nothing the second time."""
    from . import queue as job_queue
    problems = validate(config)
    if problems:
        raise CronError('config/workers.json schedules are not usable:\n  '
                        + '\n  '.join(problems))

    rows = [row for row in plan(config, now)
            if not only or row['schedule_id'] in set(only)]
    queued, skipped, already = [], [], []
    for row in rows:
        if not row['due']:
            skipped.append({k: row[k] for k in ('schedule_id', 'kind', 'reason')})
            continue
        # Asked before enqueueing, so the report can say "already queued"
        # rather than reporting a no-op as fresh work.
        existing = job_queue.find_by_key(session, row['idempotency_key'])
        job = job_queue.enqueue(session, row['kind'], row['payload'], config,
                                idempotency_key=row['idempotency_key'],
                                priority=int(row.get('priority') or 100))
        record = {'schedule_id': row['schedule_id'], 'kind': row['kind'],
                  'occurrence': row['occurrence'], 'job_id': job.job_id,
                  'idempotency_key': row['idempotency_key']}
        (already if existing is not None else queued).append(record)
    return {'now': stamp(_floor_minute(now or datetime.now(timezone.utc))),
            'queued': queued, 'already_queued': already, 'not_due': skipped,
            'summary': {'queued': len(queued), 'already_queued': len(already),
                        'not_due': len(skipped)}}
