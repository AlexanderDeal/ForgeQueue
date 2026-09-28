"""add queue job statuses

Revision ID: 7c1a5b4d9e20
Revises: 2e6ad68cf4e8
"""

from collections.abc import Sequence

from alembic import op


revision: str = "7c1a5b4d9e20"
down_revision: str | None = "2e6ad68cf4e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_jobs_status", "jobs", type_="check")
    op.create_check_constraint(
        "ck_jobs_status",
        "jobs",
        "status IN ('PENDING', 'QUEUED', 'PROCESSING', 'COMPLETED', "
        "'FAILED', 'RETRYING')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_jobs_status", "jobs", type_="check")
    op.create_check_constraint(
        "ck_jobs_status",
        "jobs",
        "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')",
    )
