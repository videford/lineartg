"""oauth token refresh + expiry

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa

revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("oauth_tokens", sa.Column("refresh_token", sa.Text(), nullable=True))
    op.add_column(
        "oauth_tokens",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("oauth_tokens", "expires_at")
    op.drop_column("oauth_tokens", "refresh_token")
