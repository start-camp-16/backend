import json

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Post


def create_post(
    client: TestClient,
    *,
    tag: str = "자유",
    title: str = "제목",
    content: str = "본문",
    password: str = "1234",
):
    return client.post(
        "/api/posts",
        json={"tag": tag, "title": title, "content": content, "password": password},
    )


def test_create_and_get_post_never_expose_password(client: TestClient):
    created = create_post(client, title=" 제목 ", content=" 본문 ")

    assert created.status_code == 201
    assert created.json()["title"] == "제목"
    assert created.json()["content"] == "본문"
    assert "password" not in json.dumps(created.json())

    fetched = client.get(f"/api/posts/{created.json()['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created.json()
    assert "password" not in json.dumps(fetched.json())


def test_list_combines_tag_search_and_pagination(client: TestClient):
    create_post(client, tag="관광", title="한강 산책", content="야경")
    create_post(client, tag="관광", title="서울숲", content="한강 근처")
    create_post(client, tag="문화", title="한강 전시", content="미술")

    response = client.get(
        "/api/posts",
        params={"tag": "관광", "q": "한강", "page": 1, "size": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["title"] == "서울숲"
    assert "content" not in payload["items"][0]
    assert payload["pagination"] == {
        "page": 1,
        "size": 1,
        "total_items": 2,
        "total_pages": 2,
    }


def test_blank_search_is_treated_as_no_filter(client: TestClient):
    create_post(client, title="첫 글")
    create_post(client, title="둘째 글")

    response = client.get("/api/posts", params={"q": "   "})

    assert response.status_code == 200
    assert response.json()["pagination"]["total_items"] == 2


def test_update_requires_matching_password(client: TestClient):
    post_id = create_post(client).json()["id"]

    rejected = client.put(
        f"/api/posts/{post_id}",
        json={
            "password": "9999",
            "tag": "문화",
            "title": "수정 제목",
            "content": "수정 본문",
        },
    )
    updated = client.put(
        f"/api/posts/{post_id}",
        json={
            "password": "1234",
            "tag": "문화",
            "title": "수정 제목",
            "content": "수정 본문",
        },
    )

    assert rejected.status_code == 403
    assert rejected.json()["code"] == "PASSWORD_MISMATCH"
    assert updated.status_code == 200
    assert updated.json()["tag"] == "문화"
    assert updated.json()["title"] == "수정 제목"


def test_delete_requires_matching_password(
    client: TestClient,
    db_session: Session,
):
    post_id = create_post(client).json()["id"]

    rejected = client.request(
        "DELETE",
        f"/api/posts/{post_id}",
        json={"password": "9999"},
    )
    deleted = client.request(
        "DELETE",
        f"/api/posts/{post_id}",
        json={"password": "1234"},
    )

    assert rejected.status_code == 403
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert db_session.scalar(select(Post).where(Post.id == post_id)) is None


def test_missing_post_uses_contract_error(client: TestClient):
    response = client.get("/api/posts/999")

    assert response.status_code == 404
    assert response.json()["code"] == "POST_NOT_FOUND"


def test_post_id_must_be_positive(client: TestClient):
    response = client.get("/api/posts/0")

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
