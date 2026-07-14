from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Location


def add_location(db_session: Session, content_id: str, district: str) -> None:
    db_session.add(
        Location(
            content_id=content_id,
            category="관광지",
            title=f"장소 {content_id}",
            district=district,
            source_order=int(content_id),
        )
    )


def test_categories_follow_contract_order(client: TestClient):
    response = client.get("/api/meta/categories")

    assert response.status_code == 200
    assert response.json() == {
        "items": ["관광지", "레포츠", "문화시설", "쇼핑", "숙박", "여행코스", "축제공연행사"]
    }


def test_districts_are_sorted_with_other_last(client: TestClient, db_session: Session):
    add_location(db_session, "3", "기타")
    add_location(db_session, "1", "마포구")
    add_location(db_session, "2", "강남구")
    add_location(db_session, "4", "강남구")
    db_session.commit()

    response = client.get("/api/meta/districts")

    assert response.status_code == 200
    assert response.json() == {"items": ["강남구", "마포구", "기타"]}


def test_districts_are_empty_without_location_data(client: TestClient):
    response = client.get("/api/meta/districts")

    assert response.status_code == 200
    assert response.json() == {"items": []}
