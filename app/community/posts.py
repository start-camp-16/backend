from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.community.classifications import PostDistrict, PostPrefix
from app.community.schemas import (
    PostCreate,
    PostDetail,
    PostListResponse,
    PostSummary,
    PostUpdate,
)
from app.errors import AppError
from app.models import Post
from app.schemas import Pagination


def post_not_found() -> AppError:
    return AppError(
        status_code=404,
        code="POST_NOT_FOUND",
        message="게시글을 찾을 수 없습니다.",
    )


def password_mismatch() -> AppError:
    return AppError(
        status_code=403,
        code="PASSWORD_MISMATCH",
        message="비밀번호가 일치하지 않습니다.",
    )


def require_post(session: Session, post_id: int) -> Post:
    post = session.get(Post, post_id)
    if post is None:
        raise post_not_found()
    return post


def create_post(session: Session, payload: PostCreate) -> PostDetail:
    post = Post(
        district=payload.district.value,
        prefix=payload.prefix.value,
        title=payload.title,
        content=payload.content,
        password=payload.password,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return PostDetail.model_validate(post)


def get_post(session: Session, post_id: int) -> PostDetail:
    return PostDetail.model_validate(require_post(session, post_id))


def list_posts(
    session: Session,
    *,
    district: PostDistrict | None,
    prefix: PostPrefix | None,
    query: str | None,
    page: int,
    size: int,
) -> PostListResponse:
    filters = []
    if district is not None:
        filters.append(Post.district == district.value)
    if prefix is not None:
        filters.append(Post.prefix == prefix.value)
    normalized_query = query.strip() if query else ""
    if normalized_query:
        lowered_query = normalized_query.lower()
        filters.append(
            or_(
                func.lower(Post.title).contains(lowered_query, autoescape=True),
                func.lower(Post.content).contains(lowered_query, autoescape=True),
            )
        )

    total_items = session.scalar(select(func.count()).select_from(Post).where(*filters)) or 0
    rows = list(
        session.scalars(
            select(Post)
            .where(*filters)
            .order_by(Post.created_at.desc(), Post.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    )
    total_pages = (total_items + size - 1) // size if total_items else 0
    return PostListResponse(
        items=[PostSummary.model_validate(post) for post in rows],
        pagination=Pagination(
            page=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


def update_post(session: Session, post_id: int, payload: PostUpdate) -> PostDetail:
    post = require_post(session, post_id)
    if post.password != payload.password:
        raise password_mismatch()
    post.district = payload.district.value
    post.prefix = payload.prefix.value
    post.title = payload.title
    post.content = payload.content
    session.commit()
    session.refresh(post)
    return PostDetail.model_validate(post)


def delete_post(session: Session, post_id: int, password: str) -> None:
    post = require_post(session, post_id)
    if post.password != password:
        raise password_mismatch()
    session.delete(post)
    session.commit()
