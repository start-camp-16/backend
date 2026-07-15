from dataclasses import dataclass
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.errors import AppError
from app.models import Course, CourseStop


@dataclass(frozen=True)
class CourseListPage:
    items: tuple[Course, ...]
    query: str
    page: int
    page_size: int
    total_items: int
    total_pages: int


def _literal_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_courses(
    session: Session,
    query: str,
    page: int,
    page_size: int = 20,
) -> CourseListPage:
    normalized = query.strip()
    filters: list[ColumnElement[bool]] = []
    if normalized:
        filters.append(Course.title.ilike(f"%{_literal_like(normalized)}%", escape="\\"))

    total_items = session.scalar(select(func.count(Course.id)).where(*filters)) or 0
    total_pages = max(1, ceil(total_items / page_size))
    resolved_page = min(page, total_pages)
    statement = (
        select(Course)
        .where(*filters)
        .options(selectinload(Course.stops).selectinload(CourseStop.location))
        .order_by(Course.created_at.desc(), Course.id.desc())
        .offset((resolved_page - 1) * page_size)
        .limit(page_size)
    )
    return CourseListPage(
        items=tuple(session.scalars(statement)),
        query=normalized,
        page=resolved_page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
    )


def delete_course_as_admin(session: Session, public_id: str) -> None:
    course = session.scalar(select(Course).where(Course.public_id == public_id))
    if course is None:
        raise AppError(
            status_code=404,
            code="COURSE_NOT_FOUND",
            message="코스를 찾을 수 없습니다.",
        )
    session.delete(course)
    session.commit()
