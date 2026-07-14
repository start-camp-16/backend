from typing import Annotated

from fastapi import Query
from fastapi.testclient import TestClient

from app.errors import AppError
from app.main import create_app


def test_fastapi_validation_uses_shared_error_shape():
    app = create_app()

    @app.get("/probe")
    def probe(page: Annotated[int, Query(ge=1)]) -> dict[str, int]:
        return {"page": page}

    response = TestClient(app).get("/probe", params={"page": 0})

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert set(response.json()) == {"code", "message", "details"}


def test_known_domain_error_preserves_status_and_safe_message():
    app = create_app()

    @app.get("/failure")
    def failure() -> None:
        raise AppError(
            status_code=403,
            code="PASSWORD_MISMATCH",
            message="비밀번호가 일치하지 않습니다.",
        )

    response = TestClient(app).get("/failure")

    assert response.status_code == 403
    assert response.json() == {
        "code": "PASSWORD_MISMATCH",
        "message": "비밀번호가 일치하지 않습니다.",
        "details": None,
    }
