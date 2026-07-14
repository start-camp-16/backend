import pytest
from pydantic import ValidationError

from app.community.schemas import PostCreate


def test_post_create_trims_title_and_content():
    payload = PostCreate(tag="자유", title="  제목  ", content="  본문  ", password="1234")

    assert payload.title == "제목"
    assert payload.content == "본문"


def test_post_create_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        PostCreate(
            tag="자유",
            title="제목",
            content="본문",
            password="1234",
            admin=True,
        )
