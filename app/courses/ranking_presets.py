from dataclasses import dataclass


@dataclass(frozen=True)
class CourseRankingPreset:
    rank: int
    district: str
    title: str
    description: str
    content_ids: tuple[str, ...]


COURSE_RANKING_PRESETS = (
    CourseRankingPreset(
        rank=1,
        district="강남구",
        title="코엑스 올인원 데이",
        description="봉은사부터 코엑스 쇼핑과 숙박까지 이어지는 하루 코스",
        content_ids=("126504", "130284", "2507822", "1984944", "142769"),
    ),
    CourseRankingPreset(
        rank=2,
        district="마포구",
        title="홍대 감성 산책",
        description="경의선숲길에서 홍대 거리 문화를 즐기고 숙박으로 마무리하는 코스",
        content_ids=("2553819", "2578284", "3082405", "2907142"),
    ),
    CourseRankingPreset(
        rank=3,
        district="서초구",
        title="반포 한강 나들이",
        description="한강과 세빛섬을 둘러본 뒤 쇼핑과 숙박으로 이어지는 코스",
        content_ids=("970138", "970052", "132492", "143033"),
    ),
    CourseRankingPreset(
        rank=4,
        district="송파구",
        title="잠실 패밀리 데이",
        description="석촌호수와 롯데월드를 즐기고 숙박으로 마무리하는 코스",
        content_ids=("754052", "126498", "2003909", "3464755"),
    ),
    CourseRankingPreset(
        rank=5,
        district="노원구",
        title="노원 과학·예술 산책",
        description="미술과 과학 체험 후 인근 쇼핑으로 마무리하는 가족 코스",
        content_ids=("1866427", "2989541", "2894600"),
    ),
)
