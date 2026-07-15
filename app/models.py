from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.community.classifications import POST_DISTRICTS, POST_PREFIXES

LOCATION_CATEGORIES = (
    "관광지",
    "레포츠",
    "문화시설",
    "쇼핑",
    "숙박",
    "여행코스",
    "축제공연행사",
)


def sql_string_values(values: tuple[str, ...]) -> str:
    return ",".join(f"'{value}'" for value in values)


def utc_now() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator[datetime]):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        del dialect
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("UTCDateTime requires a timezone-aware datetime")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        del dialect
        if value is None:
            return None
        return value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    pass


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        CheckConstraint(
            "category IN ('관광지','레포츠','문화시설','쇼핑','숙박','여행코스','축제공연행사')",
            name="ck_locations_category",
        ),
        CheckConstraint("source_order >= 1", name="ck_locations_source_order"),
        Index(
            "ix_locations_category_district_order",
            "category",
            "district",
            "source_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    address1: Mapped[str | None] = mapped_column(String(500))
    address2: Mapped[str | None] = mapped_column(String(500))
    district: Mapped[str] = mapped_column(String(20), nullable=False)
    longitude: Mapped[float | None]
    latitude: Mapped[float | None]
    image_url: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(100))
    source_order: Mapped[int] = mapped_column(nullable=False)


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        CheckConstraint(
            f"district IN ({sql_string_values(POST_DISTRICTS)})",
            name="ck_posts_district",
        ),
        CheckConstraint(
            f"prefix IN ({sql_string_values(POST_PREFIXES)})",
            name="ck_posts_prefix",
        ),
        CheckConstraint("length(title) BETWEEN 1 AND 100", name="ck_posts_title_length"),
        CheckConstraint("length(content) BETWEEN 1 AND 5000", name="ck_posts_content_length"),
        CheckConstraint("length(password) BETWEEN 4 AND 20", name="ck_posts_password_length"),
        Index("ix_posts_created_at", "created_at"),
        Index("ix_posts_district", "district"),
        Index("ix_posts_prefix", "prefix"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    district: Mapped[str] = mapped_column(String(10), nullable=False)
    prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint("length(content) BETWEEN 1 AND 1000", name="ck_comments_content_length"),
        CheckConstraint("length(password) BETWEEN 4 AND 20", name="ck_comments_password_length"),
        Index("ix_comments_post_created_at", "post_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    post: Mapped[Post] = relationship(back_populates="comments")


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("length(title) BETWEEN 1 AND 100", name="ck_courses_title_length"),
        CheckConstraint("length(password) BETWEEN 4 AND 20", name="ck_courses_password_length"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
    stops: Mapped[list["CourseStop"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CourseStop.position",
    )


class CourseStop(Base):
    __tablename__ = "course_stops"
    __table_args__ = (
        CheckConstraint("position BETWEEN 1 AND 5", name="ck_course_stops_position"),
        UniqueConstraint("course_id", "position", name="uq_course_stops_course_position"),
        UniqueConstraint("course_id", "location_id", name="uq_course_stops_course_location"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    course: Mapped[Course] = relationship(back_populates="stops")
    location: Mapped[Location] = relationship()
