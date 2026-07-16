from app.courses.ranking_presets import COURSE_RANKING_PRESETS


def test_presets_cover_five_districts_in_rank_order() -> None:
    assert [preset.rank for preset in COURSE_RANKING_PRESETS] == [1, 2, 3, 4, 5]
    assert [preset.district for preset in COURSE_RANKING_PRESETS] == [
        "강남구",
        "마포구",
        "서초구",
        "송파구",
        "노원구",
    ]


def test_presets_have_three_to_five_unique_stops() -> None:
    for preset in COURSE_RANKING_PRESETS:
        assert 3 <= len(preset.content_ids) <= 5
        assert len(set(preset.content_ids)) == len(preset.content_ids)


def test_presets_keep_accommodation_as_the_final_stop() -> None:
    expected_last_accommodation_ids = {
        "강남구": "142769",
        "마포구": "2907142",
        "서초구": "143033",
        "송파구": "3464755",
    }

    for preset in COURSE_RANKING_PRESETS:
        expected_id = expected_last_accommodation_ids.get(preset.district)
        if expected_id is not None:
            assert preset.content_ids[-1] == expected_id
