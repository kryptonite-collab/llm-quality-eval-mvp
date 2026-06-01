"""User-scoped slash command overrides + custom prompts (SQLite).

Each row is either:
  - A user-defined custom command (``prompt`` is set) — fires as
    ``send-as-message`` in chat, replacing ``/<name>`` with the stored prompt.
  - An override entry for a built-in command (``prompt`` is NULL) — exists
    only to record ``is_enabled=False`` for that built-in's name.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class UserSlashCommand(Base, TimestampMixin):
    """A custom or overridden slash command, scoped to one user."""

    __tablename__ = "user_slash_commands"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_slash_commands_user_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User] = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        kind = "custom" if self.prompt is not None else "builtin-override"
        return f"<UserSlashCommand({kind} name={self.name} enabled={self.is_enabled})>"
