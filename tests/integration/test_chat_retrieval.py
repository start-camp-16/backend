from sqlalchemy.orm import Session

from app.chat.query import parse_query
from app.chat.retrieval import retrieve_sources
from app.models import Location, Post


def seed_chat_data(db_session: Session) -> None:
    db_session.add_all(
        [
            Location(
                content_id="1",
                category="문화시설",
                title="한강 미술관",
                address1="서울특별시 강남구 한강로",
                district="강남구",
                longitude=0,
                latitude=0,
                source_order=2,
            ),
            Location(
                content_id="2",
                category="문화시설",
                title="전시 문화관",
                address1="서울특별시 강남구 테헤란로",
                district="강남구",
                longitude=127.0,
                latitude=37.5,
                source_order=1,
            ),
            Location(
                content_id="3",
                category="관광지",
                title="전시와 무관한 장소",
                district="강남구",
                source_order=1,
            ),
            Post(tag="문화", title="강남 전시 후기", content="좋았어요", password="1234"),
            Post(tag="자유", title="강남 전시 모임", content="같이 가요", password="1234"),
        ]
    )
    db_session.commit()


def test_retrieval_combines_filters_keywords_and_limits(db_session: Session):
    seed_chat_data(db_session)

    context = retrieve_sources(
        db_session,
        parse_query("강남구 문화시설 전시"),
        location_limit=1,
        post_limit=5,
    )

    assert [location.content_id for location in context.locations] == ["2"]
    assert [post.title for post in context.posts] == ["강남 전시 모임", "강남 전시 후기"]


def test_zero_coordinates_are_removed_from_evidence(db_session: Session):
    seed_chat_data(db_session)

    context = retrieve_sources(
        db_session,
        parse_query("강남구 문화시설 한강"),
        location_limit=5,
        post_limit=5,
    )

    assert context.locations[0].content_id == "1"
    assert context.locations[0].longitude is None
    assert context.locations[0].latitude is None


def test_post_tag_filters_community_results(db_session: Session):
    seed_chat_data(db_session)

    context = retrieve_sources(
        db_session,
        parse_query("자유 전시"),
        location_limit=5,
        post_limit=5,
    )

    assert [post.tag for post in context.posts] == ["자유"]


def test_unrecognized_filter_with_no_matches_returns_empty(db_session: Session):
    seed_chat_data(db_session)

    context = retrieve_sources(
        db_session,
        parse_query("종로구 천문대"),
        location_limit=5,
        post_limit=5,
    )

    assert context.locations == []
    assert context.posts == []


def test_source_type_without_its_own_filter_is_not_broadly_queried(db_session: Session):
    seed_chat_data(db_session)

    location_only = retrieve_sources(
        db_session,
        parse_query("문화시설"),
        location_limit=5,
        post_limit=5,
    )
    post_only = retrieve_sources(
        db_session,
        parse_query("자유"),
        location_limit=5,
        post_limit=5,
    )

    assert location_only.locations
    assert location_only.posts == []
    assert post_only.locations == []
    assert post_only.posts
