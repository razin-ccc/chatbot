"""add conversation_id to documents

Revision ID: d8e9f0a1b2c3
Revises: b7c8d9e0f1a2
Create Date: 2026-06-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=True),
    )
    # Legacy global documents cannot be scoped to a conversation.
    op.execute("DELETE FROM documents WHERE conversation_id IS NULL")
    op.alter_column("documents", "conversation_id", nullable=False)
    op.create_foreign_key(
        "fk_documents_conversations_id",
        "documents",
        "conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_documents_conversation_id", "documents", ["conversation_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_documents_conversation_id", table_name="documents")
    op.drop_constraint("fk_documents_conversations_id", "documents", type_="foreignkey")
    op.drop_column("documents", "conversation_id")
