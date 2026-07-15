from app.chat.query import parse_query


def test_query_extracts_known_terms_and_remaining_keywords():
    parsed = parse_query("강남구 문화시설 전시 추천")

    assert parsed.district == "강남구"
    assert parsed.location_category == "문화시설"
    assert parsed.post_prefix is None
    assert parsed.keywords == ("전시", "추천")


def test_query_extracts_community_prefix():
    parsed = parse_query("마포구 자유 자전거 모임")

    assert parsed.district == "마포구"
    assert parsed.location_category is None
    assert parsed.post_prefix == "자유"
    assert parsed.keywords == ("자전거", "모임")


def test_query_uses_longest_location_category_first():
    parsed = parse_query("문화시설 알려줘")

    assert parsed.location_category == "문화시설"
    assert parsed.post_prefix is None
    assert parsed.keywords == ()
