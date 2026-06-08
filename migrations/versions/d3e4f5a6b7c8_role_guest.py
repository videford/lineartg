"""add 'guest' value to the role enum

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-06-05
"""
from alembic import op

revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block — use the
    # autocommit block so Alembic commits the surrounding migration first.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'guest' BEFORE 'member'")


def downgrade() -> None:
    # Postgres cannot drop a single enum value; leaving 'guest' in place is safe.
    pass
