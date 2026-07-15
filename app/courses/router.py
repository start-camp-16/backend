from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.courses.schemas import (
    CourseCreate,
    CourseDetail,
    CoursePasswordRequest,
    CourseSuggestionRequest,
    CourseSuggestionResponse,
    CourseUpdate,
)
from app.courses.service import (
    create_course,
    delete_course,
    get_course,
    suggest_course,
    update_course,
)
from app.db import get_db

router = APIRouter(prefix="/api")
PublicIdPath = Annotated[str, Path(min_length=32, max_length=32, pattern=r"^[0-9a-f]{32}$")]


@router.post(
    "/course-suggestions",
    response_model=CourseSuggestionResponse,
    operation_id="createCourseSuggestion",
)
def create_suggestion(
    payload: CourseSuggestionRequest,
    session: Annotated[Session, Depends(get_db)],
) -> CourseSuggestionResponse:
    return suggest_course(session, payload)


@router.post(
    "/courses",
    response_model=CourseDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createCourse",
)
def create(
    payload: CourseCreate,
    session: Annotated[Session, Depends(get_db)],
) -> CourseDetail:
    return create_course(session, payload)


@router.get(
    "/courses/{public_id}",
    response_model=CourseDetail,
    operation_id="getCourse",
)
def detail(
    public_id: PublicIdPath,
    session: Annotated[Session, Depends(get_db)],
) -> CourseDetail:
    return get_course(session, public_id)


@router.put(
    "/courses/{public_id}",
    response_model=CourseDetail,
    operation_id="updateCourse",
)
def update(
    public_id: PublicIdPath,
    payload: CourseUpdate,
    session: Annotated[Session, Depends(get_db)],
) -> CourseDetail:
    return update_course(session, public_id, payload)


@router.delete(
    "/courses/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteCourse",
)
def delete(
    public_id: PublicIdPath,
    payload: CoursePasswordRequest,
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_course(session, public_id, payload.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
