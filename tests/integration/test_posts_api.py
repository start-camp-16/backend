import json

from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models import Post


def create_post(
    client: TestClient,
    *,
    district: str = "강남구",
    prefix: str = "자유",
    title: str = "제목",
    content: str = "본문",
    password: str = "1234",
):
    return client.post(
        "/api/posts",
        json={
            "district": district,
            "prefix": prefix,
            "title": title,
            "content": content,
            "password": password,
        },
    )


def create_comment(client: TestClient, post_id: int, content: str = "댓글"):
    return client.post(
        f"/api/posts/{post_id}/comments",
        json={"content": content, "password": "5678"},
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


def test_list_combines_district_prefix_search_and_pagination(client: TestClient):
    create_post(client, district="강남구", prefix="관광", title="한강 산책", content="야경")
    create_post(client, district="강남구", prefix="관광", title="서울숲", content="한강 근처")
    create_post(client, district="마포구", prefix="관광", title="한강 공원", content="산책")
    create_post(client, district="강남구", prefix="문화", title="한강 전시", content="미술")

    response = client.get(
        "/api/posts",
        params={
            "district": "강남구",
            "prefix": "관광",
            "q": "한강",
            "page": 1,
            "size": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["district"] == "강남구"
    assert payload["items"][0]["prefix"] == "관광"
    assert payload["items"][0]["title"] == "서울숲"
    assert "content" not in payload["items"][0]
    assert payload["pagination"] == {
        "page": 1,
        "size": 1,
        "total_items": 2,
        "total_pages": 2,
    }


def test_list_includes_comment_count_for_filtered_search_results(client: TestClient):
    commented = create_post(
        client,
        district="강남구",
        prefix="관광",
        title="댓글 집계 명소",
    ).json()
    uncommented = create_post(
        client,
        district="강남구",
        prefix="관광",
        title="댓글 집계 산책",
    ).json()
    excluded = create_post(
        client,
        district="마포구",
        prefix="관광",
        title="댓글 집계 공원",
    ).json()
    create_comment(client, commented["id"], "첫 댓글")
    create_comment(client, commented["id"], "둘째 댓글")
    create_comment(client, excluded["id"], "제외 댓글")

    response = client.get(
        "/api/posts",
        params={"district": "강남구", "prefix": "관광", "q": "댓글 집계"},
    )

    assert response.status_code == 200
    counts = {item["id"]: item["comment_count"] for item in response.json()["items"]}
    assert counts == {commented["id"]: 2, uncommented["id"]: 0}

    detail = client.get(f"/api/posts/{commented['id']}")
    assert detail.status_code == 200
    assert "comment_count" not in detail.json()


def test_list_without_district_returns_all_districts(client: TestClient):
    create_post(client, district="강남구", title="강남 글")
    create_post(client, district="마포구", title="마포 글")

    response = client.get("/api/posts")

    assert response.status_code == 200
    assert {item["district"] for item in response.json()["items"]} == {"강남구", "마포구"}


def test_create_rejects_old_tag_and_invalid_district(client: TestClient):
    old_contract = client.post(
        "/api/posts",
        json={
            "district": "강남구",
            "prefix": "자유",
            "tag": "자유",
            "title": "제목",
            "content": "본문",
            "password": "1234",
        },
    )
    invalid_district = create_post(client, district="기타")

    assert old_contract.status_code == 400
    assert invalid_district.status_code == 400


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
            "district": "마포구",
            "prefix": "문화",
            "title": "수정 제목",
            "content": "수정 본문",
        },
    )
    updated = client.put(
        f"/api/posts/{post_id}",
        json={
            "password": "1234",
            "district": "마포구",
            "prefix": "문화",
            "title": "수정 제목",
            "content": "수정 본문",
        },
    )

    assert rejected.status_code == 403
    assert rejected.json()["code"] == "PASSWORD_MISMATCH"
    assert updated.status_code == 200
    assert updated.json()["district"] == "마포구"
    assert updated.json()["prefix"] == "문화"
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
