GANGNAM_DEMO_DISTRICT = "강남구"
GANGNAM_DEMO_CATEGORIES = frozenset(("쇼핑", "문화시설", "숙박"))
GANGNAM_DEMO_STOP_COUNT = 5
GANGNAM_DEMO_CONTENT_IDS = (
    "3076105",  # 코엑스 오디토리움
    "2507822",  # 별마당도서관
    "1984944",  # 스타필드 코엑스몰
    "1985821",  # 파르나스몰
    "142769",  # 그랜드 인터컨티넨탈 서울 파르나스
)


def match_demo_course(
    district: str,
    categories: list[str],
    stop_count: int,
) -> tuple[str, ...] | None:
    if (
        district == GANGNAM_DEMO_DISTRICT
        and frozenset(categories) == GANGNAM_DEMO_CATEGORIES
        and len(categories) == len(GANGNAM_DEMO_CATEGORIES)
        and stop_count == GANGNAM_DEMO_STOP_COUNT
    ):
        return GANGNAM_DEMO_CONTENT_IDS
    return None
