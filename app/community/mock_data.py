import random
from dataclasses import dataclass
from typing import Literal

from app.community.classifications import POST_DISTRICTS, POST_PREFIXES

MOCK_PASSWORD = "mock1234"
MOCK_RANDOM_SEED = 20250715

PostKind = Literal["shared", "specific"]


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
    kind: PostKind = "specific"


SHARED_POST_TEMPLATES = (
    (
        "{district}에서 가볍게 걷기 좋은 곳을 공유해요",
        "{district}에서 대중교통으로 가기 편하고 천천히 걷기 좋은 장소를 찾고 있어요. "
        "붐비는 시간대와 쉬어 갈 수 있는 지점을 함께 알려 주시면 좋겠습니다.",
    ),
    (
        "{district}에서 혼자 식사하기 좋은 곳이 궁금해요",
        "{district}에서 혼자 방문해도 부담 없고 식사 시간이 오래 걸리지 않는 곳을 "
        "찾고 있습니다. 대표 메뉴와 비교적 여유로운 방문 시간도 공유해 주세요.",
    ),
    (
        "{district} 주말 나들이 정보를 모아봐요",
        "이번 주말에 {district} 안에서 즐길 수 있는 전시, 행사, 시장 정보를 찾고 있어요. "
        "예약 여부와 대중교통 이용 팁이 있다면 함께 남겨 주세요.",
    ),
)

DISTRICT_FEATURE_NAMES: dict[str, tuple[str, str]] = {
    "강남구": ("코엑스", "서울 선릉과 정릉 [유네스코 세계유산]"),
    "강동구": ("서울 암사동 유적", "길동생태공원"),
    "강북구": ("북한산국립공원(서울)", "근현대사기념관"),
    "강서구": ("서울식물원", "겸재정선미술관"),
    "관악구": ("관악산", "관악산 낙성대공원"),
    "광진구": ("서울어린이대공원", "뚝섬한강공원"),
    "구로구": ("푸른수목원", "고척 스카이돔"),
    "금천구": ("호암산성", "금천예술공장"),
    "노원구": ("화랑대 철도공원", "서울시립과학관"),
    "도봉구": ("도봉산", "둘리뮤지엄"),
    "동대문구": ("홍릉시험림(홍릉숲)", "서울약령시한의약박물관"),
    "동작구": ("국립서울현충원", "노량진수산물도매시장"),
    "마포구": ("하늘공원", "경의선숲길"),
    "서대문구": ("서대문형무소역사관", "서대문 안산(안산자락길)"),
    "서초구": ("반포한강공원", "예술의전당"),
    "성동구": ("서울숲", "성수동 카페거리"),
    "성북구": ("길상사(서울)", "성북동고택북촌산책길"),
    "송파구": ("석촌호수", "롯데월드 어드벤처"),
    "양천구": ("서서울호수공원", "목동종합운동장"),
    "영등포구": ("여의도한강공원", "문래창작촌"),
    "용산구": ("국립중앙박물관", "용산가족공원"),
    "은평구": ("진관사", "은평한옥마을"),
    "종로구": ("경복궁", "북촌한옥마을"),
    "중구": ("남산서울타워", "덕수궁"),
    "중랑구": ("용마산", "중랑장미공원"),
}

COMMENT_TEMPLATES = (
    "{district} 정보 찾고 있었는데 공유해 주셔서 감사합니다.",
    "방문 전에 운영 시간과 휴무일도 확인해 보면 좋을 것 같아요.",
    "대중교통으로 다녀온 후기도 궁금합니다.",
    "주말에는 사람이 많을 수 있으니 오전 방문도 괜찮겠네요.",
    "저도 다음 나들이 때 참고해 볼게요.",
    "근처에서 함께 들를 만한 곳도 있으면 추천해 주세요.",
    "사진 찍기 좋은 시간대가 언제인지 궁금해요.",
    "아이와 함께 가도 괜찮은지 아시는 분 계실까요?",
)


def build_community_mock_posts() -> tuple[MockPostSeed, ...]:
    if set(DISTRICT_FEATURE_NAMES) != set(POST_DISTRICTS):
        raise ValueError("District feature data must cover every supported district")

    randomizer = random.Random(MOCK_RANDOM_SEED)
    seeds: list[MockPostSeed] = []
    for district_index, district in enumerate(POST_DISTRICTS):
        post_data: list[tuple[PostKind, str, str]] = [
            (
                "shared",
                title.format(district=district),
                content.format(district=district),
            )
            for title, content in SHARED_POST_TEMPLATES
        ]
        post_data.extend(
            (
                "specific",
                f"{feature_name} 다녀오신 분 계신가요?",
                f"{district}의 {feature_name}에 방문해 보려고 합니다. "
                "추천 동선과 여유롭게 둘러보기 좋은 시간대, 주변에서 함께 들를 만한 "
                "장소가 있다면 알려 주세요.",
            )
            for feature_name in DISTRICT_FEATURE_NAMES[district]
        )

        for post_index, (kind, title, content) in enumerate(post_data):
            prefix_index = (district_index * len(post_data) + post_index) % len(POST_PREFIXES)
            prefix = POST_PREFIXES[prefix_index]
            comment_count = randomizer.randint(0, 3)
            comment_texts = randomizer.sample(COMMENT_TEMPLATES, k=comment_count)
            comments = tuple(
                MockCommentSeed(content=text.format(district=district)) for text in comment_texts
            )
            seeds.append(
                MockPostSeed(
                    district=district,
                    prefix=prefix,
                    title=title,
                    content=content,
                    comments=comments,
                    kind=kind,
                )
            )
    return tuple(seeds)


COMMUNITY_MOCK_POSTS = build_community_mock_posts()
