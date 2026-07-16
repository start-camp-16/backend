from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.courses.ranking_presets import COURSE_RANKING_PRESETS
from app.locations.importer import import_manifest
from app.locations.recommendations import get_default_recommendations
from app.locations.schemas import LocationCategory
from app.locations.service import get_locations, get_rankings
from app.models import Location


def test_course_ranking_presets_match_imported_districts(db_session: Session):
    import_manifest(db_session, Path("data/manifest.json"))

    for preset in COURSE_RANKING_PRESETS:
        rows = list(
            db_session.scalars(
                select(Location).where(Location.content_id.in_(preset.content_ids))
            )
        )

        assert len(rows) == len(preset.content_ids)
        assert all(row.district == preset.district for row in rows)


def test_recommendations_match_imported_location_combinations(db_session: Session):
    report = import_manifest(db_session, Path("data/manifest.json"))
    recommendations = get_default_recommendations()

    assert report.total == 6518
    assert len(recommendations) == 149
    assert sum(map(len, recommendations.values())) == 673

    for (district, category), content_ids in recommendations.items():
        combination_count = db_session.scalar(
            select(func.count())
            .select_from(Location)
            .where(Location.district == district, Location.category == category)
        )
        rows = list(
            db_session.scalars(
                select(Location).where(Location.content_id.in_(content_ids))
            )
        )
        assert len(content_ids) == min(5, combination_count or 0)
        assert len(rows) == len(content_ids)
        assert all(row.district == district and row.category == category for row in rows)


def test_real_data_supports_rankings_and_full_location_list(db_session: Session):
    import_manifest(db_session, Path("data/manifest.json"))
    recommendations = get_default_recommendations()
    district, category_value = next(iter(recommendations))
    expected_ids = recommendations[(district, category_value)]

    rankings = get_rankings(
        db_session,
        district=district,
        category=LocationCategory(category_value),
    )
    locations = get_locations(
        db_session,
        district=None,
        category=None,
        page=1,
        size=5,
    )

    assert [item.content_id for item in rankings.items] == list(expected_ids)
    assert [item.rank for item in rankings.items] == list(range(1, len(expected_ids) + 1))
    assert len(locations.items) == 5
    assert locations.pagination.total_items == 6518
