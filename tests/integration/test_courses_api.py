import json

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Course, Location


def seed_locations(db_session: Session) -> None:
    locations = [
        ("tour-1", "관광지", 127.0, 37.5, 1),
        ("tour-2", "관광지", 127.002, 37.5, 2),
        ("tour-3", "관광지", 127.004, 37.5, 3),
        ("culture-1", "문화시설", 127.001, 37.5, 1),
        ("culture-2", "문화시설", 127.003, 37.5, 2),
        ("culture-no-coordinates", "문화시설", None, None, 3),
    ]
    for content_id, category, longitude, latitude, source_order in locations:
        db_session.add(
            Location(
                content_id=content_id,
                category=category,
                title=content_id,
                address1="서울특별시 강남구 테헤란로",
                address2=None,
                district="강남구",
                longitude=longitude,
                latitude=latitude,
                image_url="https://example.com/image.jpg",
                thumbnail_url=None,
                phone=None,
                source_order=source_order,
            )
        )
    db_session.commit()


def test_course_suggestion_balances_categories_and_returns_distances(
    client: TestClient,
    db_session: Session,
    monkeypatch,
):
    seed_locations(db_session)
    monkeypatch.setattr(
        "app.courses.service.get_default_recommendations",
        lambda: {("강남구", "관광지"): ("tour-1",)},
    )

    response = client.post(
        "/api/course-suggestions",
        json={
            "district": "강남구",
            "categories": ["관광지", "문화시설"],
            "stop_count": 4,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [stop["location"]["content_id"] for stop in payload["stops"]] == [
        "tour-1",
        "culture-1",
        "tour-2",
        "culture-2",
    ]
    assert [stop["position"] for stop in payload["stops"]] == [1, 2, 3, 4]
    assert payload["stops"][0]["distance_from_previous_meters"] is None
    assert all(stop["distance_from_previous_meters"] > 0 for stop in payload["stops"][1:])
    assert payload["total_straight_line_distance_meters"] == sum(
        stop["distance_from_previous_meters"] for stop in payload["stops"][1:]
    )


def test_course_suggestion_rejects_insufficient_locations(
    client: TestClient,
    db_session: Session,
):
    seed_locations(db_session)

    response = client.post(
        "/api/course-suggestions",
        json={
            "district": "강남구",
            "categories": ["문화시설"],
            "stop_count": 3,
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "COURSE_NOT_ENOUGH_LOCATIONS"


def test_course_crud_uses_public_id_and_never_exposes_password(
    client: TestClient,
    db_session: Session,
):
    seed_locations(db_session)

    created = client.post(
        "/api/courses",
        json={
            "title": " 강남 산책 ",
            "password": "1234",
            "location_content_ids": ["tour-1", "culture-1", "tour-2"],
        },
    )

    assert created.status_code == 201
    created_payload = created.json()
    assert created_payload["title"] == "강남 산책"
    assert len(created_payload["public_id"]) == 32
    assert "password" not in json.dumps(created_payload)
    assert [stop["location"]["content_id"] for stop in created_payload["stops"]] == [
        "tour-1",
        "culture-1",
        "tour-2",
    ]

    fetched = client.get(f"/api/courses/{created_payload['public_id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created_payload

    rejected = client.put(
        f"/api/courses/{created_payload['public_id']}",
        json={
            "password": "9999",
            "title": "수정 코스",
            "location_content_ids": ["culture-2", "tour-2", "tour-3"],
        },
    )
    assert rejected.status_code == 403
    assert rejected.json()["code"] == "PASSWORD_MISMATCH"

    updated = client.put(
        f"/api/courses/{created_payload['public_id']}",
        json={
            "password": "1234",
            "title": "수정 코스",
            "location_content_ids": ["culture-2", "tour-2", "tour-3"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "수정 코스"
    assert [stop["location"]["content_id"] for stop in updated.json()["stops"]] == [
        "culture-2",
        "tour-2",
        "tour-3",
    ]

    deleted = client.request(
        "DELETE",
        f"/api/courses/{created_payload['public_id']}",
        json={"password": "1234"},
    )
    assert deleted.status_code == 204
    deleted_course = db_session.scalar(
        select(Course).where(Course.public_id == created_payload["public_id"])
    )
    assert deleted_course is None


def test_course_create_validates_stop_count_duplicates_and_missing_locations(
    client: TestClient,
    db_session: Session,
):
    seed_locations(db_session)
    base = {"title": "코스", "password": "1234"}

    too_short = client.post(
        "/api/courses",
        json={**base, "location_content_ids": ["tour-1", "tour-2"]},
    )
    duplicate = client.post(
        "/api/courses",
        json={**base, "location_content_ids": ["tour-1", "tour-1", "tour-2"]},
    )
    missing = client.post(
        "/api/courses",
        json={**base, "location_content_ids": ["tour-1", "tour-2", "missing"]},
    )

    assert too_short.status_code == 400
    assert duplicate.status_code == 400
    assert too_short.json()["code"] == "VALIDATION_ERROR"
    assert duplicate.json()["code"] == "VALIDATION_ERROR"
    assert missing.status_code == 404
    assert missing.json()["code"] == "LOCATION_NOT_FOUND"


def test_course_with_missing_coordinates_returns_null_total_distance(
    client: TestClient,
    db_session: Session,
):
    seed_locations(db_session)

    response = client.post(
        "/api/courses",
        json={
            "title": "좌표 없는 코스",
            "password": "1234",
            "location_content_ids": ["tour-1", "culture-no-coordinates", "tour-2"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["stops"][1]["distance_from_previous_meters"] is None
    assert payload["stops"][2]["distance_from_previous_meters"] is None
    assert payload["total_straight_line_distance_meters"] is None


def test_reordering_course_updates_timestamp_when_title_is_unchanged(
    client: TestClient,
    db_session: Session,
):
    seed_locations(db_session)
    created = client.post(
        "/api/courses",
        json={
            "title": "순서 변경 코스",
            "password": "1234",
            "location_content_ids": ["tour-1", "culture-1", "tour-2"],
        },
    ).json()

    updated = client.put(
        f"/api/courses/{created['public_id']}",
        json={
            "title": "순서 변경 코스",
            "password": "1234",
            "location_content_ids": ["tour-2", "culture-1", "tour-1"],
        },
    )

    assert updated.status_code == 200
    assert updated.json()["updated_at"] > created["updated_at"]
