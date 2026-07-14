import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.locations.recommendations import get_default_recommendations
from app.locations.schemas import (
    LocationCategory,
    LocationItem,
    LocationListResponse,
    RankingItem,
    RankingResponse,
)
from app.models import Location
from app.schemas import Pagination

logger = logging.getLogger(__name__)


def list_categories() -> list[LocationCategory]:
    return list(LocationCategory)


def list_districts(session: Session) -> list[str]:
    districts = set(session.scalars(select(Location.district).distinct()))
    return sorted(districts, key=lambda district: (district == "기타", district))


def _location_values(row: Location) -> dict[str, object]:
    return {
        "content_id": row.content_id,
        "category": LocationCategory(row.category),
        "title": row.title,
        "address": " ".join(filter(None, (row.address1, row.address2))) or None,
        "district": row.district,
        "longitude": row.longitude,
        "latitude": row.latitude,
        "image_url": row.image_url,
        "thumbnail_url": row.thumbnail_url,
        "phone": row.phone,
    }


def get_rankings(
    session: Session,
    *,
    district: str,
    category: LocationCategory,
) -> RankingResponse:
    content_ids = get_default_recommendations().get((district, category.value), ())
    rows = list(
        session.scalars(select(Location).where(Location.content_id.in_(content_ids)))
    ) if content_ids else []
    rows_by_content_id = {row.content_id: row for row in rows}
    items = [
        RankingItem(
            rank=rank,
            **_location_values(row),
        )
        for rank, content_id in enumerate(content_ids, start=1)
        if (row := rows_by_content_id.get(content_id)) is not None
    ]
    if len(items) != len(content_ids):
        logger.warning(
            "Some recommended locations were not found",
            extra={"district": district, "category": category.value},
        )
    return RankingResponse(
        district=district,
        category=category,
        items=items,
    )


def get_locations(
    session: Session,
    *,
    district: str | None,
    category: LocationCategory | None,
    page: int,
    size: int,
) -> LocationListResponse:
    filters = []
    if district is not None:
        filters.append(Location.district == district)
    if category is not None:
        filters.append(Location.category == category.value)

    total_items = session.scalar(select(func.count()).select_from(Location).where(*filters)) or 0
    order_by = (
        (Location.source_order.asc(), Location.id.asc())
        if category is not None
        else (Location.category.asc(), Location.source_order.asc(), Location.id.asc())
    )
    offset = (page - 1) * size
    rows = list(
        session.scalars(
            select(Location)
            .where(*filters)
            .order_by(*order_by)
            .offset(offset)
            .limit(size)
        )
    )
    total_pages = (total_items + size - 1) // size if total_items else 0
    return LocationListResponse(
        items=[LocationItem(**_location_values(row)) for row in rows],
        pagination=Pagination(
            page=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )
