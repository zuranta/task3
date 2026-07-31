"""create comparison_runs table

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-30

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comparison_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("version_a_label", sa.String(length=255), nullable=False),
        sa.Column("version_b_label", sa.String(length=255), nullable=False),
        sa.Column("langsmith_experiment_id_a", sa.String(length=255), nullable=True),
        sa.Column("langsmith_experiment_id_b", sa.String(length=255), nullable=True),
        sa.Column("aggregate_score_a", sa.JSON(), nullable=True),
        sa.Column("aggregate_score_b", sa.JSON(), nullable=True),
        sa.Column("winner", sa.String(length=8), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="running"),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("comparison_runs")
