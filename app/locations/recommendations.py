import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models import LOCATION_CATEGORIES

RecommendationKey = tuple[str, str]
RecommendationIndex = dict[RecommendationKey, tuple[str, ...]]
DEFAULT_RECOMMENDATIONS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "recommendations.json"
)


class RecommendationValidationError(ValueError):
    pass


def _read_payload(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecommendationValidationError(f"cannot read recommendation file: {path}") from exc


def load_recommendations(path: str | Path) -> RecommendationIndex:
    payload = _read_payload(Path(path))
    if not isinstance(payload, dict):
        raise RecommendationValidationError("recommendation root must be an object")
    entries = payload.get("recommendations")
    if not isinstance(entries, list):
        raise RecommendationValidationError("recommendations must be an array")

    index: RecommendationIndex = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise RecommendationValidationError("recommendation entries must be objects")
        district = entry.get("district")
        category = entry.get("category")
        content_ids = entry.get("contentIds")
        if not isinstance(district, str) or not district:
            raise RecommendationValidationError("district must be a non-empty string")
        if category not in LOCATION_CATEGORIES:
            raise RecommendationValidationError(f"unsupported category: {category}")
        if not isinstance(content_ids, list) or not 1 <= len(content_ids) <= 5:
            raise RecommendationValidationError("contentIds must contain between 1 and 5 IDs")
        if any(not isinstance(content_id, str) or not content_id for content_id in content_ids):
            raise RecommendationValidationError("contentIds must be non-empty strings")
        if len(set(content_ids)) != len(content_ids):
            raise RecommendationValidationError("duplicate contentIds")

        key = (district, category)
        if key in index:
            raise RecommendationValidationError(f"duplicate combination: {district}/{category}")
        index[key] = tuple(content_ids)
    return index


@lru_cache(maxsize=1)
def get_default_recommendations() -> RecommendationIndex:
    return load_recommendations(DEFAULT_RECOMMENDATIONS_PATH)
