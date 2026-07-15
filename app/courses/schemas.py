from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.community.schemas import Password, StrictRequest, TrimmedTitle
from app.locations.schemas import LocationCategory, LocationItem

PublicId = Annotated[
    str,
    StringConstraints(min_length=32, max_length=32, pattern=r"^[0-9a-f]{32}$"),
]


class CourseSuggestionRequest(StrictRequest):
    district: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    categories: list[LocationCategory] = Field(min_length=1, max_length=3)
    stop_count: int = Field(ge=3, le=5)

    @field_validator("categories")
    @classmethod
    def categories_must_be_unique(
        cls,
        categories: list[LocationCategory],
    ) -> list[LocationCategory]:
        if len(set(categories)) != len(categories):
            raise ValueError("categories must be unique")
        return categories

    @model_validator(mode="after")
    def category_count_must_not_exceed_stop_count(self) -> "CourseSuggestionRequest":
        if len(self.categories) > self.stop_count:
            raise ValueError("category count must not exceed stop count")
        return self


class CourseStopItem(BaseModel):
    position: int = Field(ge=1, le=5)
    distance_from_previous_meters: int | None = Field(default=None, ge=0)
    location: LocationItem


class CourseSuggestionResponse(BaseModel):
    district: str
    categories: list[LocationCategory]
    stops: list[CourseStopItem]
    total_straight_line_distance_meters: int


class CourseCreate(StrictRequest):
    title: TrimmedTitle
    password: Password
    location_content_ids: list[str] = Field(min_length=3, max_length=5)

    @field_validator("location_content_ids")
    @classmethod
    def locations_must_be_unique(cls, content_ids: list[str]) -> list[str]:
        if len(set(content_ids)) != len(content_ids):
            raise ValueError("location content IDs must be unique")
        return content_ids


class CourseUpdate(CourseCreate):
    pass


class CoursePasswordRequest(StrictRequest):
    password: Password


class CourseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: PublicId
    title: str
    created_at: datetime
    updated_at: datetime
    stops: list[CourseStopItem]
    total_straight_line_distance_meters: int | None
