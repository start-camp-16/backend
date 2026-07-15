import pytest

from app.courses.recommender import (
    CourseCandidate,
    haversine_meters,
    select_course_candidates,
)


def candidate(
    content_id: str,
    category: str,
    longitude: float,
    latitude: float,
    *,
    curated_rank: int | None = None,
    source_order: int = 1,
) -> CourseCandidate:
    return CourseCandidate(
        content_id=content_id,
        category=category,
        longitude=longitude,
        latitude=latitude,
        curated_rank=curated_rank,
        has_image=True,
        has_address=True,
        source_order=source_order,
    )


def test_haversine_returns_zero_for_same_coordinates():
    assert haversine_meters(127.0, 37.5, 127.0, 37.5) == 0


def test_haversine_rounds_distance_to_meters():
    assert haversine_meters(126.978, 37.5665, 126.9781, 37.5665) == 9


def test_selection_includes_categories_evenly_and_uses_nearest_candidate():
    candidates = [
        candidate("tour-start", "관광지", 127.0, 37.5, curated_rank=1),
        candidate("culture-near", "문화시설", 127.001, 37.5),
        candidate("culture-far", "문화시설", 127.1, 37.5),
        candidate("tour-next", "관광지", 127.002, 37.5),
    ]

    selected = select_course_candidates(
        candidates,
        categories=["관광지", "문화시설"],
        stop_count=4,
    )

    assert [item.content_id for item in selected] == [
        "tour-start",
        "culture-near",
        "tour-next",
        "culture-far",
    ]
    assert [item.category for item in selected] == ["관광지", "문화시설"] * 2


def test_selection_is_deterministic_for_equal_distances():
    candidates = [
        candidate("start", "관광지", 127.0, 37.5, curated_rank=1),
        candidate("later", "문화시설", 127.001, 37.5, source_order=2),
        candidate("earlier", "문화시설", 126.999, 37.5, source_order=1),
    ]

    selected = select_course_candidates(
        candidates,
        categories=["관광지", "문화시설"],
        stop_count=3,
    )

    assert [item.content_id for item in selected] == ["start", "earlier", "later"]


def test_selection_rejects_insufficient_valid_candidates():
    candidates = [
        candidate("valid", "관광지", 127.0, 37.5),
        candidate("zero", "관광지", 0.0, 0.0),
        candidate("missing", "관광지", 127.0, 37.5),
    ]
    candidates[-1] = CourseCandidate(
        content_id="missing",
        category="관광지",
        longitude=None,
        latitude=37.5,
        curated_rank=None,
        has_image=False,
        has_address=False,
        source_order=3,
    )

    with pytest.raises(ValueError, match="insufficient candidates"):
        select_course_candidates(candidates, categories=["관광지"], stop_count=3)


def test_selection_rejects_category_without_valid_candidate():
    candidates = [
        candidate("tour-1", "관광지", 127.0, 37.5),
        candidate("tour-2", "관광지", 127.1, 37.5),
        candidate("tour-3", "관광지", 127.2, 37.5),
    ]

    with pytest.raises(ValueError, match="insufficient candidates"):
        select_course_candidates(
            candidates,
            categories=["관광지", "문화시설"],
            stop_count=3,
        )
