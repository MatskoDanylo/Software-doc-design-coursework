from enum import StrEnum

from sqlalchemy import Column, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class TitleKind(StrEnum):
    MOVIE = "movie"
    SERIES = "series"


title_genres = Table(
    "title_genres",
    Base.metadata,
    Column("title_id", ForeignKey("titles.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)


class Title(Base):
    __tablename__ = "titles"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    year: Mapped[int] = mapped_column(Integer, index=True)
    country: Mapped[str] = mapped_column(String(100), index=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    poster_url: Mapped[str | None] = mapped_column(String(500))

    genres: Mapped[list[Genre]] = relationship(secondary=title_genres, lazy="selectin", order_by=Genre.name)
    seasons: Mapped[list["Season"]] = relationship(
        back_populates="title", cascade="all, delete-orphan", passive_deletes=True, order_by="Season.number"
    )
    video: Mapped["VideoAsset | None"] = relationship(
        back_populates="title", uselist=False, foreign_keys="VideoAsset.title_id"
    )


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(Integer)

    title: Mapped[Title] = relationship(back_populates="seasons")
    episodes: Mapped[list["Episode"]] = relationship(
        back_populates="season", cascade="all, delete-orphan", passive_deletes=True, order_by="Episode.number"
    )


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"))
    number: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))

    season: Mapped[Season] = relationship(back_populates="episodes")
    video: Mapped["VideoAsset | None"] = relationship(
        back_populates="episode", uselist=False, foreign_keys="VideoAsset.episode_id"
    )


class VideoAsset(Base):
    __tablename__ = "video_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    title_id: Mapped[int | None] = mapped_column(ForeignKey("titles.id", ondelete="CASCADE"))
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"))
    hls_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | processing | ready | failed

    title: Mapped[Title | None] = relationship(back_populates="video", foreign_keys=[title_id])
    episode: Mapped[Episode | None] = relationship(back_populates="video", foreign_keys=[episode_id])
