"""Engine and session plumbing.

`HARNESS_DATABASE_URL` decides everything. Unset means no database, and every
other layer already works that way — the screener reads files, the harness
reads its runs. Setting it turns the database on for the commands that offer
it; nothing starts depending on it silently.

The SQLite fallback is not a second production target. It exists so the schema,
the migrations and the sync can be exercised in a unit test with no service
running, which is the difference between a migration checked on every commit
and one checked when somebody remembers.
"""
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
ENV_VAR = 'HARNESS_DATABASE_URL'
DEFAULT_SQLITE_URL = f'sqlite+pysqlite:///{ROOT / "data" / "harness.sqlite3"}'


class DatabaseNotConfigured(RuntimeError):
    """Raised instead of quietly inventing a database nobody asked for."""


def database_url(url: Optional[str] = None, allow_default: bool = False) -> str:
    if url:
        return url
    configured = os.environ.get(ENV_VAR)
    if configured:
        return configured
    if allow_default:
        Path(ROOT / 'data').mkdir(parents=True, exist_ok=True)
        return DEFAULT_SQLITE_URL
    raise DatabaseNotConfigured(
        f'{ENV_VAR} is not set. Point it at PostgreSQL '
        '(postgresql+psycopg://user@host/db) or pass --sqlite to use a local file.')


def engine_for(url: Optional[str] = None, allow_default: bool = False, echo: bool = False) -> Engine:
    resolved = database_url(url, allow_default)
    engine = create_engine(resolved, echo=echo, future=True,
                           **({'connect_args': {'check_same_thread': False}}
                              if resolved.startswith('sqlite') else {}))
    if resolved.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def _enforce_foreign_keys(connection, _record):
            # SQLite ignores foreign keys unless asked, and a test that skips
            # them is not testing the schema the production database has.
            cursor = connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()
    return engine


def session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, class_=Session, future=True)


@contextmanager
def session_scope(engine: Engine):
    """A transaction that commits on success and rolls back on anything else."""
    session = session_factory(engine)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def is_configured() -> bool:
    return bool(os.environ.get(ENV_VAR))
