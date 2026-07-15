from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.admin.auth import require_admin

router = APIRouter(include_in_schema=False)
AdminAccess = Annotated[None, Depends(require_admin)]


@router.get("/courses", response_class=HTMLResponse)
def course_list(_: AdminAccess) -> HTMLResponse:
    return HTMLResponse(
        '<!doctype html><html lang="ko"><meta charset="utf-8">'
        "<title>저장된 코스</title><body><h1>저장된 코스</h1></body></html>"
    )
