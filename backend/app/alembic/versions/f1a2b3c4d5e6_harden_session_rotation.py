"""harden session rotation

Revision ID: f1a2b3c4d5e6
Revises: e2f4a6b8c0d1
Create Date: 2026-11-05 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import Column, DateTime, Text


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e2f4a6b8c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tokens issued before this revision have no sid claim and can no longer be used.
    op.execute("DELETE FROM session")
    op.add_column("session", Column("previous_refresh_token", Text, nullable=True))
    op.add_column(
        "session", Column("rotated_at", DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "session",
        Column("absolute_expires_at", DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("session", "absolute_expires_at")
    op.drop_column("session", "rotated_at")
    op.drop_column("session", "previous_refresh_token")
