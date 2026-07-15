from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.admin.auth import require_admin
from app.admin.courses import list_courses
from app.admin.views import render_course_list
from app.db import get_db

router = APIRouter(include_in_schema=False)
AdminAccess = Annotated[None, Depends(require_admin)]
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/courses", response_class=HTMLResponse)
def course_list(
    _: AdminAccess,
    session: DatabaseSession,
    q: Annotated[str, Query(max_length=100)] = "",
    page: Annotated[int, Query(ge=1)] = 1,
) -> HTMLResponse:
    result = list_courses(session, q, page)
    return HTMLResponse(render_course_list(result))
