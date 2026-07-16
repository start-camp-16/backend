import logging
from collections import Counter
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, sessionmaker
from starlette.testclient import TestClient

from app.community.bootstrap import (
    COMMUNITY_MOCK_POSTS,
    MOCK_DATA_STARTED_AT,
    MockPostSeed,
    reset_community_mock_data,
)
from app.community.classifications import POST_PREFIXES
from app.main import create_app
from app.models import Comment, Location, Post


def test_empty_database_gets_five_gangnam_posts_per_prefix(
    db_engine: Engine,
) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)

    inserted = reset_community_mock_data(session_factory)

    with session_factory() as session:
        posts = list(
            session.scalars(
                select(Post).options(selectinload(Post.comments)).order_by(Post.created_at)
            )
        )

    assert inserted == 35
    assert len(posts) == 35
    assert {post.district for post in posts} == {"강남구"}
    assert Counter(post.prefix for post in posts) == Counter(
        {prefix: 5 for prefix in POST_PREFIXES}
    )
    assert all(3 <= len(post.comments) <= 4 for post in posts)
    assert {len(post.comments) for post in posts} == {3, 4}
    assert all(post.password == "mock1234" for post in posts)
    assert all(comment.password == "mock1234" for post in posts for comment in post.comments)
    assert [post.created_at for post in posts] == [
        MOCK_DATA_STARTED_AT + timedelta(days=post_index) for post_index in range(35)
    ]
    assert all(comment.created_at > post.created_at for post in posts for comment in post.comments)


def test_repeated_reset_reproduces_the_same_data(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)

    def snapshot() -> list[tuple[str, str, str, str, tuple[str, ...]]]:
        with session_factory() as session:
            posts = session.scalars(
                select(Post).options(selectinload(Post.comments)).order_by(Post.created_at)
            )
            return [
                (
                    post.district,
                    post.prefix,
                    post.title,
                    post.content,
                    tuple(comment.content for comment in post.comments),
                )
                for post in posts
            ]

    reset_community_mock_data(session_factory)
    first_snapshot = snapshot()
    reset_community_mock_data(session_factory)

    assert snapshot() == first_snapshot


def test_reset_replaces_gangnam_and_preserves_other_districts(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    existing_time = datetime(2024, 12, 31, tzinfo=UTC)
    with session_factory.begin() as session:
        gangnam = Post(
            district="강남구",
            prefix="자유",
            title="기존 강남 게시글",
            content="교체될 데이터",
            password="1234",
            created_at=existing_time,
            updated_at=existing_time,
        )
        gangnam.comments = [Comment(content="기존 강남 댓글", password="1234")]
        mapo = Post(
            district="마포구",
            prefix="자유",
            title="보존할 마포 게시글",
            content="초기화 후에도 유지할 데이터",
            password="1234",
            created_at=existing_time,
            updated_at=existing_time,
        )
        mapo.comments = [Comment(content="보존할 마포 댓글", password="1234")]
        session.add_all([gangnam, mapo])

    inserted = reset_community_mock_data(session_factory)

    with session_factory() as session:
        assert inserted == 35
        assert session.scalar(
            select(func.count()).select_from(Post).where(Post.district == "강남구")
        ) == 35
        assert session.scalar(
            select(func.count()).select_from(Post).where(Post.title == "기존 강남 게시글")
        ) == 0
        assert session.scalar(
            select(func.count()).select_from(Post).where(Post.title == "보존할 마포 게시글")
        ) == 1
        assert session.scalar(
            select(func.count())
            .select_from(Comment)
            .where(Comment.content == "보존할 마포 댓글")
        ) == 1


def test_failed_seed_rolls_back_every_post_and_comment(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    existing_time = datetime(2024, 12, 31, tzinfo=UTC)
    with session_factory.begin() as session:
        session.add(
            Post(
                district="강남구",
                prefix="자유",
                title="롤백으로 보존할 글",
                content="초기화 실패 뒤에도 남아야 합니다.",
                password="1234",
                created_at=existing_time,
                updated_at=existing_time,
            )
        )
    invalid_seeds = (
        COMMUNITY_MOCK_POSTS[0],
        MockPostSeed(
            district="기타",
            prefix="자유",
            title="실패",
            content="전체 롤백 확인",
        ),
    )

    with pytest.raises(IntegrityError):
        reset_community_mock_data(session_factory, seeds=invalid_seeds)

    with session_factory() as session:
        assert session.scalar(select(func.count(Post.id))) == 1
        assert session.scalar(select(func.count(Comment.id))) == 0
        assert session.scalar(select(Post.title)) == "롤백으로 보존할 글"


def test_startup_bootstraps_community_when_enabled(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    app = create_app(
        bootstrap_community=True,
        session_factory=session_factory,
    )

    with TestClient(app):
        pass

    with session_factory() as session:
        assert session.scalar(
            select(func.count()).select_from(Post).where(Post.district == "강남구")
        ) == 35


def test_reset_logs_counts_and_duration(
    db_engine: Engine,
    caplog: pytest.LogCaptureFixture,
) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)

    with caplog.at_level(logging.INFO, logger="app.community.bootstrap"):
        reset_community_mock_data(session_factory)

    record = next(
        record for record in caplog.records if record.message == "Community mock reset completed"
    )
    assert record.inserted_posts == 35
    assert record.inserted_comments == sum(len(seed.comments) for seed in COMMUNITY_MOCK_POSTS)
    assert 0 <= record.elapsed_ms < 1000


def test_startup_replaces_existing_community_data_and_keeps_locations(
    db_engine: Engine,
) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    existing_time = datetime(2024, 12, 31, tzinfo=UTC)
    with session_factory.begin() as session:
        session.add_all(
            [
                Post(
                    district="강남구",
                    prefix="자유",
                    title="운영 게시글",
                    content="재배포 뒤에는 초기 데이터로 교체될 글",
                    password="1234",
                    created_at=existing_time,
                    updated_at=existing_time,
                ),
                Location(
                    content_id="startup-location",
                    category="관광지",
                    title="유지할 장소",
                    district="강남구",
                    source_order=1,
                ),
            ]
        )
    app = create_app(
        bootstrap_community=True,
        session_factory=session_factory,
    )

    with TestClient(app):
        pass

    with session_factory() as session:
        assert session.scalar(
            select(func.count()).select_from(Post).where(Post.district == "강남구")
        ) == 35
        assert session.scalar(
            select(func.count()).select_from(Post).where(Post.title == "운영 게시글")
        ) == 0
        assert session.scalar(
            select(func.count()).select_from(Location).where(
                Location.content_id == "startup-location"
            )
        ) == 1
