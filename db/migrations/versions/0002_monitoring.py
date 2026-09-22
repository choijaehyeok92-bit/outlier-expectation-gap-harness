"""Monitoring watch items and the append-only observation log.

Two tables with deliberately different lifecycles. `monitoring_watch_item` is
derived from agent reports and deep dives, so it is upserted and carries
`updated_at`. `monitoring_observation` is a record of what someone saw, so it
is append-only, has no `updated_at`, and `source` is NOT NULL — a number
nobody can trace is not evidence, and a status computed from one would be
worse than no status at all.

`server_default` uses `func.now()` rather than a literal so the DDL renders
correctly on PostgreSQL and SQLite alike; both tables are exercised on both.

Revision ID: 0002_monitoring
Revises: 0001_initial
Create Date: 2026-09-22 03:32:01.069444+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002_monitoring'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JSON_COLUMN = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')


def upgrade() -> None:
    op.create_table(
        'monitoring_observation',
        sa.Column('observation_id', sa.String(length=64), nullable=False),
        sa.Column('ticker', sa.String(length=64), nullable=False),
        sa.Column('watch_id', sa.String(length=64), nullable=False),
        sa.Column('value_text', sa.Text(), nullable=True),
        sa.Column('value_number', sa.Numeric(precision=38, scale=10, asdecimal=False),
                  nullable=True),
        sa.Column('unit', sa.String(length=64), nullable=True),
        sa.Column('triggered', sa.Boolean(), nullable=True),
        sa.Column('period', sa.String(length=255), nullable=True),
        sa.Column('as_of_date', sa.Date(), nullable=False),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('fact_or_estimate', sa.String(length=64), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('supersedes', sa.String(length=64), nullable=True),
        sa.Column('pre_analysis', sa.Boolean(), nullable=False),
        sa.Column('recorded_at_utc', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.CheckConstraint("fact_or_estimate IN ('fact','estimate','interpretation')",
                           name='ck_observation_fact_or_estimate'),
        sa.CheckConstraint(
            "source_type IN ('filing','ir','industry','secondary','market','other')",
            name='ck_observation_source_type'),
        sa.PrimaryKeyConstraint('observation_id'),
    )
    with op.batch_alter_table('monitoring_observation', schema=None) as batch_op:
        batch_op.create_index('ix_observation_ticker', ['ticker', 'as_of_date'], unique=False)
        batch_op.create_index('ix_observation_watch', ['watch_id', 'as_of_date'], unique=False)

    op.create_table(
        'monitoring_watch_item',
        sa.Column('watch_id', sa.String(length=64), nullable=False),
        sa.Column('ticker', sa.String(length=64), nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=True),
        sa.Column('kind', sa.String(length=64), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('source_kind', sa.String(length=64), nullable=False),
        sa.Column('source_ref', sa.String(length=64), nullable=True),
        sa.Column('as_of_date', sa.Date(), nullable=True),
        sa.Column('cadence', sa.String(length=64), nullable=True),
        sa.Column('direction_required', sa.String(length=64), nullable=True),
        sa.Column('warning_threshold', sa.Text(), nullable=True),
        sa.Column('thesis_break_threshold', sa.Text(), nullable=True),
        sa.Column('comparison', JSON_COLUMN, nullable=True),
        sa.Column('machine_checkable', sa.Boolean(), nullable=False),
        sa.Column('not_machine_checkable_reason', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.CheckConstraint("kind IN ('kpi','falsifier')", name='ck_watch_item_kind'),
        sa.PrimaryKeyConstraint('watch_id'),
    )
    with op.batch_alter_table('monitoring_watch_item', schema=None) as batch_op:
        batch_op.create_index('ix_watch_item_ticker', ['ticker', 'kind'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('monitoring_watch_item', schema=None) as batch_op:
        batch_op.drop_index('ix_watch_item_ticker')
    op.drop_table('monitoring_watch_item')
    with op.batch_alter_table('monitoring_observation', schema=None) as batch_op:
        batch_op.drop_index('ix_observation_watch')
        batch_op.drop_index('ix_observation_ticker')
    op.drop_table('monitoring_observation')
