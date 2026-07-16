from app.courses.demo_presets import GANGNAM_DEMO_CONTENT_IDS, match_demo_course


def test_matches_gangnam_demo_request_regardless_of_category_order() -> None:
    assert (
        match_demo_course("강남구", ["쇼핑", "문화시설", "숙박"], 5)
        == GANGNAM_DEMO_CONTENT_IDS
    )
    assert (
        match_demo_course("강남구", ["숙박", "쇼핑", "문화시설"], 5)
        == GANGNAM_DEMO_CONTENT_IDS
    )


def test_rejects_every_non_demo_condition() -> None:
    assert match_demo_course("서초구", ["쇼핑", "문화시설", "숙박"], 5) is None
    assert match_demo_course("강남구", ["쇼핑", "문화시설"], 5) is None
    assert match_demo_course("강남구", ["쇼핑", "문화시설", "숙박"], 4) is None
