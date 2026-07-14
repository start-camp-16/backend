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
    db_session.commit()


def test_rankings_return_configured_top_five_in_order(
    client: TestClient,
    db_session: Session,
    monkeypatch,
):
    seed_rankings(db_session)
    monkeypatch.setattr(
        "app.locations.service.get_default_recommendations",
        lambda: {("강남구", "관광지"): ("3", "1", "5", "2", "4")},
    )

    response = client.get(
        "/api/rankings",
        params={"district": "강남구", "category": "관광지"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["district"] == "강남구"
    assert payload["category"] == "관광지"
    assert [item["content_id"] for item in payload["items"]] == ["3", "1", "5", "2", "4"]
    assert [item["rank"] for item in payload["items"]] == [1, 2, 3, 4, 5]
    assert payload["items"][0]["address"] == "서울특별시 강남구 테헤란로 3층"
    assert "pagination" not in payload
    assert "source_order" not in payload["items"][0]


def test_empty_ranking_returns_selected_combination(
    client: TestClient,
    monkeypatch,
):
    monkeypatch.setattr("app.locations.service.get_default_recommendations", lambda: {})

    response = client.get(
        "/api/rankings",
        params={"district": "강남구", "category": "관광지"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "district": "강남구",
        "category": "관광지",
        "items": [],
    }


def test_invalid_ranking_filters_use_validation_error(client: TestClient):
    invalid_category = client.get(
        "/api/rankings",
        params={"district": "강남구", "category": "음식점"},
    )
    missing_district = client.get("/api/rankings", params={"category": "관광지"})

    assert invalid_category.status_code == 400
    assert missing_district.status_code == 400
    assert invalid_category.json()["code"] == "VALIDATION_ERROR"
