import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from time import perf_counter

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.community.mock_data import COMMUNITY_MOCK_POSTS, MOCK_PASSWORD, MockPostSeed
from app.models import Comment, Post

logger = logging.getLogger(__name__)

MOCK_DATA_STARTED_AT = datetime(2025, 1, 1, 3, tzinfo=UTC)
MOCK_DISTRICT = "강남구"


def _add_community_mock_posts(session: Session, seeds: Sequence[MockPostSeed]) -> None:
    for post_index, seed in enumerate(seeds):
        post_created_at = MOCK_DATA_STARTED_AT + timedelta(days=post_index)
        post = Post(
            district=seed.district,
            prefix=seed.prefix,
            title=seed.title,
            content=seed.content,
            password=MOCK_PASSWORD,
            created_at=post_created_at,
            updated_at=post_created_at,
        )
        post.comments = [
            Comment(
                content=comment_seed.content,
                password=MOCK_PASSWORD,
                created_at=post_created_at + timedelta(minutes=comment_index + 1),
                updated_at=post_created_at + timedelta(minutes=comment_index + 1),
            )
            for comment_index, comment_seed in enumerate(seed.comments)
        ]
        session.add(post)


def reset_community_mock_data(
    session_factory: sessionmaker[Session],
    seeds: Sequence[MockPostSeed] = COMMUNITY_MOCK_POSTS,
) -> int:
    started_at = perf_counter()
    expected_comments = sum(len(seed.comments) for seed in seeds)
    with session_factory.begin() as session:
        session.execute(delete(Post).where(Post.district == MOCK_DISTRICT))
        _add_community_mock_posts(session, seeds)
        session.flush()
        inserted_posts = session.scalar(
            select(func.count(Post.id)).where(Post.district == MOCK_DISTRICT)
        ) or 0
        inserted_comments = session.scalar(
            select(func.count(Comment.id))
            .join(Post, Comment.post_id == Post.id)
            .where(Post.district == MOCK_DISTRICT)
        ) or 0
        if inserted_posts != len(seeds) or inserted_comments != expected_comments:
            raise RuntimeError("Community mock reset produced unexpected row counts")

    logger.info(
        "Community mock reset completed",
        extra={
            "inserted_posts": inserted_posts,
            "inserted_comments": inserted_comments,
            "elapsed_ms": round((perf_counter() - started_at) * 1000, 2),
        },
    )
    return len(seeds)
