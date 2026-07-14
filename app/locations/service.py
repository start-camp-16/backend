import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.locations.recommendations import get_default_recommendations
from app.locations.schemas import LocationCategory, RankingItem, RankingResponse
from app.models import Location

logger = logging.getLogger(__name__)


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
) -> RankingResponse:
    content_ids = get_default_recommendations().get((district, category.value), ())
    rows = list(
        session.scalars(select(Location).where(Location.content_id.in_(content_ids)))
    ) if content_ids else []
    rows_by_content_id = {row.content_id: row for row in rows}
    items = [
        RankingItem(
            rank=rank,
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
