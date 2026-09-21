"""Alembic environment.

The URL comes from `HARNESS_DATABASE_URL` (or `-x url=...`) rather than from
alembic.ini, so a migration cannot be applied to a database nobody named.

`render_as_batch` is on for SQLite, which cannot ALTER a column in place and
needs the table rebuilt. Without it a later migration would apply cleanly on
PostgreSQL and fail on the dialect the tests use.
"""
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.models import Base                      # noqa: E402
from db.session import database_url             # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def resolve_url() -> str:
    override = context.get_x_argument(as_dictionary=True).get('url')
    return database_url(override, allow_default=False)


def run_migrations_offline() -> None:
    context.configure(url=resolve_url(), target_metadata=target_metadata,
                      literal_binds=True, compare_type=True,
                      dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section['sqlalchemy.url'] = resolve_url()
    connectable = engine_from_config(section, prefix='sqlalchemy.', poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          compare_type=True,
                          render_as_batch=connection.dialect.name == 'sqlite')
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
