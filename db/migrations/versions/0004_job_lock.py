"""Resource locks, so two jobs cannot write the same run at once.

The queue already stops two workers claiming the same *row*. It says nothing
about two different rows touching the same `runs/<ID>/`, and they do: a
full-harness job rewrites `aggregate.json` while a deep dive reads it, and
`harness_core.dump_json` is a plain `write_text`, so a reader can see half a
file.

`(namespace, resource)` is UNIQUE, which is where the real guarantee lives —
the database refuses the second holder rather than the application hoping it
checked first. `ON DELETE CASCADE` means deleting a job cannot leave a lock
nobody will release.

Revision ID: 0004_job_lock
Revises: 0003_job_queue
Create Date: 2026-09-22 04:40:00.000000+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0004_job_lock'
down_revision: Union[str, None] = '0003_job_queue'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'job_lock',
        sa.Column('lock_id', sa.Integer(), nullable=False),
        sa.Column('namespace', sa.String(length=64), nullable=False),
        sa.Column('resource', sa.String(length=255), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('acquired_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['job.job_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('lock_id'),
        sa.UniqueConstraint('namespace', 'resource', name='uq_job_lock_resource'),
    )
    with op.batch_alter_table('job_lock', schema=None) as batch_op:
        batch_op.create_index('ix_job_lock_job', ['job_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('job_lock', schema=None) as batch_op:
        batch_op.drop_index('ix_job_lock_job')
    op.drop_table('job_lock')
