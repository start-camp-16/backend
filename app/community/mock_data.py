from dataclasses import dataclass

from app.community.classifications import POST_PREFIXES

MOCK_PASSWORD = "mock1234"


@dataclass(frozen=True)
class MockCommentSeed:
    content: str


@dataclass(frozen=True)
class MockPostSeed:
    district: str
    prefix: str
    title: str
    content: str
    comments: tuple[MockCommentSeed, ...] = ()


GANGNAM_THEME_SUBJECTS: dict[str, tuple[str, ...]] = {
    "관광": ("코엑스 아쿠아리움", "봉은사", "도산공원", "선정릉", "양재천 산책로"),
    "맛집": ("코엑스 점심", "압구정 브런치", "신사동 카페", "선릉 혼밥", "청담 저녁"),
    "문화": (
        "별마당도서관",
        "코엑스 오디토리움",
        "K현대미술관",
        "플랫폼엘",
        "마이아트뮤지엄",
    ),
    "행사": (
        "코엑스 전시",
        "무역센터 미디어",
        "강남페스티벌",
        "도산공원 플리마켓",
        "양재천 축제",
    ),
    "숙박": (
        "그랜드 인터컨티넨탈",
        "파크 하얏트",
        "L7 강남",
        "신라스테이 삼성",
        "호텔 안테룸",
    ),
    "쇼핑": (
        "스타필드 코엑스몰",
        "파르나스몰",
        "현대백화점 무역센터점",
        "가로수길",
        "압구정 로데오",
    ),
    "자유": (
        "코엑스 하루 동선",
        "강남 비 오는 날",
        "삼성역 약속",
        "강남 사진 명소",
        "주말 강남 나들이",
    ),
}

PREFIX_COPY: dict[str, tuple[str, str]] = {
    "관광": (
        "{subject} 방문 팁 부탁드려요",
        "강남구 {subject}에 방문하려고 합니다. "
        "붐비지 않는 시간과 주변 동선을 알려 주세요.",
    ),
    "맛집": (
        "{subject} 추천을 모아봐요",
        "강남구에서 {subject} 장소를 찾고 있어요. "
        "대표 메뉴와 대기 적은 시간을 추천해 주세요.",
    ),
    "문화": (
        "{subject} 관람 후기 궁금해요",
        "강남구 {subject}을 여유롭게 즐기는 방법과 "
        "관람 전 확인할 점을 공유해 주세요.",
    ),
    "행사": (
        "{subject} 다녀오신 분 계신가요?",
        "강남구 {subject} 일정과 예약 여부, "
        "현장에서 유용했던 팁을 알고 싶어요.",
    ),
    "숙박": (
        "{subject} 숙박 후기 부탁드려요",
        "강남구 {subject}의 객실과 교통 편의성, "
        "주변에서 함께 들를 곳이 궁금합니다.",
    ),
    "쇼핑": (
        "{subject} 쇼핑 동선 추천해 주세요",
        "강남구 {subject}에서 효율적으로 둘러볼 매장과 "
        "덜 붐비는 시간을 알려 주세요.",
    ),
    "자유": (
        "{subject} 아이디어를 나눠요",
        "강남구에서 {subject}을 계획 중입니다. "
        "실제로 다녀온 동선과 팁을 자유롭게 공유해 주세요.",
    ),
}

PREFIX_COMMENT_COPY: dict[str, tuple[str, ...]] = {
    "관광": (
        "오전 시간대가 비교적 여유로워서 천천히 둘러보기 좋았어요.",
        "지하철역에서 가까워 대중교통으로 방문하기 편했습니다.",
        "야외 장소라면 날씨와 휴관 안내를 미리 확인해 보세요.",
        "근처 명소까지 묶으면 알찬 반나절 관광 코스가 됩니다.",
    ),
    "맛집": (
        "평일 점심은 11시 30분 전에 가면 대기가 비교적 짧았어요.",
        "대표 메뉴와 계절 메뉴를 하나씩 주문해 나눠 먹기 좋았습니다.",
        "주말에는 예약 가능한지 먼저 확인하는 것을 추천해요.",
        "식사 후 근처 카페까지 걸어서 이동하기 좋은 동선입니다.",
    ),
    "문화": (
        "관람 시작 시간을 확인하고 여유 있게 도착하는 게 좋았어요.",
        "전시 해설이나 프로그램을 함께 신청하면 더 알차게 볼 수 있어요.",
        "사진 촬영 가능 구역은 현장 안내를 먼저 확인해 주세요.",
        "관람 뒤 별마당도서관까지 이어서 둘러보기 좋았습니다.",
    ),
    "행사": (
        "사전 예약 회차가 빨리 마감돼서 미리 신청하는 편이 좋아요.",
        "현장 등록 줄이 길 수 있으니 시작보다 일찍 도착해 보세요.",
        "행사장 배치도와 입장 게이트를 미리 확인하면 편합니다.",
        "종료 시간에는 주변 교통이 붐벼 지하철 이용을 추천해요.",
    ),
    "숙박": (
        "삼성역과 가까워 코엑스 일정이 있을 때 이동하기 편했어요.",
        "체크인 시간과 짐 보관 가능 여부를 미리 확인해 보세요.",
        "고층 객실을 원한다면 예약할 때 요청사항에 남기는 게 좋아요.",
        "조식 후 코엑스몰로 바로 이동하는 동선이 편리했습니다.",
    ),
    "쇼핑": (
        "매장 오픈 직후에 가면 인기 매장도 비교적 여유로웠어요.",
        "층별 안내를 먼저 보고 동선을 정하면 시간을 아낄 수 있습니다.",
        "주말에는 주차가 붐벼 지하철로 방문하는 편이 편해요.",
        "쇼핑 후 파르나스몰 식당가까지 이어서 들르기 좋았습니다.",
    ),
    "자유": (
        "비 오는 날에도 실내 이동이 많은 코엑스 쪽이 편했어요.",
        "약속 장소는 출구 번호까지 정해 두면 만나기 수월합니다.",
        "사진을 찍으려면 사람이 적은 오전 시간을 추천해요.",
        "하루에 너무 많이 잡기보다 세 곳 정도가 여유로웠습니다.",
    ),
}


def build_community_mock_posts() -> tuple[MockPostSeed, ...]:
    if set(GANGNAM_THEME_SUBJECTS) != set(POST_PREFIXES) or set(PREFIX_COMMENT_COPY) != set(
        POST_PREFIXES
    ):
        raise ValueError("Gangnam theme data must cover every supported prefix")

    seeds: list[MockPostSeed] = []
    for prefix in POST_PREFIXES:
        title_template, content_template = PREFIX_COPY[prefix]
        for subject_index, subject in enumerate(GANGNAM_THEME_SUBJECTS[prefix]):
            comment_count = 3 + (subject_index % 2)
            seeds.append(
                MockPostSeed(
                    district="강남구",
                    prefix=prefix,
                    title=title_template.format(subject=subject),
                    content=content_template.format(subject=subject),
                    comments=tuple(
                        MockCommentSeed(content=content)
                        for content in PREFIX_COMMENT_COPY[prefix][:comment_count]
                    ),
                )
            )
    return tuple(seeds)


COMMUNITY_MOCK_POSTS = build_community_mock_posts()
