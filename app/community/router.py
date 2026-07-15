from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.community.classifications import PostDistrict, PostPrefix
from app.community.comments import (
    create_comment,
    delete_comment,
    list_comments,
    update_comment,
)
from app.community.posts import create_post, delete_post, get_post, list_posts, update_post
from app.community.schemas import (
    CommentCreate,
    CommentDetail,
    CommentListResponse,
    CommentUpdate,
    PasswordRequest,
    PostCreate,
    PostDetail,
    PostListResponse,
    PostUpdate,
)
from app.db import get_db

router = APIRouter(prefix="/api")
PostId = Annotated[int, Path(ge=1)]
CommentId = Annotated[int, Path(ge=1)]


@router.get("/posts", response_model=PostListResponse, operation_id="getPosts")
def posts(
    session: Annotated[Session, Depends(get_db)],
    district: PostDistrict | None = None,
    prefix: PostPrefix | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PostListResponse:
    return list_posts(
        session,
        district=district,
        prefix=prefix,
        query=q,
        page=page,
        size=size,
    )


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


@router.get(
    "/posts/{post_id}/comments",
    response_model=CommentListResponse,
    operation_id="getComments",
)
def comments(
    post_id: PostId,
    session: Annotated[Session, Depends(get_db)],
) -> CommentListResponse:
    return list_comments(session, post_id)


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommentDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="createComment",
)
def create_post_comment(
    post_id: PostId,
    payload: CommentCreate,
    session: Annotated[Session, Depends(get_db)],
) -> CommentDetail:
    return create_comment(session, post_id, payload)


@router.put(
    "/comments/{comment_id}",
    response_model=CommentDetail,
    operation_id="updateComment",
)
def update_post_comment(
    comment_id: CommentId,
    payload: CommentUpdate,
    session: Annotated[Session, Depends(get_db)],
) -> CommentDetail:
    return update_comment(session, comment_id, payload)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteComment",
)
def delete_post_comment(
    comment_id: CommentId,
    payload: PasswordRequest,
    session: Annotated[Session, Depends(get_db)],
) -> Response:
    delete_comment(session, comment_id, payload.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
