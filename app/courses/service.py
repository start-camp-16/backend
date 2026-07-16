from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.courses.demo_presets import match_demo_course
from app.courses.ranking_presets import COURSE_RANKING_PRESETS
from app.courses.recommender import (
    CourseCandidate,
    has_valid_coordinates,
    haversine_meters,
    select_course_candidates,
)
from app.courses.schemas import (
    CourseCreate,
    CourseDetail,
    CourseRankingItem,
    CourseRankingResponse,
    CourseStopItem,
    CourseSuggestionRequest,
    CourseSuggestionResponse,
    CourseUpdate,
)
from app.errors import AppError
from app.locations.recommendations import get_default_recommendations
from app.locations.schemas import LocationCategory, LocationItem
from app.models import Course, CourseStop, Location, utc_now


def _location_item(location: Location) -> LocationItem:
    return LocationItem(
        content_id=location.content_id,
        category=LocationCategory(location.category),
        title=location.title,
        address=" ".join(filter(None, (location.address1, location.address2))) or None,
        district=location.district,
        longitude=location.longitude,
        latitude=location.latitude,
        image_url=location.image_url,
        thumbnail_url=location.thumbnail_url,
        phone=location.phone,
    )


def _candidate(location: Location, curated_rank: int | None) -> CourseCandidate:
    return CourseCandidate(
        content_id=location.content_id,
        category=location.category,
        longitude=location.longitude,
        latitude=location.latitude,
        curated_rank=curated_rank,
        has_image=bool(location.image_url),
        has_address=bool(location.address1 or location.address2),
        source_order=location.source_order,
    )


def _course_not_enough_locations() -> AppError:
    return AppError(
        status_code=400,
        code="COURSE_NOT_ENOUGH_LOCATIONS",
        message="조건에 맞는 장소가 부족합니다.",
    )


def _demo_course_locations(
    session: Session,
    content_ids: tuple[str, ...],
) -> list[Location]:
    rows = list(session.scalars(select(Location).where(Location.content_id.in_(content_ids))))
    rows_by_content_id = {row.content_id: row for row in rows}
    if len(rows_by_content_id) != len(content_ids):
        raise _course_not_enough_locations()
    return [rows_by_content_id[content_id] for content_id in content_ids]


def _stops_and_total(locations: list[Location]) -> tuple[list[CourseStopItem], int | None]:
    stops: list[CourseStopItem] = []
    total = 0
    complete_distance = True
    previous: Location | None = None
    for position, location in enumerate(locations, start=1):
        distance: int | None = None
        if previous is not None:
            previous_candidate = _candidate(previous, None)
            current_candidate = _candidate(location, None)
            if has_valid_coordinates(previous_candidate) and has_valid_coordinates(
                current_candidate
            ):
                assert previous.longitude is not None and previous.latitude is not None
                assert location.longitude is not None and location.latitude is not None
                distance = haversine_meters(
                    previous.longitude,
                    previous.latitude,
                    location.longitude,
                    location.latitude,
                )
                total += distance
            else:
                complete_distance = False
        stops.append(
            CourseStopItem(
                position=position,
                distance_from_previous_meters=distance,
                location=_location_item(location),
            )
        )
        previous = location
    return stops, total if complete_distance else None


def suggest_course(
    session: Session,
    payload: CourseSuggestionRequest,
) -> CourseSuggestionResponse:
    category_values = [category.value for category in payload.categories]
    demo_content_ids = match_demo_course(
        payload.district,
        category_values,
        payload.stop_count,
    )
    if demo_content_ids is not None:
        selected_rows = _demo_course_locations(session, demo_content_ids)
        stops, total = _stops_and_total(selected_rows)
        assert total is not None
        return CourseSuggestionResponse(
            district=payload.district,
            categories=payload.categories,
            stops=stops,
            total_straight_line_distance_meters=total,
        )

    rows = list(
        session.scalars(
            select(Location).where(
                Location.district == payload.district,
                Location.category.in_(category_values),
            )
        )
    )
    recommendation_index = get_default_recommendations()
    curated_ranks = {
        content_id: rank
        for category in category_values
        for rank, content_id in enumerate(
            recommendation_index.get((payload.district, category), ()),
            start=1,
        )
    }
    candidates = [_candidate(row, curated_ranks.get(row.content_id)) for row in rows]
    try:
        selected = select_course_candidates(
            candidates,
            categories=category_values,
            stop_count=payload.stop_count,
        )
    except ValueError as exc:
        raise _course_not_enough_locations() from exc

    rows_by_content_id = {row.content_id: row for row in rows}
    selected_rows = [rows_by_content_id[item.content_id] for item in selected]
    stops, total = _stops_and_total(selected_rows)
    assert total is not None
    return CourseSuggestionResponse(
        district=payload.district,
        categories=payload.categories,
        stops=stops,
        total_straight_line_distance_meters=total,
    )


