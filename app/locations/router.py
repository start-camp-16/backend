from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.locations.schemas import (
    CategoriesResponse,
    DistrictsResponse,
    LocationCategory,
    LocationListResponse,
    RankingResponse,
)
from app.locations.service import get_locations, get_rankings, list_categories, list_districts

router = APIRouter(prefix="/api")


@router.get(
    "/meta/categories",
    response_model=CategoriesResponse,
    operation_id="getCategories",
)
def get_categories() -> CategoriesResponse:
    return CategoriesResponse(items=list_categories())


@router.get(
    "/meta/districts",
    response_model=DistrictsResponse,
    operation_id="getDistricts",
)
def get_districts(session: Annotated[Session, Depends(get_db)]) -> DistrictsResponse:
    return DistrictsResponse(items=list_districts(session))


@router.get(
    "/rankings",
    response_model=RankingResponse,
    operation_id="getRankings",
)
def rankings(
    session: Annotated[Session, Depends(get_db)],
    district: Annotated[str, Query(min_length=1)],
    category: LocationCategory,
) -> RankingResponse:
    return get_rankings(
        session,
        district=district,
        category=category,
    )


@router.get(
    "/locations",
    response_model=LocationListResponse,
    operation_id="getLocations",
)
def locations(
    session: Annotated[Session, Depends(get_db)],
    district: Annotated[str | None, Query(min_length=1)] = None,
    category: Annotated[LocationCategory | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> LocationListResponse:
    return get_locations(
        session,
        district=district,
        category=category,
        page=page,
        size=size,
    )
