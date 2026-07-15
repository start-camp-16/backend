import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.community.classifications import POST_DISTRICTS, POST_PREFIXES
from app.models import Comment, Post

logger = logging.getLogger(__name__)

MOCK_PASSWORD = "mock1234"
MOCK_DATA_STARTED_AT = datetime(2025, 1, 1, 3, tzinfo=UTC)


@dataclass(frozen=True)
class MockCommentSeed:
    content: str


@dataclass(frozen=True)
class MockPostSeed:
    district: str
    prefix: str
    title: str
    content: str
    comments: tuple[MockCommentSeed, ...] = ()


def comment(content: str) -> MockCommentSeed:
    return MockCommentSeed(content=content)


POST_TEMPLATES = (
    (
        "{district}에서 가볍게 걷기 좋은 곳을 공유해요",
        "{district}에서 대중교통으로 가기 편하고 천천히 걷기 좋은 장소를 찾고 있어요. "
        "붐비는 시간대와 쉬어 갈 수 있는 지점을 함께 알려 주시면 좋겠습니다.",
        "산책 동선을 고를 때 참고할게요.",
    ),
    (
        "{district}에서 혼자 식사하기 좋은 곳이 궁금해요",
        "{district}에서 혼자 방문해도 부담 없고 식사 시간이 오래 걸리지 않는 곳을 "
        "찾고 있습니다. 대표 메뉴와 비교적 여유로운 방문 시간도 공유해 주세요.",
        None,
    ),
    (
        "{district} 주말 나들이 정보를 모아봐요",
        "이번 주말에 {district} 안에서 즐길 수 있는 전시, 행사, 시장 정보를 찾고 있어요. "
        "예약 여부와 대중교통 이용 팁이 있다면 함께 남겨 주세요.",
        None,
    ),
)


def build_community_mock_posts() -> tuple[MockPostSeed, ...]:
    seeds = []
    prefix_count = len(POST_PREFIXES)
    for district_index, district in enumerate(POST_DISTRICTS):
        for post_index, (title, content, comment_text) in enumerate(POST_TEMPLATES):
            prefix = POST_PREFIXES[
                (district_index * len(POST_TEMPLATES) + post_index) % prefix_count
            ]
            comments = (comment(comment_text),) if comment_text else ()
            seeds.append(
                MockPostSeed(
                    district=district,
                    prefix=prefix,
                    title=title.format(district=district),
                    content=content.format(district=district),
                    comments=comments,
                )
            )
    return tuple(seeds)


COMMUNITY_MOCK_POSTS = build_community_mock_posts()


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
