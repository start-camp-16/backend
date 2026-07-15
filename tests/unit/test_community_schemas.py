import pytest
from pydantic import ValidationError

from app.community.classifications import POST_DISTRICTS, POST_PREFIXES
from app.community.schemas import PostCreate


def test_post_create_trims_text_and_accepts_classifications():
    payload = PostCreate(
        district="강남구",
        prefix="자유",
        title="  제목  ",
        content="  본문  ",
        password="1234",
    )

    assert payload.district.value == "강남구"
    assert payload.prefix.value == "자유"
    assert payload.title == "제목"
    assert payload.content == "본문"


def test_classification_sets_are_complete():
    assert len(POST_DISTRICTS) == 25
    assert "기타" not in POST_DISTRICTS
    assert POST_PREFIXES == ("관광", "맛집", "문화", "행사", "숙박", "쇼핑", "자유")


@pytest.mark.parametrize(
    ("field", "value"),
    [("district", "기타"), ("district", "부산진구"), ("prefix", "공지")],
)
def test_post_create_rejects_unknown_classifications(field: str, value: str):
    values = {
        "district": "강남구",
        "prefix": "자유",
        "title": "제목",
        "content": "본문",
        "password": "1234",
    }
    values[field] = value

    with pytest.raises(ValidationError):
        PostCreate(**values)


def test_post_create_rejects_old_tag_field():
    with pytest.raises(ValidationError):
        PostCreate(
            district="강남구",
            prefix="자유",
            tag="자유",
            title="제목",
            content="본문",
            password="1234",
        )
