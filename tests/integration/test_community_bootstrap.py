from collections import Counter
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, sessionmaker
from starlette.testclient import TestClient

from app.community.bootstrap import (
    COMMUNITY_MOCK_POSTS,
    MockPostSeed,
    ensure_community_mock_data,
)
from app.community.classifications import POST_DISTRICTS, POST_PREFIXES
from app.main import create_app
from app.models import Comment, Post


def test_empty_database_gets_three_posts_per_district_and_fixed_comments(
    db_engine: Engine,
) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)

    inserted = ensure_community_mock_data(session_factory)

    with session_factory() as session:
        posts = list(
            session.scalars(
                select(Post).options(selectinload(Post.comments)).order_by(Post.created_at)
            )
        )

    assert inserted == 75
    assert len(posts) == 75
    assert Counter(post.district for post in posts) == Counter(
        {district: 3 for district in POST_DISTRICTS}
    )
    assert set(post.prefix for post in posts) == set(POST_PREFIXES)
    assert set(Counter(post.prefix for post in posts).values()) == {10, 11}
    assert sum(len(post.comments) for post in posts) == 25
    assert all(post.password == "mock1234" for post in posts)
    assert all(comment.password == "mock1234" for post in posts for comment in post.comments)
    assert all(comment.created_at > post.created_at for post in posts for comment in post.comments)


def test_second_bootstrap_does_not_duplicate_data(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    ensure_community_mock_data(session_factory)

    inserted = ensure_community_mock_data(session_factory)

    with session_factory() as session:
        assert session.scalar(select(func.count(Post.id))) == 75
        assert session.scalar(select(func.count(Comment.id))) == sum(
            len(seed.comments) for seed in COMMUNITY_MOCK_POSTS
        )
    assert inserted is None


def test_existing_post_prevents_all_mock_inserts(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    existing_time = datetime(2024, 12, 31, tzinfo=UTC)
    with session_factory.begin() as session:
        session.add(
            Post(
                district="강남구",
                prefix="자유",
                title="기존 게시글",
                content="사용자가 먼저 작성한 글",
                password="1234",
                created_at=existing_time,
                updated_at=existing_time,
            )
        )

    inserted = ensure_community_mock_data(session_factory)

    with session_factory() as session:
        posts = list(session.scalars(select(Post)))
        assert len(posts) == 1
        assert posts[0].title == "기존 게시글"
        assert session.scalar(select(func.count(Comment.id))) == 0
    assert inserted is None


def test_failed_seed_rolls_back_every_post_and_comment(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
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
        ensure_community_mock_data(session_factory, seeds=invalid_seeds)

    with session_factory() as session:
        assert session.scalar(select(func.count(Post.id))) == 0
        assert session.scalar(select(func.count(Comment.id))) == 0


def test_startup_bootstraps_community_when_enabled(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    app = create_app(
        bootstrap_community=True,
        session_factory=session_factory,
    )

    with TestClient(app):
        pass

    with session_factory() as session:
        assert session.scalar(select(func.count(Post.id))) == 75


def test_startup_keeps_existing_community_data(db_engine: Engine) -> None:
    session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    existing_time = datetime(2024, 12, 31, tzinfo=UTC)
    with session_factory.begin() as session:
        session.add(
            Post(
                district="강남구",
                prefix="자유",
                title="운영 게시글",
                content="재배포 뒤에도 유지되어야 하는 글",
                password="1234",
                created_at=existing_time,
                updated_at=existing_time,
            )
        )
    app = create_app(
        bootstrap_community=True,
        session_factory=session_factory,
    )

    with TestClient(app):
        pass

    with session_factory() as session:
        assert session.scalar(select(func.count(Post.id))) == 1
        assert session.scalar(select(Post.title)) == "운영 게시글"
