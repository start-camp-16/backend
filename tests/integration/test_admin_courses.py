from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker
from starlette.testclient import TestClient

from app.config import Settings
from app.db import get_db as app_get_db
from app.main import create_app
from app.models import Course, CourseStop, Location


@pytest.fixture
def admin_client_factory(
    db_session: Session,
) -> Generator[Callable[[str | None], TestClient], None, None]:
    clients: list[tuple[FastAPI, TestClient]] = []

    def factory(password: str | None) -> TestClient:
        settings = Settings(_env_file=None, admin_password=password)
        test_session_factory = sessionmaker(
            bind=db_session.get_bind(),
            expire_on_commit=False,
        )
        app = create_app(settings=settings, session_factory=test_session_factory)

        def override_get_db() -> Generator[Session, None, None]:
            yield db_session

        app.dependency_overrides[app_get_db] = override_get_db
        client = TestClient(app)
        clients.append((app, client))
        return client

    yield factory

    for app, client in clients:
        client.close()
        app.dependency_overrides.clear()


def test_admin_is_disabled_without_configured_password(
    admin_client_factory: Callable[[str | None], TestClient],
):
    client = admin_client_factory(None)

    response = client.get("/admin/courses")

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("text/html")
    assert "ADMIN_PASSWORD" in response.text


@pytest.mark.parametrize(
    "auth",
    [None, ("viewer", "operator-pass"), ("admin", "wrong-pass")],
)
def test_admin_rejects_missing_or_incorrect_credentials(
    admin_client_factory: Callable[[str | None], TestClient],
    auth: tuple[str, str] | None,
):
    client = admin_client_factory("operator-pass")

    response = client.get("/admin/courses", auth=auth)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Basic realm="course-admin"'
    assert "operator-pass" not in response.text


def test_admin_accepts_matching_credentials(
    admin_client_factory: Callable[[str | None], TestClient],
):
    client = admin_client_factory("operator-pass")

    response = client.get("/admin/courses", auth=("admin", "operator-pass"))

    assert response.status_code == 200
    assert "저장된 코스" in response.text


def seed_admin_courses(db_session: Session, count: int = 23) -> None:
    location = Location(
        content_id="admin-location",
        category="관광지",
        title="관리자 & 장소 <확인>",
        address1="서울특별시 종로구",
        address2=None,
        district="종로구",
        longitude=126.98,
        latitude=37.57,
        image_url=None,
        thumbnail_url=None,
        phone=None,
        source_order=1,
    )
    db_session.add(location)
    db_session.flush()
    base = datetime(2026, 1, 1, tzinfo=UTC)
    for index in range(count):
        title = f"코스 {index:02d}"
        if index == 7:
            title = "한강 & 야경 <추천>"
        course = Course(
            public_id=f"{index:032x}",
            title=title,
            password="1234",
            created_at=base + timedelta(minutes=index),
            updated_at=base + timedelta(minutes=index),
        )
        course.stops.append(CourseStop(position=1, location=location))
        db_session.add(course)
    db_session.commit()


def test_admin_lists_latest_courses_with_stops_and_pagination(
    admin_client_factory: Callable[[str | None], TestClient],
    db_session: Session,
):
    seed_admin_courses(db_session)
    client = admin_client_factory("operator-pass")

    first = client.get("/admin/courses", auth=("admin", "operator-pass"))
    second = client.get("/admin/courses?page=2", auth=("admin", "operator-pass"))

    assert first.status_code == 200
    assert first.text.index("코스 22") < first.text.index("코스 21")
    assert "코스 03" in first.text
    assert "코스 02" not in first.text
    assert "관리자 &amp; 장소 &lt;확인&gt;" in first.text
    assert "1 / 2 페이지" in first.text
    assert second.status_code == 200
    assert "코스 02" in second.text
    assert "코스 00" in second.text
    assert "2 / 2 페이지" in second.text


def test_admin_searches_title_and_escapes_html(
    admin_client_factory: Callable[[str | None], TestClient],
    db_session: Session,
):
    seed_admin_courses(db_session, count=10)
    client = admin_client_factory("operator-pass")

    response = client.get(
        "/admin/courses?q=%EC%95%BC%EA%B2%BD",
        auth=("admin", "operator-pass"),
    )

    assert response.status_code == 200
    assert "한강 &amp; 야경 &lt;추천&gt;" in response.text
    assert "코스 06" not in response.text
    assert 'value="야경"' in response.text


def test_admin_shows_empty_state_and_clamps_page(
    admin_client_factory: Callable[[str | None], TestClient],
    db_session: Session,
):
    seed_admin_courses(db_session, count=2)
    client = admin_client_factory("operator-pass")

    empty = client.get(
        "/admin/courses?q=missing",
        auth=("admin", "operator-pass"),
    )
    beyond = client.get("/admin/courses?page=99", auth=("admin", "operator-pass"))

    assert empty.status_code == 200
    assert "검색 결과가 없습니다" in empty.text
    assert beyond.status_code == 200
    assert "1 / 1 페이지" in beyond.text
    assert "코스 01" in beyond.text