def get_course_rankings(session: Session) -> CourseRankingResponse:
    content_ids = tuple(
        content_id
        for preset in COURSE_RANKING_PRESETS
        for content_id in preset.content_ids
    )
    rows = list(session.scalars(select(Location).where(Location.content_id.in_(content_ids))))
    rows_by_content_id = {row.content_id: row for row in rows}
    if len(rows_by_content_id) != len(set(content_ids)):
        raise AppError(
            status_code=500,
            code="COURSE_RANKING_DATA_INCOMPLETE",
            message="코스 랭킹 데이터를 불러올 수 없습니다.",
        )

    items: list[CourseRankingItem] = []
    for preset in COURSE_RANKING_PRESETS:
        locations = [rows_by_content_id[content_id] for content_id in preset.content_ids]
        stops, total = _stops_and_total(locations)
        thumbnail_url = next((row.image_url for row in locations if row.image_url), None)
        items.append(
            CourseRankingItem(
                rank=preset.rank,
                district=preset.district,
                title=preset.title,
                description=preset.description,
                thumbnail_url=thumbnail_url,
                stops=stops,
                total_straight_line_distance_meters=total,
            )
        )
    return CourseRankingResponse(items=items)


def _course_query(public_id: str) -> Select[tuple[Course]]:
    return (
        select(Course)
        .where(Course.public_id == public_id)
        .options(selectinload(Course.stops).selectinload(CourseStop.location))
    )


def _require_course(session: Session, public_id: str) -> Course:
    course = session.scalar(_course_query(public_id))
    if course is None:
        raise AppError(
            status_code=404,
            code="COURSE_NOT_FOUND",
            message="코스를 찾을 수 없습니다.",
        )
    return course


def _require_locations(session: Session, content_ids: list[str]) -> list[Location]:
    rows = list(session.scalars(select(Location).where(Location.content_id.in_(content_ids))))
    rows_by_content_id = {row.content_id: row for row in rows}
    if len(rows_by_content_id) != len(content_ids):
        raise AppError(
            status_code=404,
            code="LOCATION_NOT_FOUND",
            message="장소를 찾을 수 없습니다.",
        )
    return [rows_by_content_id[content_id] for content_id in content_ids]


def _course_detail(course: Course) -> CourseDetail:
    ordered_stops = sorted(course.stops, key=lambda stop: stop.position)
    locations = [stop.location for stop in ordered_stops]
    stops, total = _stops_and_total(locations)
    return CourseDetail(
        public_id=course.public_id,
        title=course.title,
        created_at=course.created_at,
        updated_at=course.updated_at,
        stops=stops,
        total_straight_line_distance_meters=total,
    )


def _new_public_id(session: Session) -> str:
    while True:
        public_id = uuid4().hex
        if session.scalar(select(Course.id).where(Course.public_id == public_id)) is None:
            return public_id


def create_course(session: Session, payload: CourseCreate) -> CourseDetail:
    locations = _require_locations(session, payload.location_content_ids)
    course = Course(
        public_id=_new_public_id(session),
        title=payload.title,
        password=payload.password,
    )
    course.stops = [
        CourseStop(position=position, location=location)
        for position, location in enumerate(locations, start=1)
    ]
    session.add(course)
    session.commit()
    session.refresh(course)
    return _course_detail(course)


def get_course(session: Session, public_id: str) -> CourseDetail:
    return _course_detail(_require_course(session, public_id))


def update_course(
    session: Session,
    public_id: str,
    payload: CourseUpdate,
) -> CourseDetail:
    course = _require_course(session, public_id)
    if course.password != payload.password:
        raise AppError(
            status_code=403,
            code="PASSWORD_MISMATCH",
            message="비밀번호가 일치하지 않습니다.",
        )
    locations = _require_locations(session, payload.location_content_ids)
    course.title = payload.title
    course.updated_at = utc_now()
    course.stops.clear()
    session.flush()
    course.stops.extend(
        CourseStop(position=position, location=location)
        for position, location in enumerate(locations, start=1)
    )
    session.commit()
    session.refresh(course)
    return _course_detail(course)


def delete_course(session: Session, public_id: str, password: str) -> None:
    course = _require_course(session, public_id)
    if course.password != password:
        raise AppError(
            status_code=403,
            code="PASSWORD_MISMATCH",
            message="비밀번호가 일치하지 않습니다.",
        )
    session.delete(course)
    session.commit()
