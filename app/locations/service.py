from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.locations.schemas import LocationCategory, RankingItem, RankingListResponse
from app.models import Location
from app.schemas import Pagination


def list_categories() -> list[LocationCategory]:
    return list(LocationCategory)


def list_districts(session: Session) -> list[str]:
    districts = set(session.scalars(select(Location.district).distinct()))
    return sorted(districts, key=lambda district: (district == "기타", district))


def get_rankings(
    session: Session,
    *,
    district: str,
    category: LocationCategory,
    page: int,
    size: int,
) -> RankingListResponse:
    filters = (Location.district == district, Location.category == category.value)
    total_items = session.scalar(select(func.count()).select_from(Location).where(*filters)) or 0
    offset = (page - 1) * size
    query = (
        select(Location)
        .where(*filters)
        .order_by(Location.source_order.asc(), Location.id.asc())
        .offset(offset)
        .limit(size)
    )
    rows = list(session.scalars(query))
    items = [
        RankingItem(
            rank=offset + index,
            content_id=row.content_id,
            category=LocationCategory(row.category),
            title=row.title,
            address=" ".join(filter(None, (row.address1, row.address2))) or None,
            district=row.district,
            longitude=row.longitude,
            latitude=row.latitude,
            image_url=row.image_url,
            thumbnail_url=row.thumbnail_url,
            phone=row.phone,
            source_order=row.source_order,
        )
        for index, row in enumerate(rows, start=1)
    ]
    total_pages = (total_items + size - 1) // size if total_items else 0
    return RankingListResponse(
        items=items,
        pagination=Pagination(
            page=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )
