"""Freeze-time validation of company_context.json.

A frozen run is the thing every later stage trusts, so the context is checked
once, at the moment it is locked, rather than being re-litigated by each agent.
Three kinds of error are caught here:

* shape and range — the schema, read under Draft 2020-12 with a format checker
  so `as_of_date` has to be a real calendar date and not merely ten characters;
* economic ordering — a terminal multiple set where bear exceeds base, or base
  exceeds bull, is not a scenario spread, and the DCF would silently produce a
  bear case above the bull case;
* identity — the context has to name this run and keep the cutoff it was
  initialised with.

Validation runs when a run is frozen. Runs frozen before this check existed stay
readable: nothing here is invoked on read.
"""
ORDER = ('bear', 'base', 'bull')


def _schema_errors(ctx, schema):
    import jsonschema
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
    for error in sorted(validator.iter_errors(ctx), key=lambda e: list(e.absolute_path)):
        where = '.'.join(str(p) for p in error.absolute_path) or '(root)'
        yield f'{where}: {error.message}'


def _multiple_order_errors(ctx, val_policy):
    """Check the multiples the DCF will actually use, not just the overrides.

    An override that sets bear alone can invert the ordering against the policy
    defaults it is merged into, so the effective set is what gets tested.
    """
    override = ((ctx.get('valuation_overrides') or {}).get('terminal_multiples') or {})
    effective = {}
    for case in ORDER:
        value = override.get(case)
        if value is None:
            value = (val_policy.get('terminal_multiples') or {}).get(case)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            effective[case] = float(value)
    errors = []
    for low, high in (('bear', 'base'), ('base', 'bull')):
        if low in effective and high in effective and effective[low] > effective[high]:
            errors.append(f'valuation_overrides.terminal_multiples: {low} ({effective[low]:g}) '
                          f'> {high} ({effective[high]:g}); scenario multiples must not invert')
    return errors


def _identity_errors(ctx, run_id, manifest):
    errors = []
    declared = ctx.get('ticker')
    lineage = ((manifest or {}).get('lineage') or {}).get('source_run')
    # fork-run copies the source context byte for byte on purpose, so a fork may
    # legitimately still carry the source ticker; anything else is the wrong company.
    if isinstance(declared, str) and declared.upper() not in {run_id.upper()} | ({lineage.upper()} if lineage else set()):
        expected = run_id.upper() + (f' (or forked source {lineage.upper()})' if lineage else '')
        errors.append(f'ticker: company_context says {declared!r} but this run is {expected}')
    initialised = (manifest or {}).get('as_of_date')
    if initialised and ctx.get('as_of_date') != initialised:
        errors.append(f"as_of_date: the run was initialised at {initialised} and the cutoff cannot move to "
                      f"{ctx.get('as_of_date')!r}; fork or init a new run instead")
    return errors


def validate(ctx, run_id, manifest, schema, val_policy):
    """Return every reason this context must not be frozen, in report order."""
    errors = list(_schema_errors(ctx, schema))
    errors += _multiple_order_errors(ctx, val_policy)
    errors += _identity_errors(ctx, run_id, manifest)
    return errors

