"""SyncSource model — stores RAG sync source configurations."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SyncSource(TimestampMixin, Base):
    """Configurable connector source for RAG document synchronization."""

    __tablename__ = "sync_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(20), nullable=False)
    collection_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    config: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    sync_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="new_only")
    schedule_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_sync_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
