from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Location


def seed_rankings(db_session: Session) -> None:
    for source_order in [5, 1, 4, 2, 3]:
        db_session.add(
            Location(
                content_id=str(source_order),
                category="관광지",
                title=f"장소 {source_order}",
                address1="서울특별시 강남구 테헤란로" if source_order == 3 else None,
                address2="3층" if source_order == 3 else None,
                district="강남구",
                longitude=127.0,
                latitude=37.5,
                image_url=None,
                thumbnail_url=None,
                phone=None,
                source_order=source_order,
            )
        )
    db_session.add(
        Location(
            content_id="other",
            category="문화시설",
            title="다른 카테고리",
            district="강남구",
            source_order=1,
        )
    )
    db_session.commit()


def test_rank_continues_across_pages(client: TestClient, db_session: Session):
    seed_rankings(db_session)

    response = client.get(
        "/api/rankings",
        params={"district": "강남구", "category": "관광지", "page": 2, "size": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["rank"] for item in payload["items"]] == [3, 4]
    assert [item["source_order"] for item in payload["items"]] == [3, 4]
    assert payload["items"][0]["address"] == "서울특별시 강남구 테헤란로 3층"
    assert payload["pagination"] == {
        "page": 2,
        "size": 2,
        "total_items": 5,
        "total_pages": 3,
    }


def test_empty_ranking_has_zero_total_pages(client: TestClient):
    response = client.get(
        "/api/rankings",
        params={"district": "강남구", "category": "관광지"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "pagination": {"page": 1, "size": 20, "total_items": 0, "total_pages": 0},
    }


def test_invalid_ranking_filters_use_validation_error(client: TestClient):
    invalid_category = client.get(
        "/api/rankings",
        params={"district": "강남구", "category": "음식점"},
    )
    invalid_page = client.get(
        "/api/rankings",
        params={"district": "강남구", "category": "관광지", "page": 0},
    )
    missing_district = client.get("/api/rankings", params={"category": "관광지"})

    assert invalid_category.status_code == 400
    assert invalid_page.status_code == 400
    assert missing_district.status_code == 400
    assert invalid_category.json()["code"] == "VALIDATION_ERROR"
