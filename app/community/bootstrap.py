import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.community.mock_data import COMMUNITY_MOCK_POSTS, MOCK_PASSWORD, MockPostSeed
from app.models import Comment, Post

logger = logging.getLogger(__name__)

MOCK_DATA_STARTED_AT = datetime(2025, 1, 1, 3, tzinfo=UTC)


def ensure_community_mock_data(
    session_factory: sessionmaker[Session],
    seeds: Sequence[MockPostSeed] = COMMUNITY_MOCK_POSTS,
) -> int | None:
    with session_factory.begin() as session:
        if session.scalar(select(Post.id).limit(1)) is not None:
            logger.info("Community mock bootstrap skipped because a post already exists")
            return None

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

    inserted = len(seeds)
    logger.info("Community mock bootstrap completed", extra={"inserted": inserted})
    return inserted
