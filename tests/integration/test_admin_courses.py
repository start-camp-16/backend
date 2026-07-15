from collections.abc import Callable, Generator

import pytest
from fastapi import FastAPI
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.config import Settings
from app.db import get_db as app_get_db
from app.main import create_app


@pytest.fixture
def admin_client_factory(
    db_session: Session,
) -> Generator[Callable[[str | None], TestClient], None, None]:
    clients: list[tuple[FastAPI, TestClient]] = []

    def factory(password: str | None) -> TestClient:
        settings = Settings(_env_file=None, admin_password=password)
        app = create_app(settings=settings)

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
