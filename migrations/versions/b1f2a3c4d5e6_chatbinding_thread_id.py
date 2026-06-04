"""chatbinding thread_id

Revision ID: b1f2a3c4d5e6
Revises: 3f08854ccd2a
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa

revision = "b1f2a3c4d5e6"
down_revision = "3f08854ccd2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_bindings", sa.Column("thread_id", sa.BigInteger(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("chat_bindings", "thread_id")
