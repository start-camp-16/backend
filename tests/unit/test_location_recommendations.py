import json
from pathlib import Path

import pytest

from app.locations.recommendations import (
    RecommendationValidationError,
    load_recommendations,
)


def write_payload(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "recommendations.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def recommendation(content_ids: list[str], **overrides: object) -> dict[str, object]:
    item: dict[str, object] = {
        "district": "강남구",
        "category": "관광지",
        "contentIds": content_ids,
    }
    item.update(overrides)
    return item


def test_load_recommendations_indexes_content_ids(tmp_path: Path):
    path = write_payload(
        tmp_path,
        {"recommendations": [recommendation(["a", "b"])]},
    )

    assert load_recommendations(path) == {("강남구", "관광지"): ("a", "b")}


@pytest.mark.parametrize(
    ("items", "message"),
    [
        ([recommendation(["a"]), recommendation(["b"])], "duplicate combination"),
        ([recommendation(["a", "a"])], "duplicate contentIds"),
        ([recommendation(["1", "2", "3", "4", "5", "6"])], "between 1 and 5"),
        ([recommendation(["a"], category="음식점")], "unsupported category"),
    ],
)
def test_load_recommendations_rejects_invalid_entries(
    tmp_path: Path,
    items: list[dict[str, object]],
    message: str,
):
    path = write_payload(tmp_path, {"recommendations": items})

    with pytest.raises(RecommendationValidationError, match=message):
        load_recommendations(path)


def test_load_recommendations_rejects_invalid_root(tmp_path: Path):
    path = write_payload(tmp_path, [])

    with pytest.raises(RecommendationValidationError, match="root"):
        load_recommendations(path)
