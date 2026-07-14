from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Location


def seed_locations(db_session: Session) -> None:
    rows = [
        ("a", "관광지", "강남구", 3),
        ("b", "관광지", "강남구", 1),
        ("c", "관광지", "강남구", 2),
        ("d", "문화시설", "강남구", 2),
        ("e", "문화시설", "강남구", 1),
        ("f", "관광지", "종로구", 1),
    ]
    for content_id, category, district, source_order in rows:
        db_session.add(
            Location(
                content_id=content_id,
                category=category,
                title=f"장소 {content_id}",
                address1=f"서울특별시 {district}",
                district=district,
                source_order=source_order,
            )
        )
    db_session.commit()


def test_locations_support_optional_district_filter_and_pagination(
    client: TestClient,
    db_session: Session,
):
    seed_locations(db_session)

    response = client.get(
        "/api/locations",
        params={"district": "강남구", "page": 1, "size": 2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["content_id"] for item in payload["items"]] == ["b", "c"]
    assert payload["pagination"] == {
        "page": 1,
        "size": 2,
        "total_items": 5,
        "total_pages": 3,
    }
    assert "rank" not in payload["items"][0]
    assert "source_order" not in payload["items"][0]


def test_locations_support_category_and_combined_filters(
    client: TestClient,
    db_session: Session,
):
    seed_locations(db_session)

    category_response = client.get("/api/locations", params={"category": "관광지"})
    combined_response = client.get(
        "/api/locations",
        params={"district": "강남구", "category": "관광지"},
    )

    assert [item["content_id"] for item in category_response.json()["items"]] == [
        "b",
        "f",
        "c",
        "a",
    ]
    assert [item["content_id"] for item in combined_response.json()["items"]] == [
        "b",
        "c",
        "a",
    ]


def test_locations_without_filters_returns_all_categories_in_stable_order(
    client: TestClient,
    db_session: Session,
):
    seed_locations(db_session)

    response = client.get("/api/locations")

    assert [item["content_id"] for item in response.json()["items"]] == [
        "b",
        "f",
        "c",
        "a",
        "e",
        "d",
    ]


def test_locations_empty_and_invalid_requests(client: TestClient):
    empty = client.get("/api/locations", params={"district": "없는구"})
    invalid_page = client.get("/api/locations", params={"page": 0})
    invalid_category = client.get("/api/locations", params={"category": "음식점"})

    assert empty.status_code == 200
    assert empty.json()["items"] == []
    assert empty.json()["pagination"]["total_pages"] == 0
    assert invalid_page.status_code == 400
    assert invalid_category.status_code == 400
