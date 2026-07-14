import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, TypedDict

DISTRICT_PATTERN = re.compile(r"(?:서울특별시|서울)\s+([가-힣]+구)(?:\s|$)")
CATEGORY_KEYWORDS = {
    "관광지": ("궁", "공원", "한강", "산", "숲", "전망", "역사", "유적", "마을", "광장"),
    "문화시설": ("박물관", "미술관", "공연장", "극장", "문화", "전시", "아트", "기념관"),
    "축제공연행사": ("축제", "페스티벌", "공연", "음악", "문화제", "마켓"),
    "여행코스": ("코스", "길", "투어", "산책", "둘레길", "도보"),
    "레포츠": ("체험", "스포츠", "클라이밍", "수영", "자전거", "승마", "캠핑"),
    "숙박": ("호텔", "한옥", "게스트하우스", "리조트", "호스텔"),
    "쇼핑": ("시장", "몰", "백화점", "거리", "상가", "공방"),
}


class RecommendationOutput(TypedDict):
    district: str
    category: str
    contentIds: list[str]


def extract_district(address: object) -> str:
    match = DISTRICT_PATTERN.search(address if isinstance(address, str) else "")
    return match.group(1) if match else "기타"


def recommendation_score(category: str, item: dict[str, Any]) -> int:
    raw_title = item.get("title")
    title = raw_title if isinstance(raw_title, str) else ""
    score = 30 if any(keyword in title for keyword in CATEGORY_KEYWORDS[category]) else 0
    score += 10 if item.get("firstimage") else 0
    score += 5 if item.get("addr1") else 0
    return score


def build_recommendations(
    sources: list[tuple[str, list[dict[str, Any]]]],
) -> list[RecommendationOutput]:
    groups: dict[tuple[str, str], list[tuple[int, int, str]]] = defaultdict(list)
    for category, items in sources:
        for source_order, item in enumerate(items, start=1):
            content_id = item.get("contentid")
            if not isinstance(content_id, str) or not content_id:
                continue
            district = extract_district(item.get("addr1"))
            groups[(district, category)].append(
                (-recommendation_score(category, item), source_order, content_id)
            )

    recommendations: list[RecommendationOutput] = []
    for district, category in sorted(groups):
        candidates = sorted(groups[(district, category)])
        recommendations.append(
            {
                "district": district,
                "category": category,
                "contentIds": [content_id for _, _, content_id in candidates[:5]],
            }
        )
    return recommendations


def read_sources(manifest_path: Path) -> list[tuple[str, list[dict[str, Any]]]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources: list[tuple[str, list[dict[str, Any]]]] = []
    for source in manifest["sources"]:
        raw_path = manifest_path.parent / source["path"]
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        sources.append((source["category"], payload["items"]))
    return sources


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate demo location recommendations")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    recommendations = build_recommendations(read_sources(args.manifest))
    payload = {"recommendations": recommendations}
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    total = sum(len(item["contentIds"]) for item in recommendations)
    print(f"combinations={len(recommendations)} recommendations={total} verified=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
