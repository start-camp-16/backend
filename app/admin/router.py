from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.admin.auth import require_admin
from app.admin.courses import delete_course_as_admin, list_courses
from app.admin.views import render_course_list
from app.db import get_db

router = APIRouter(include_in_schema=False)
AdminAccess = Annotated[None, Depends(require_admin)]
DatabaseSession = Annotated[Session, Depends(get_db)]
PublicIdPath = Annotated[
    str,
    Path(min_length=32, max_length=32, pattern=r"^[0-9a-f]{32}$"),
]


@router.get("/courses", response_class=HTMLResponse)
def course_list(
    _: AdminAccess,
    session: DatabaseSession,
    q: Annotated[str, Query(max_length=100)] = "",
    page: Annotated[int, Query(ge=1)] = 1,
) -> HTMLResponse:
    result = list_courses(session, q, page)
    return HTMLResponse(render_course_list(result))


@router.post("/courses/{public_id}/delete", response_class=RedirectResponse)
def force_delete_course(
    _: AdminAccess,
    session: DatabaseSession,
    public_id: PublicIdPath,
    q: Annotated[str, Query(max_length=100)] = "",
    page: Annotated[int, Query(ge=1)] = 1,
) -> RedirectResponse:
    delete_course_as_admin(session, public_id)
    params: dict[str, str | int] = {"page": page}
    if q.strip():
        params["q"] = q.strip()
    return RedirectResponse(
        url=f"/admin/courses?{urlencode(params)}",
        status_code=303,
    )
