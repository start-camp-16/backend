from dataclasses import dataclass
from functools import partial
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_METERS = 6_371_000


@dataclass(frozen=True)
class CourseCandidate:
    content_id: str
    category: str
    longitude: float | None
    latitude: float | None
    curated_rank: int | None
    has_image: bool
    has_address: bool
    source_order: int


def haversine_meters(
    longitude1: float,
    latitude1: float,
    longitude2: float,
    latitude2: float,
) -> int:
    longitude_delta = radians(longitude2 - longitude1)
    latitude_delta = radians(latitude2 - latitude1)
    latitude1_radians = radians(latitude1)
    latitude2_radians = radians(latitude2)
    value = (
        sin(latitude_delta / 2) ** 2
        + cos(latitude1_radians) * cos(latitude2_radians) * sin(longitude_delta / 2) ** 2
    )
    return round(2 * EARTH_RADIUS_METERS * asin(sqrt(value)))


def has_valid_coordinates(candidate: CourseCandidate) -> bool:
    if candidate.longitude is None or candidate.latitude is None:
        return False
    return not (candidate.longitude == 0 and candidate.latitude == 0)


def _quality_rank(candidate: CourseCandidate) -> int:
    if candidate.has_image and candidate.has_address:
        return 0
    if candidate.has_image or candidate.has_address:
        return 1
    return 2


def _priority(
    candidate: CourseCandidate,
    category_order: dict[str, int],
) -> tuple[int, int, int, int, int, str]:
    curated_group = 0 if candidate.curated_rank is not None else 1
    curated_rank = candidate.curated_rank or 0
    return (
        curated_group,
        curated_rank,
        category_order[candidate.category],
        _quality_rank(candidate),
        candidate.source_order,
        candidate.content_id,
    )


def _next_priority(
    item: CourseCandidate,
    *,
    current: CourseCandidate,
    category_order: dict[str, int],
) -> tuple[object, ...]:
    assert current.longitude is not None and current.latitude is not None
    assert item.longitude is not None and item.latitude is not None
    return (
        haversine_meters(
            current.longitude,
            current.latitude,
            item.longitude,
            item.latitude,
        ),
        *_priority(item, category_order),
    )


def select_course_candidates(
    candidates: list[CourseCandidate],
    *,
    categories: list[str],
    stop_count: int,
) -> list[CourseCandidate]:
    category_order = {category: index for index, category in enumerate(categories)}
    remaining = [
        candidate
        for candidate in candidates
        if candidate.category in category_order and has_valid_coordinates(candidate)
    ]
    available_categories = {candidate.category for candidate in remaining}
    if len(remaining) < stop_count or available_categories != set(categories):
        raise ValueError("insufficient candidates")

    first = min(remaining, key=lambda item: _priority(item, category_order))
    selected = [first]
    remaining.remove(first)
    category_counts = {category: 0 for category in categories}
    category_counts[first.category] += 1

    while len(selected) < stop_count:
        available_categories = {candidate.category for candidate in remaining}
        minimum_count = min(category_counts[category] for category in available_categories)
        target_categories = {
            category
            for category in available_categories
            if category_counts[category] == minimum_count
        }
        current = selected[-1]
        next_key = partial(
            _next_priority,
            current=current,
            category_order=category_order,
        )

        next_candidate = min(
            (candidate for candidate in remaining if candidate.category in target_categories),
            key=next_key,
        )
        selected.append(next_candidate)
        remaining.remove(next_candidate)
        category_counts[next_candidate.category] += 1

    return selected
