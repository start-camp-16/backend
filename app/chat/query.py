import re
from dataclasses import dataclass

from app.community.classifications import POST_DISTRICTS, POST_PREFIXES

LOCATION_CATEGORIES = (
    "축제공연행사",
    "문화시설",
    "여행코스",
    "관광지",
    "레포츠",
    "쇼핑",
    "숙박",
)
IGNORED_PHRASES = ("알려줘", "알려주세요", "보여줘", "보여주세요")


@dataclass(frozen=True)
class ParsedQuery:
    district: str | None
    location_category: str | None
    post_prefix: str | None
    keywords: tuple[str, ...]


def _extract_first(text: str, candidates: tuple[str, ...]) -> tuple[str | None, str]:
    for candidate in candidates:
        if candidate in text:
            return candidate, text.replace(candidate, " ", 1)
    return None, text


def parse_query(message: str) -> ParsedQuery:
    remainder = message
    district, remainder = _extract_first(remainder, POST_DISTRICTS)
    location_category, remainder = _extract_first(remainder, LOCATION_CATEGORIES)
    post_prefix, remainder = _extract_first(remainder, POST_PREFIXES)
    for phrase in IGNORED_PHRASES:
        remainder = remainder.replace(phrase, " ")
    normalized = re.sub(r"[^0-9A-Za-z가-힣]+", " ", remainder)
    keywords = tuple(token for token in normalized.split() if token)
    return ParsedQuery(
        district=district,
        location_category=location_category,
        post_prefix=post_prefix,
        keywords=keywords,
    )
