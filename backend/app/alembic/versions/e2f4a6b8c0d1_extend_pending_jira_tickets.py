"""Extend pending Jira tickets for traceability and idempotency

Revision ID: e2f4a6b8c0d1
Revises: 9db8d2a36591
Create Date: 2026-06-19 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e2f4a6b8c0d1"
down_revision: Union[str, Sequence[str], None] = "9db8d2a36591"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add traceability columns and status check constraint."""
    op.add_column(
        "pending_jira_tickets",
        sa.Column("conversation_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "pending_jira_tickets",
        sa.Column("jira_key", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "pending_jira_tickets",
        sa.Column(
            "approved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "pending_jira_tickets",
        sa.Column("approved_by", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_pending_jira_tickets_conversation_id",
        "pending_jira_tickets",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_pending_jira_tickets_approved_by",
        "pending_jira_tickets",
        "users",
        ["approved_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_pending_jira_tickets_conversation_id"),
        "pending_jira_tickets",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pending_jira_tickets_jira_key"),
        "pending_jira_tickets",
        ["jira_key"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_pending_jira_tickets_status",
        "pending_jira_tickets",
        "status IN ('pending', 'processing', 'approved', 'rejected')",
    )


def downgrade() -> None:
    """Remove traceability columns and status check constraint."""
    op.drop_constraint(
        "ck_pending_jira_tickets_status",
        "pending_jira_tickets",
        type_="check",
    )
    op.drop_index(
        op.f("ix_pending_jira_tickets_jira_key"),
        table_name="pending_jira_tickets",
    )
    op.drop_index(
        op.f("ix_pending_jira_tickets_conversation_id"),
        table_name="pending_jira_tickets",
    )
    op.drop_constraint(
        "fk_pending_jira_tickets_approved_by",
        "pending_jira_tickets",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_pending_jira_tickets_conversation_id",
        "pending_jira_tickets",
        type_="foreignkey",
    )
    op.drop_column("pending_jira_tickets", "approved_by")
    op.drop_column("pending_jira_tickets", "approved_at")
    op.drop_column("pending_jira_tickets", "jira_key")
    op.drop_column("pending_jira_tickets", "conversation_id")
