import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Comment


def create_post(client: TestClient, password: str = "1234") -> int:
    response = client.post(
        "/api/posts",
        json={
            "district": "강남구",
            "prefix": "자유",
            "title": "제목",
            "content": "본문",
            "password": password,
        },
    )
    return response.json()["id"]


def create_comment(
    client: TestClient,
    post_id: int,
    *,
    content: str = "댓글",
    password: str = "5678",
):
    return client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": content, "password": password},
    )


def test_create_and_list_comments_oldest_first_without_password(client: TestClient):
    post_id = create_post(client)
    first = create_comment(client, post_id, content=" 첫 댓글 ")
    second = create_comment(client, post_id, content="둘째 댓글")

    response = client.get(f"/api/posts/{post_id}/comments")

    assert first.status_code == 201
    assert first.json()["content"] == "첫 댓글"
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [
        first.json()["id"],
        second.json()["id"],
    ]
    assert "password" not in json.dumps(response.json())


def test_missing_parent_rejects_comment_list_and_create(client: TestClient):
    listed = client.get("/api/posts/999/comments")
    created = create_comment(client, 999)

    assert listed.status_code == 404
    assert created.status_code == 404
    assert listed.json()["code"] == "POST_NOT_FOUND"
    assert created.json()["code"] == "POST_NOT_FOUND"


def test_update_comment_requires_matching_password(client: TestClient):
    post_id = create_post(client)
    comment_id = create_comment(client, post_id).json()["id"]

    rejected = client.put(
        f"/api/comments/{comment_id}",
        json={"content": "수정 댓글", "password": "9999"},
    )
    updated = client.put(
        f"/api/comments/{comment_id}",
        json={"content": " 수정 댓글 ", "password": "5678"},
    )

    assert rejected.status_code == 403
    assert rejected.json()["code"] == "PASSWORD_MISMATCH"
    assert updated.status_code == 200
    assert updated.json()["content"] == "수정 댓글"


def test_delete_comment_requires_matching_password(client: TestClient):
    post_id = create_post(client)
    comment_id = create_comment(client, post_id).json()["id"]

    rejected = client.request(
        "DELETE",
        f"/api/comments/{comment_id}",
        json={"password": "9999"},
    )
    deleted = client.request(
        "DELETE",
        f"/api/comments/{comment_id}",
        json={"password": "5678"},
    )

    assert rejected.status_code == 403
    assert deleted.status_code == 204
    assert deleted.content == b""


def test_missing_comment_uses_contract_error(client: TestClient):
    response = client.put(
        "/api/comments/999",
        json={"content": "댓글", "password": "5678"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "COMMENT_NOT_FOUND"


def test_deleting_post_cascades_comments(
    client: TestClient,
    db_session: Session,
):
    post_id = create_post(client)
    created = create_comment(client, post_id)

    assert created.status_code == 201

    response = client.request(
        "DELETE",
        f"/api/posts/{post_id}",
        json={"password": "1234"},
    )

    assert response.status_code == 204
    assert db_session.scalar(select(func.count(Comment.id))) == 0


def test_comment_ids_must_be_positive(client: TestClient):
    response = client.put(
        "/api/comments/0",
        json={"content": "댓글", "password": "5678"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
