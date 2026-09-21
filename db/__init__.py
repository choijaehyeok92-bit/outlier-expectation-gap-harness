"""Database layer: schema, migrations, sync and the read repository.

The point worth stating first is what this layer is *not*. It is not the
source of truth for a harness run. `runs/<RUN_ID>/aggregate.json` is, and the
`harness_run` table is an index over it, bound to the file by
`aggregate_sha256`. A reader who wants to know what the harness decided reads
the artifact; a reader who wants to find it quickly reads the table.

Everything here is optional. The harness, the screener and the deep dive all
work with no database configured; `HARNESS_DATABASE_URL` turns this on.
"""
from .session import DEFAULT_SQLITE_URL, database_url, engine_for, session_scope

__all__ = ['DEFAULT_SQLITE_URL', 'database_url', 'engine_for', 'session_scope']
