from scripts.generate_recommendations import build_recommendations


def test_build_recommendations_selects_five_scored_places_per_combination():
    items = [
        {
            "contentid": str(index),
            "title": title,
            "addr1": "서울특별시 강남구 테헤란로",
            "firstimage": "image.jpg" if index != 6 else "",
        }
        for index, title in enumerate(
            ["일반 장소", "한강 공원", "역사 박물관", "전망 공원", "서울 숲", "문화 광장"],
            start=1,
        )
    ]

    result = build_recommendations([("관광지", items)])

    assert len(result) == 1
    assert result[0]["district"] == "강남구"
    assert result[0]["category"] == "관광지"
    assert result[0]["contentIds"] == ["2", "3", "4", "5", "6"]


def test_build_recommendations_keeps_short_combinations():
    items = [
        {
            "contentid": "one",
            "title": "작은 미술관",
            "addr1": "서울특별시 종로구 세종로",
            "firstimage": "",
        }
    ]

    result = build_recommendations([("문화시설", items)])

    assert result[0]["contentIds"] == ["one"]
