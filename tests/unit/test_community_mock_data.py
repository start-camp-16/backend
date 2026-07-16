from collections import Counter

from app.community.classifications import POST_PREFIXES
from app.community.mock_data import build_community_mock_posts


def test_builds_five_gangnam_posts_for_every_prefix() -> None:
    posts = build_community_mock_posts()

    assert len(posts) == 35
    assert {post.district for post in posts} == {"강남구"}
    assert Counter(post.prefix for post in posts) == Counter(
        {prefix: 5 for prefix in POST_PREFIXES}
    )


def test_every_post_has_three_or_four_contextual_comments() -> None:
    posts = build_community_mock_posts()

    assert {len(post.comments) for post in posts} == {3, 4}
    assert all(comment.content.strip() for post in posts for comment in post.comments)


def test_each_prefix_uses_distinct_comment_copy() -> None:
    posts = build_community_mock_posts()
    first_comment_set_by_prefix = {
        prefix: tuple(
            comment.content
            for comment in next(post for post in posts if post.prefix == prefix).comments
        )
        for prefix in POST_PREFIXES
    }

    assert len(set(first_comment_set_by_prefix.values())) == len(POST_PREFIXES)


def test_build_is_deterministic_and_titles_are_unique() -> None:
    posts = build_community_mock_posts()

    assert posts == build_community_mock_posts()
    assert len({post.title for post in posts}) == 35
