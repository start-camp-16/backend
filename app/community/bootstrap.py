import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Comment, Post

logger = logging.getLogger(__name__)

MOCK_PASSWORD = "mock1234"
MOCK_DATA_STARTED_AT = datetime(2025, 1, 1, 3, tzinfo=UTC)


@dataclass(frozen=True)
class MockCommentSeed:
    content: str


@dataclass(frozen=True)
class MockPostSeed:
    tag: str
    title: str
    content: str
    comments: tuple[MockCommentSeed, ...] = ()


def comment(content: str) -> MockCommentSeed:
    return MockCommentSeed(content=content)


COMMUNITY_MOCK_POSTS = (
    MockPostSeed(
        tag="관광",
        title="한강 노을 보기 좋은 산책 코스 추천해요",
        content=(
            "여의나루역에서 물빛광장 쪽으로 천천히 걸었는데 해 질 무렵 풍경이 정말 "
            "좋았어요. 돗자리 없이 가볍게 걷는다면 마포대교 방향으로 이어지는 길도 "
            "편합니다. 바람이 강할 수 있으니 얇은 겉옷은 챙겨 가세요."
        ),
        comments=(
            comment("저녁 6시쯤 가도 많이 붐비나요?"),
            comment("평일에는 비교적 여유로웠고 주말은 자전거가 많았어요."),
        ),
    ),
    MockPostSeed(
        tag="맛집",
        title="을지로에서 혼밥하기 편했던 칼국수집",
        content=(
            "을지로3가 골목에서 점심을 먹었는데 회전이 빠르고 혼자 온 손님도 많아서 "
            "부담이 없었어요. 멸치 향이 진한 국물에 면이 부드러운 편이고, 매운 양념은 "
            "조금씩 넣는 게 좋았습니다. 열두 시 전 방문을 추천해요."
        ),
        comments=(
            comment("근처 직장인 점심으로 괜찮겠네요."),
            comment("김치가 칼국수랑 잘 어울리는지도 궁금해요."),
            comment("김치는 익지 않은 스타일이라 국물이랑 잘 맞았어요."),
        ),
    ),
    MockPostSeed(
        tag="문화",
        title="비 오는 날 다녀온 서울공예박물관",
        content=(
            "안국역에서 가깝고 실내 전시가 잘 이어져 있어 비 오는 날 방문하기 "
            "좋았습니다. 전통 공예뿐 아니라 제작 과정과 재료를 보여 주는 전시가 많아 "
            "천천히 보면 두 시간 정도 걸려요. 관람 뒤 정독도서관 쪽 산책도 좋습니다."
        ),
        comments=(comment("아이와 함께 보기에도 어렵지 않을까요?"),),
    ),
    MockPostSeed(
        tag="자유",
        title="서울 여행할 때 대중교통만으로 충분할까요?",
        content=(
            "2박 3일 동안 경복궁, 성수, 잠실을 둘러볼 예정입니다. 렌터카 없이 지하철과 "
            "버스만 이용하려고 하는데 짐이 많지 않다면 괜찮을까요? 출퇴근 시간에 피하면 "
            "좋은 구간도 알려 주시면 감사하겠습니다."
        ),
        comments=(
            comment("세 지역 모두 지하철 접근이 좋아서 대중교통이면 충분해요."),
            comment("평일 8시 전후와 6시 전후만 피하면 이동이 한결 편합니다."),
        ),
    ),
    MockPostSeed(
        tag="행사",
        title="주말 광화문 책마당 방문 후기",
        content=(
            "야외 의자와 읽을 책이 준비되어 있어 잠깐 쉬어 가기 좋았어요. 시간대별 "
            "프로그램은 현장에서 바뀔 수 있으니 방문 전에 공식 일정을 확인하는 편이 "
            "안전합니다. 햇볕이 강한 시간에는 모자와 물을 챙기세요."
        ),
    ),
    MockPostSeed(
        tag="숙박",
        title="서울역 근처 숙소 고를 때 확인할 점",
        content=(
            "기차를 일찍 타야 해서 서울역 근처에서 묵었는데 지도상 거리보다 역 출구와 "
            "숙소 사이의 경사를 확인하는 게 중요했어요. 큰 짐이 있다면 엘리베이터가 있는 "
            "출구와 체크인 가능 시간을 먼저 문의해 보세요."
        ),
        comments=(comment("공항철도 이용 예정이라 출구 정보가 특히 유용하네요."),),
    ),
    MockPostSeed(
        tag="쇼핑",
        title="망원시장에서 선물용 간식 골라봤어요",
        content=(
            "바로 먹는 음식도 많지만 포장하기 좋은 약과와 한과를 파는 곳도 있었어요. "
            "오후에는 통로가 붐벼서 장을 여유롭게 보려면 오전 방문이 낫습니다. 시장 안은 "
            "카드 결제가 대부분 가능했지만 소액 현금도 조금 준비했어요."
        ),
        comments=(
            comment("상온에서 하루 정도 보관할 간식도 많았나요?"),
            comment("포장 날짜를 확인할 수 있는 제품이 있어서 선물하기 괜찮았어요."),
        ),
    ),
    MockPostSeed(
        tag="관광",
        title="북촌은 이른 아침에 걸어보세요",
        content=(
            "주민이 생활하는 동네라 조용히 둘러보려고 오전 일찍 방문했습니다. 계동길에서 "
            "가회동 방향으로 걷는 코스가 완만했고 골목 안내 표지판도 잘 보였어요. 사진을 "
            "찍을 때는 주택 출입구를 막지 않도록 주의하면 좋겠습니다."
        ),
        comments=(comment("조용한 관람 예절까지 알려 주셔서 좋아요."),),
    ),
    MockPostSeed(
        tag="맛집",
        title="성수에서 찾은 담백한 브런치 메뉴",
        content=(
            "유명한 카페 대기 줄을 피해 골목 안 작은 가게에 들어갔는데 채소가 넉넉한 "
            "샌드위치와 수프가 괜찮았어요. 주말에는 재료가 일찍 소진될 수 있고 좌석 간격이 "
            "좁아 두세 명이 방문하기에 적당해 보였습니다."
        ),
    ),
    MockPostSeed(
        tag="문화",
        title="국립중앙박물관 반나절 관람 동선",
        content=(
            "전시실이 넓어서 모두 보려 하기보다 관심 있는 상설관 두 곳을 먼저 정하는 게 "
            "좋았습니다. 오전에는 사유의 방을 보고 점심 뒤 서화관을 둘러봤어요. 중간중간 "
            "쉴 공간이 많지만 편한 신발은 꼭 필요합니다."
        ),
        comments=(
            comment("무료 상설전시만 봐도 반나절이 금방 지나가더라고요."),
            comment("어르신과 함께 가는데 휴식 공간이 많다니 다행이에요."),
            comment("물품 보관함을 먼저 이용하면 관람이 훨씬 편해요."),
        ),
    ),
    MockPostSeed(
        tag="관광",
        title="낙산공원 야경 산책 시 알아둘 점",
        content=(
            "혜화역에서 성곽길을 따라 올라가니 경사가 있지만 중간 전망이 좋았어요. 해가 "
            "진 뒤에는 일부 구간이 어두워 밝은 길로 다니는 편이 안전합니다. 내려올 때는 "
            "동대문 방향 코스를 이용하면 지하철역까지 자연스럽게 이어집니다."
        ),
        comments=(
            comment("운동화 신고 천천히 올라가면 초보도 괜찮을까요?"),
            comment("쉬는 구간을 포함해 한 시간 정도 잡으면 무리 없었어요."),
        ),
    ),
    MockPostSeed(
        tag="맛집",
        title="광장시장에서는 메뉴를 나눠 먹는 게 좋았어요",
        content=(
            "빈대떡과 육회, 잔치국수까지 한 번에 먹고 싶어서 일행과 메뉴를 하나씩 나눠 "
            "주문했습니다. 가게마다 영업시간과 휴무가 달라 특정 메뉴가 목적이라면 미리 "
            "확인하세요. 사람이 많은 곳에서는 소지품도 잘 챙겨야 합니다."
        ),
        comments=(comment("여럿이 가서 조금씩 맛보는 방법 좋네요."),),
    ),
    MockPostSeed(
        tag="행사",
        title="여의도 봄꽃 구경은 평일 오전이 편해요",
        content=(
            "개화 시기 주말에는 이동이 어려울 정도로 붐벼 평일 오전에 다녀왔습니다. "
            "국회의사당역에서 시작해 한강 쪽으로 빠지는 동선이 편했어요. 교통 통제와 "
            "개방 구간은 해마다 달라질 수 있으니 당일 공지를 확인하세요."
        ),
        comments=(
            comment("유모차로 이동 가능한 구간인지 궁금했는데 동선 참고할게요."),
            comment("오전에도 햇빛이 강해서 양산이 유용했어요."),
        ),
    ),
    MockPostSeed(
        tag="숙박",
        title="홍대입구 숙소에서 공항 이동한 후기",
        content=(
            "귀국 비행기가 오전이라 공항철도 접근성을 보고 숙소를 골랐습니다. 역과 가깝더라도 "
            "출입구에서 승강장까지 시간이 꽤 걸릴 수 있어 여유 있게 나오는 게 좋아요. "
            "새벽 체크아웃 방식과 짐 보관 가능 여부도 미리 확인했습니다."
        ),
    ),
    MockPostSeed(
        tag="쇼핑",
        title="인사동에서 부담 없는 기념품 찾기",
        content=(
            "전통 문양 책갈피와 작은 보자기처럼 부피가 크지 않은 물건을 중심으로 "
            "둘러봤어요. 큰길뿐 아니라 쌈지길 안쪽에도 가격대가 다양한 가게가 있습니다. "
            "도자기는 포장 상태와 기내 반입 가능 여부를 꼭 확인하세요."
        ),
        comments=(
            comment("책갈피는 여러 명에게 선물하기 좋겠어요."),
            comment("한글 디자인 엽서도 종류가 많아서 추천합니다."),
        ),
    ),
    MockPostSeed(
        tag="자유",
        title="서울에서 하루 만 보 걷기 좋은 동네는 어디일까요?",
        content=(
            "복잡한 관광지보다 동네 분위기를 느끼며 오래 걷고 싶습니다. 연남동과 서촌 중 "
            "한 곳을 생각하고 있는데 중간에 쉬기 좋은 공원이나 서점이 있는 코스를 "
            "추천해 주세요. 평일 오후에 방문할 예정입니다."
        ),
        comments=(
            comment("연남동은 경의선숲길을 따라 걸으면 쉬어 갈 곳이 많아요."),
            comment("서촌은 골목과 전시 공간을 함께 보기 좋아서 천천히 걷기 좋습니다."),
            comment("걷는 거리만 보면 연남동, 골목 구경은 서촌을 추천해요."),
        ),
    ),
    MockPostSeed(
        tag="문화",
        title="정동길에서 작은 전시 공간 둘러보기",
        content=(
            "덕수궁 관람 뒤 정동길을 걸으며 전시 공간 두 곳을 들렀습니다. 건물 사이 거리가 "
            "가까워 짧은 오후 일정으로 묶기 좋았어요. 전시 교체 기간에는 휴관할 수 있으니 "
            "각 공간의 운영 시간을 확인하고 가는 것을 권합니다."
        ),
        comments=(comment("덕수궁 돌담길과 함께 묶어서 가봐야겠어요."),),
    ),
    MockPostSeed(
        tag="관광",
        title="서울숲에서 조용히 쉬기 좋은 구역",
        content=(
            "메인 잔디밭은 활기차지만 조금 안쪽 산책로로 들어가면 벤치가 많고 비교적 "
            "조용했습니다. 곤충식물원 주변을 걷고 성수동 방향으로 이동하는 코스도 편해요. "
            "주말에는 자전거와 반려견이 많아 서로 길을 양보하면 좋겠습니다."
        ),
        comments=(
            comment("돗자리 없이 벤치에서 쉬기에도 괜찮았어요."),
            comment("가을 은행나무가 예쁠 때 다시 가고 싶네요."),
        ),
    ),
    MockPostSeed(
        tag="맛집",
        title="서촌에서 늦은 점심 먹을 때 참고하세요",
        content=(
            "오후 세 시쯤 방문하니 브레이크타임인 식당이 많았습니다. 늦은 점심이라면 "
            "통인시장 운영 여부나 브레이크타임 없는 가게를 미리 확인하는 게 좋아요. 저는 "
            "간단한 국수와 만두를 먹고 근처 카페로 이동했습니다."
        ),
        comments=(comment("브레이크타임을 놓치기 쉬운데 좋은 정보네요."),),
    ),
    MockPostSeed(
        tag="자유",
        title="여름 서울 여행 준비물 공유해요",
        content=(
            "실내외 온도 차가 커서 얇은 겉옷이 가장 유용했고, 갑작스러운 소나기에 대비해 "
            "작은 우산도 챙겼습니다. 물을 자주 마시고 한낮에는 박물관이나 전시처럼 실내 "
            "일정을 넣으니 덜 지쳤어요. 편한 신발도 꼭 추천합니다."
        ),
    ),
)


def ensure_community_mock_data(
    session_factory: sessionmaker[Session],
    seeds: Sequence[MockPostSeed] = COMMUNITY_MOCK_POSTS,
) -> int | None:
    with session_factory.begin() as session:
        if session.scalar(select(Post.id).limit(1)) is not None:
            logger.info("Community mock bootstrap skipped because a post already exists")
            return None

        for post_index, seed in enumerate(seeds):
            post_created_at = MOCK_DATA_STARTED_AT + timedelta(days=post_index)
            post = Post(
                tag=seed.tag,
                title=seed.title,
                content=seed.content,
                password=MOCK_PASSWORD,
                created_at=post_created_at,
                updated_at=post_created_at,
            )
            post.comments = [
                Comment(
                    content=comment_seed.content,
                    password=MOCK_PASSWORD,
                    created_at=post_created_at + timedelta(minutes=comment_index + 1),
                    updated_at=post_created_at + timedelta(minutes=comment_index + 1),
                )
                for comment_index, comment_seed in enumerate(seed.comments)
            ]
            session.add(post)

    inserted = len(seeds)
    logger.info("Community mock bootstrap completed", extra={"inserted": inserted})
    return inserted
