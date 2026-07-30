"""create documents, queries, answers, citations, rate_limit_counters tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-30

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="processing"),
        sa.Column("failure_reason", sa.String(length=500), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    op.create_table(
        "queries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_queries_user_id", "queries", ["user_id"])

    op.create_table(
        "answers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "query_id",
            sa.String(length=36),
            sa.ForeignKey("queries.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("groundedness_status", sa.String(length=16), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("context_window_utilization", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "citations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("answer_id", sa.String(length=36), sa.ForeignKey("answers.id"), nullable=False),
        sa.Column(
            "document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False
        ),
        sa.Column("location_label", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_citations_answer_id", "citations", ["answer_id"])

    op.create_table(
        "rate_limit_counters",
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("counter_type", sa.String(length=16), primary_key=True),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("rate_limit_counters")
    op.drop_index("ix_citations_answer_id", table_name="citations")
    op.drop_table("citations")
    op.drop_table("answers")
    op.drop_index("ix_queries_user_id", table_name="queries")
    op.drop_table("queries")
    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_table("documents")
