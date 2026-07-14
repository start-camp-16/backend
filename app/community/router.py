from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.community.posts import create_post, delete_post, get_post, list_posts, update_post
from app.community.schemas import (
    PasswordRequest,
    PostCreate,
    PostDetail,
    PostListResponse,
    PostTag,
    PostUpdate,
)
from app.db import get_db

router = APIRouter(prefix="/api")
PostId = Annotated[int, Path(ge=1)]


@router.get("/posts", response_model=PostListResponse, operation_id="getPosts")
def posts(
    session: Annotated[Session, Depends(get_db)],
    tag: PostTag | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PostListResponse:
    return list_posts(session, tag=tag, query=q, page=page, size=size)


@router.post(
    "/posts",
    response_model=PostDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createPost",
)
def create(payload: PostCreate, session: Annotated[Session, Depends(get_db)]) -> PostDetail:
    return create_post(session, payload)


@router.get("/posts/{post_id}", response_model=PostDetail, operation_id="getPost")
def detail(
    post_id: PostId,
    session: Annotated[Session, Depends(get_db)],
) -> PostDetail:
    return get_post(session, post_id)


@router.put("/posts/{post_id}", response_model=PostDetail, operation_id="updatePost")
def update(
    post_id: PostId,
    payload: PostUpdate,
    session: Annotated[Session, Depends(get_db)],
) -> PostDetail:
    return update_post(session, post_id, payload)


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deletePost",
)
def delete(
    post_id: PostId,
    payload: PasswordRequest,
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_post(session, post_id, payload.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
