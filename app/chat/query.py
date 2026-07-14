import re
from dataclasses import dataclass

SEOUL_DISTRICTS = (
    "강남구",
    "강동구",
    "강북구",
    "강서구",
    "관악구",
    "광진구",
    "구로구",
    "금천구",
    "노원구",
    "도봉구",
    "동대문구",
    "동작구",
    "마포구",
    "서대문구",
    "서초구",
    "성동구",
    "성북구",
    "송파구",
    "양천구",
    "영등포구",
    "용산구",
    "은평구",
    "종로구",
    "중구",
    "중랑구",
)
LOCATION_CATEGORIES = (
    "축제공연행사",
    "문화시설",
    "여행코스",
    "관광지",
    "레포츠",
    "쇼핑",
    "숙박",
)
POST_TAGS = ("관광", "맛집", "문화", "행사", "숙박", "쇼핑", "자유")
IGNORED_PHRASES = ("알려줘", "알려주세요", "보여줘", "보여주세요")


@dataclass(frozen=True)
class ParsedQuery:
    district: str | None
    location_category: str | None
    post_tag: str | None
    keywords: tuple[str, ...]


def _extract_first(text: str, candidates: tuple[str, ...]) -> tuple[str | None, str]:
    for candidate in candidates:
        if candidate in text:
            return candidate, text.replace(candidate, " ", 1)
    return None, text


def parse_query(message: str) -> ParsedQuery:
    remainder = message
    district, remainder = _extract_first(remainder, SEOUL_DISTRICTS)
    location_category, remainder = _extract_first(remainder, LOCATION_CATEGORIES)
    post_tag, remainder = _extract_first(remainder, POST_TAGS)
    for phrase in IGNORED_PHRASES:
        remainder = remainder.replace(phrase, " ")
    normalized = re.sub(r"[^0-9A-Za-z가-힣]+", " ", remainder)
    keywords = tuple(token for token in normalized.split() if token)
    return ParsedQuery(
        district=district,
        location_category=location_category,
        post_tag=post_tag,
        keywords=keywords,
    )
