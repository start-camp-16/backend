from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas import Pagination


class LocationCategory(StrEnum):
    TOURIST_ATTRACTION = "관광지"
    LEISURE_SPORTS = "레포츠"
    CULTURAL_FACILITY = "문화시설"
    SHOPPING = "쇼핑"
    ACCOMMODATION = "숙박"
    TRAVEL_COURSE = "여행코스"
    FESTIVAL_EVENT = "축제공연행사"


class CategoriesResponse(BaseModel):
    items: list[LocationCategory]


class DistrictsResponse(BaseModel):
    items: list[str]


class RankingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int = Field(ge=1)
    content_id: str
    category: LocationCategory
    title: str
    address: str | None
    district: str
    longitude: float | None
    latitude: float | None
    image_url: str | None
    thumbnail_url: str | None
    phone: str | None
    source_order: int = Field(ge=1)


class RankingListResponse(BaseModel):
    items: list[RankingItem]
    pagination: Pagination
