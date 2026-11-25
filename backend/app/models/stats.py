from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TitleStats(Base):
    __tablename__ = "title_stats"

    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True)
    unique_viewers: Mapped[int] = mapped_column(Integer, default=0)
    completions: Mapped[int] = mapped_column(Integer, default=0)
    last_watched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class TitleViewer(Base):
    __tablename__ = "title_viewers"

    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    first_finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
