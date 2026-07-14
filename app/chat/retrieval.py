from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.chat.query import ParsedQuery
from app.models import Location, Post


@dataclass(frozen=True)
class LocationEvidence:
    content_id: str
    title: str
    category: str
    district: str
    address: str | None
    longitude: float | None
    latitude: float | None
    phone: str | None


@dataclass(frozen=True)
class PostEvidence:
    post_id: int
    title: str
    tag: str
    content: str


@dataclass(frozen=True)
class RetrievedContext:
    locations: list[LocationEvidence]
    posts: list[PostEvidence]


def _location_keyword_filter(keyword: str) -> ColumnElement[bool]:
    lowered = keyword.lower()
    return or_(
        func.lower(Location.title).contains(lowered, autoescape=True),
        func.lower(Location.address1).contains(lowered, autoescape=True),
        func.lower(Location.address2).contains(lowered, autoescape=True),
    )


def _post_keyword_filter(keyword: str) -> ColumnElement[bool]:
    lowered = keyword.lower()
    return or_(
        func.lower(Post.title).contains(lowered, autoescape=True),
        func.lower(Post.content).contains(lowered, autoescape=True),
        func.lower(Post.tag).contains(lowered, autoescape=True),
    )


def retrieve_sources(
    session: Session,
    parsed: ParsedQuery,
    *,
    location_limit: int,
    post_limit: int,
) -> RetrievedContext:
    if not any((parsed.district, parsed.location_category, parsed.post_tag, parsed.keywords)):
        return RetrievedContext(locations=[], posts=[])

    location_filters = []
    if parsed.district:
        location_filters.append(Location.district == parsed.district)
    if parsed.location_category:
        location_filters.append(Location.category == parsed.location_category)
    location_filters.extend(_location_keyword_filter(keyword) for keyword in parsed.keywords)

    post_filters = []
    if parsed.post_tag:
        post_filters.append(Post.tag == parsed.post_tag)
    post_filters.extend(_post_keyword_filter(keyword) for keyword in parsed.keywords)

    location_rows = (
        list(
            session.scalars(
                select(Location)
                .where(*location_filters)
                .order_by(Location.source_order.asc(), Location.id.asc())
                .limit(location_limit)
            )
        )
        if parsed.district or parsed.location_category or parsed.keywords
        else []
    )
    post_rows = (
        list(
            session.scalars(
                select(Post)
                .where(*post_filters)
                .order_by(Post.created_at.desc(), Post.id.desc())
                .limit(post_limit)
            )
        )
        if parsed.post_tag or parsed.keywords
        else []
    )

    locations = []
    for row in location_rows:
        coordinates_missing = row.longitude == 0 and row.latitude == 0
        locations.append(
            LocationEvidence(
                content_id=row.content_id,
                title=row.title,
                category=row.category,
                district=row.district,
                address=" ".join(filter(None, (row.address1, row.address2))) or None,
                longitude=None if coordinates_missing else row.longitude,
                latitude=None if coordinates_missing else row.latitude,
                phone=row.phone,
            )
        )
    posts = [
        PostEvidence(post_id=row.id, title=row.title, tag=row.tag, content=row.content)
        for row in post_rows
    ]
    return RetrievedContext(locations=locations, posts=posts)
