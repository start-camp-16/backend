from collections import Counter

from app.community.classifications import POST_DISTRICTS, POST_PREFIXES
from app.community.mock_data import build_community_mock_posts


def test_builds_five_posts_per_district() -> None:
    posts = build_community_mock_posts()

    assert len(posts) == 125
    assert Counter(post.district for post in posts) == Counter(
        {district: 5 for district in POST_DISTRICTS}
    )


def test_each_district_has_three_shared_and_two_specific_posts() -> None:
    posts = build_community_mock_posts()

    for district in POST_DISTRICTS:
        district_posts = [post for post in posts if post.district == district]
        assert Counter(post.kind for post in district_posts) == {
            "shared": 3,
            "specific": 2,
        }


def test_build_distributes_prefixes_and_bounded_comments() -> None:
    posts = build_community_mock_posts()

    assert set(post.prefix for post in posts) == set(POST_PREFIXES)
    assert set(Counter(post.prefix for post in posts).values()) == {17, 18}
    comment_counts = [len(post.comments) for post in posts]
    assert set(comment_counts) <= {0, 1, 2, 3}
    assert 0 in comment_counts
    assert 3 in comment_counts


def test_build_is_deterministic() -> None:
    assert build_community_mock_posts() == build_community_mock_posts()


def test_specific_posts_mention_two_distinct_district_features() -> None:
    posts = build_community_mock_posts()

    for district in POST_DISTRICTS:
        specific_posts = [
            post for post in posts if post.district == district and post.kind == "specific"
        ]
        assert len({post.title for post in specific_posts}) == 2
        assert all(district in post.content for post in specific_posts)
