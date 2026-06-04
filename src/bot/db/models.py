from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Role(str, enum.Enum):
    """Bot-level role. Independent from Linear's own permissions —
    rank-and-file members have no Linear account at all."""

    member = "member"
    lead = "lead"
    admin = "admin"  # PM / workspace owner


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(Base, TimestampMixin):
    """A Telegram user mapped to a virtual Linear identity.

    `linear_label` (e.g. "tg:ivan") is how we represent assignment to a
    seat-less member: issues get this label, and /my filters by it."""

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(128))
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    linear_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lang: Mapped[str] = mapped_column(String(8), default="ru")
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.member)
    is_active: Mapped[bool] = mapped_column(default=True)
    # True once the user has entered their real first/last name via /start.
    registered: Mapped[bool] = mapped_column(default=False)


class OAuthToken(Base, TimestampMixin):
    """One token per Linear workspace, obtained via actor=app OAuth.
    All mutations are performed with this token + createAsUser."""

    __tablename__ = "oauth_tokens"

    workspace_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    access_token: Mapped[str] = mapped_column(Text)
    scope: Mapped[str | None] = mapped_column(String(256), nullable=True)
    app_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Project(Base, TimestampMixin):
    """Local cache of Linear projects — for names, pickers, and lead scoping.
    Refreshed via /syncprojects."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Linear project id
    name: Mapped[str] = mapped_column(String(256))
    team_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)


class ProjectLead(Base, TimestampMixin):
    """Assigns a Telegram user as lead of a specific Linear project. A user can
    lead several projects; being a lead is a bot role and needs no Linear seat."""

    __tablename__ = "project_leads"
    __table_args__ = (
        UniqueConstraint("telegram_id", "project_id", name="uq_lead_project"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )


class ChatBinding(Base, TimestampMixin):
    """Links a Telegram group chat to a default Linear team. The chat is
    shared (not per-project), so the project is chosen at task-creation time."""

    __tablename__ = "chat_bindings"

    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    linear_team_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class IssueLink(Base, TimestampMixin):
    """Maps a Linear issue to the Telegram message(s) that reference it,
    so Linear webhook events can be routed back to the right chat/thread,
    and replies can become Linear comments."""

    __tablename__ = "issue_links"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    linear_issue_id: Mapped[str] = mapped_column(String(64), index=True)
    linear_issue_identifier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger)


class WebhookDedup(Base):
    """Idempotency guard for Linear webhook deliveries."""

    __tablename__ = "webhook_dedup"

    delivery_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
