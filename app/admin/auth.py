from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.config import Settings

security = HTTPBasic(auto_error=False)


@dataclass(frozen=True)
class AdminAuthError(Exception):
    status_code: int
    message: str
    request_credentials: bool = False


def _matches(left: str, right: str) -> bool:
    left_digest = sha256(left.encode()).digest()
    right_digest = sha256(right.encode()).digest()
    return compare_digest(left_digest, right_digest)


def require_admin(
    request: Request,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(security)],
) -> None:
    settings: Settings = request.app.state.settings
    configured = settings.admin_password
    if configured is None or not configured.get_secret_value():
        raise AdminAuthError(
            status_code=503,
            message="관리자 기능을 사용하려면 ADMIN_PASSWORD를 설정해 주세요.",
        )

    valid = (
        credentials is not None
        and _matches(credentials.username, "admin")
        and _matches(credentials.password, configured.get_secret_value())
    )
    if not valid:
        raise AdminAuthError(
            status_code=401,
            message="관리자 비밀번호를 확인해 주세요.",
            request_credentials=True,
        )


def register_admin_exception_handler(app: FastAPI) -> None:
    @app.exception_handler(AdminAuthError)
    async def handle_admin_auth_error(
        request: Request,
        exception: AdminAuthError,
    ) -> HTMLResponse:
        del request
        headers = (
            {"WWW-Authenticate": 'Basic realm="course-admin"'}
            if exception.request_credentials
            else None
        )
        content = (
            '<!doctype html><html lang="ko"><meta charset="utf-8">'
            "<title>관리자 접근 오류</title>"
            f"<body><h1>{exception.message}</h1></body></html>"
        )
        return HTMLResponse(content, status_code=exception.status_code, headers=headers)
