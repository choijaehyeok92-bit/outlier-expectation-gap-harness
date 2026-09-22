"""Give `job` what a queue actually needs: leases, backoff and a claim index.

The table has existed since 0001 with `status`, `attempts` and an
`idempotency_key`, which is enough to *record* work and not enough to hand it
out. Three things were missing.

`available_at` — a failed job that returns to `queued` immediately retries
against whatever broke it as fast as the loop spins. Backoff is a timestamp,
not a sleep.

`lease_expires_at` and `worker_id` — a worker that dies mid-job leaves its row
`running` forever. With a lease the row becomes claimable again, and the
worker id says who had it.

`max_attempts` per row — the config's default belongs to the queue, but a
single expensive job may deserve a different cap than a cheap one, and the cap
has to survive a config edit.

`started_at` / `finished_at` are for reading the table afterwards; `priority`
orders the claim. The partial index is on `(status, available_at)`, which is
exactly the claim predicate.

Existing rows get sensible defaults and keep their history.

Revision ID: 0003_job_queue
Revises: 0002_monitoring
Create Date: 2026-09-22 04:05:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0003_job_queue'
down_revision: Union[str, None] = '0002_monitoring'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('job', schema=None) as batch_op:
        # server_default so rows written before this migration are claimable
        # rather than stuck with a NULL nobody compares against.
        batch_op.add_column(sa.Column('max_attempts', sa.Integer(), nullable=False,
                                      server_default='3'))
        batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=False,
                                      server_default='100'))
        batch_op.add_column(sa.Column('available_at', sa.DateTime(timezone=True),
                                      nullable=False, server_default=sa.func.now()))
        batch_op.add_column(sa.Column('lease_expires_at', sa.DateTime(timezone=True),
                                      nullable=True))
        batch_op.add_column(sa.Column('worker_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('started_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index('ix_job_claimable', ['status', 'available_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('job', schema=None) as batch_op:
        batch_op.drop_index('ix_job_claimable')
        for column in ('finished_at', 'started_at', 'worker_id', 'lease_expires_at',
                       'available_at', 'priority', 'max_attempts'):
            batch_op.drop_column(column)
