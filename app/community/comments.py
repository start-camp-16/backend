from sqlalchemy import select
from sqlalchemy.orm import Session

from app.community.posts import password_mismatch, require_post
from app.community.schemas import CommentCreate, CommentDetail, CommentListResponse, CommentUpdate
from app.errors import AppError
from app.models import Comment


def comment_not_found() -> AppError:
    return AppError(
        status_code=404,
        code="COMMENT_NOT_FOUND",
        message="댓글을 찾을 수 없습니다.",
    )


def require_comment(session: Session, comment_id: int) -> Comment:
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise comment_not_found()
    return comment


def list_comments(session: Session, post_id: int) -> CommentListResponse:
    require_post(session, post_id)
    rows = list(
        session.scalars(
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc(), Comment.id.asc())
        )
    )
    return CommentListResponse(items=[CommentDetail.model_validate(row) for row in rows])


def create_comment(session: Session, post_id: int, payload: CommentCreate) -> CommentDetail:
    require_post(session, post_id)
    comment = Comment(
        post_id=post_id,
        content=payload.content,
        password=payload.password,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return CommentDetail.model_validate(comment)


def update_comment(session: Session, comment_id: int, payload: CommentUpdate) -> CommentDetail:
    comment = require_comment(session, comment_id)
    if comment.password != payload.password:
        raise password_mismatch()
    comment.content = payload.content
    session.commit()
    session.refresh(comment)
    return CommentDetail.model_validate(comment)


def delete_comment(session: Session, comment_id: int, password: str) -> None:
    comment = require_comment(session, comment_id)
    if comment.password != password:
        raise password_mismatch()
    session.delete(comment)
    session.commit()
