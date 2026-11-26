from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.catalog import Episode, Title


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WatchHistory(Base):
    __tablename__ = "watch_history"
    __table_args__ = (
        UniqueConstraint("user_id", "title_id", "episode_id", postgresql_nulls_not_distinct=True),
        Index("ix_watch_history_user_id_last_watched", "user_id", "last_watched"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"), index=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"))
    progress_sec: Mapped[int] = mapped_column(Integer, default=0)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)
    last_watched: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    title: Mapped[Title] = relationship()
    episode: Mapped[Episode | None] = relationship()
