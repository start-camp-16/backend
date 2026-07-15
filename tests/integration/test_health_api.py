import logging

from starlette.testclient import TestClient

from app.db import get_db
from app.main import create_app


def test_health_checks_database(client: TestClient):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_request_log_contains_metadata_without_body(client: TestClient, caplog):
    caplog.set_level(logging.INFO, logger="app.main")

    client.post(
        "/api/posts",
        json={
            "district": "강남구",
            "prefix": "자유",
            "title": "제목",
            "content": "본문",
            "password": "secret-1234",
        },
    )

    records = [record for record in caplog.records if record.message == "Request completed"]
    assert len(records) == 1
    assert records[0].method == "POST"
    assert records[0].status_code == 201
    assert records[0].elapsed_ms >= 0
    assert "secret-1234" not in caplog.text


def test_health_database_failure_uses_internal_error_contract():
    class FailingSession:
        def execute(self, statement):
            raise RuntimeError("database unavailable")

    app = create_app()
    app.dependency_overrides[get_db] = lambda: FailingSession()

    response = TestClient(app, raise_server_exceptions=False).get("/api/health")

    assert response.status_code == 500
    assert response.json() == {
        "code": "INTERNAL_ERROR",
        "message": "서버 오류가 발생했습니다.",
        "details": None,
    }
