from datetime import UTC

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Comment, Location, Post


def make_location(content_id: str = "100") -> Location:
    return Location(
        content_id=content_id,
        category="관광지",
        title="테스트 장소",
        address1="서울특별시 강남구 테헤란로",
        address2=None,
        district="강남구",
        longitude=127.0,
        latitude=37.5,
        image_url=None,
        thumbnail_url=None,
        phone=None,
        source_order=1,
    )


def test_location_content_id_is_unique(db_session: Session):
    db_session.add_all([make_location(), make_location()])

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_location_ranking_index_has_expected_column_order(db_engine):
    indexes = inspect(db_engine).get_indexes("locations")
    ranking_index = next(
        index for index in indexes if index["name"] == "ix_locations_category_district_order"
    )

    assert ranking_index["column_names"] == ["category", "district", "source_order"]


def test_deleting_post_cascades_comments(db_session: Session):
    post = Post(tag="자유", title="제목", content="본문", password="1234")
    post.comments.append(Comment(content="댓글", password="5678"))
    db_session.add(post)
    db_session.commit()

    db_session.delete(post)
    db_session.commit()

    assert db_session.scalar(select(func.count(Comment.id))) == 0


def test_post_timestamps_are_utc(db_session: Session):
    post = Post(tag="자유", title="제목", content="본문", password="1234")
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    assert post.created_at.tzinfo is UTC
    assert post.updated_at.tzinfo is UTC
