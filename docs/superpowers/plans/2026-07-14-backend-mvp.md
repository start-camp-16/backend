# 뭐할구 Backend MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 서울 장소 6,518건의 원본 순위 조회, 익명 게시글·댓글, 저장소 근거 기반 챗봇을 제공하는 FastAPI MVP를 구현한다.

**Architecture:** FastAPI 라우터는 요청 검증과 응답 변환만 담당하고, 기능별 서비스가 SQLAlchemy 세션과 외부 챗봇 포트를 사용한다. SQLite는 Alembic으로 관리하며 장소 원천 데이터는 명시적 CLI로만 upsert한다. 챗봇 검색과 OpenAI 호출을 분리해 검색은 실제 DB로, 제공자 오류는 가짜 클라이언트로 결정적으로 테스트한다.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2/pydantic-settings, SQLAlchemy 2.x, Alembic, SQLite, OpenAI Python SDK Responses API, pytest, pytest-cov, HTTPX, Ruff, mypy

## Global Constraints

- 인증·회원·JWT는 구현하지 않는다.
- 장소 순위는 점수가 아니라 카테고리 JSON의 1-based `source_order ASC`다.
- 장소 카테고리는 `관광지, 레포츠, 문화시설, 쇼핑, 숙박, 여행코스, 축제공연행사`만 허용한다.
- 게시글 태그는 `관광, 맛집, 문화, 행사, 숙박, 쇼핑, 자유`만 허용한다.
- 비밀번호는 과제 요구대로 평문 저장하되 API 응답, 오류 응답, 로그에 절대 포함하지 않는다.
- 모든 datetime은 UTC로 저장하고 API에서는 timezone이 포함된 ISO 8601 문자열로 반환한다.
- 페이지는 1 이상, 페이지 크기는 1~100이며 기본값은 각각 1과 20이다.
- 챗봇 대화는 DB에 저장하지 않고 조회된 장소·게시글만 근거로 전달한다.
- 실제 `.env`와 SQLite DB는 커밋하지 않는다. 원천 JSON은 공공누리 제3유형 출처 표기와 변경 금지 조건을 지키며 원본 그대로 보관한다.
- API 경로·상태 코드·스키마는 canonical 계약인 `shared/openapi.yaml`과 일치시킨다.

## 확인된 선행 조건과 결정

1. 현재 계약 파일은 `docs/api.yaml`이지만 PRD는 `shared/openapi.yaml`을 지정한다. 첫 작업에서 파일을 이동하고 이후 계약 테스트는 그 경로만 읽는다.
2. `data/`의 원천 JSON 7개는 실제 합계 6,518건이며 각 파일의 `total`과 `items` 길이가 PRD의 카테고리별 건수와 일치한다. Task 3에서 `data/raw/`로 이동하되 내용은 변경하지 않는다.
3. 실제 JSON 파일명은 한글 Unicode 조합 방식에 영향을 받을 수 있다. 커밋된 `data/manifest.json`에서 카테고리, `contentTypeId`, 경로, 기대 건수를 명시해 파일명 추론을 제거한다.
4. `OPENAI_MODEL`은 환경변수 필수값이 아니라 배포 설정값으로 둔다. `.env.example`에는 비용을 고려한 예시값만 두며 코드가 특정 모델명에 의존하지 않게 한다.
5. 초기 스키마부터 Alembic을 사용한다. 앱 시작 시 `create_all()`이나 자동 데이터 적재를 실행하지 않는다.

## Target File Map

```text
app/
  main.py                 # app factory, middleware, routers
  config.py               # environment settings
  db.py                   # engine/session dependency
  errors.py               # domain errors and handlers
  models.py               # Location, Post, Comment ORM models
  schemas.py              # shared pagination/error schemas
  locations/              # import, meta, ranking queries and schemas
  community/              # post/comment services, schemas and routers
  chat/                   # query parsing, retrieval, provider port and router
  health.py               # database health endpoint
alembic/                   # versioned database migrations
scripts/import_locations.py
shared/openapi.yaml        # canonical API contract
tests/{unit,integration,contract}/
data/manifest.json         # seven source paths and expected counts
```

---

### Task 1: Project Foundation, Configuration, and Error Contract

**Files:**
- Create: `pyproject.toml`, `.python-version`, `.gitignore`, `.env.example`
- Create: `app/__init__.py`, `app/config.py`, `app/db.py`, `app/errors.py`, `app/main.py`, `app/schemas.py`
- Create: `tests/conftest.py`, `tests/unit/test_config.py`, `tests/integration/test_errors.py`
- Move during implementation: `docs/api.yaml` → `shared/openapi.yaml`

**Interfaces:**
- Produces: `Settings`, `get_settings()`, `get_db()`, `create_app()`, `AppError`, `Pagination`, `ErrorResponse`.

- [ ] **Step 1: Add the Python toolchain and dependency groups**

```toml
[project]
name = "mwohalgu-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "alembic>=1.13", "fastapi>=0.115", "openai>=1.0",
  "pydantic-settings>=2.0", "sqlalchemy>=2.0", "uvicorn[standard]>=0.30"
]

[project.optional-dependencies]
dev = ["httpx>=0.27", "mypy>=1.11", "pytest>=8.0", "pytest-cov>=5.0", "ruff>=0.6"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

- [ ] **Step 2: Write failing configuration and validation-error tests**

```python
def test_settings_accept_server_start_without_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert Settings(_env_file=None).openai_api_key is None

def test_fastapi_validation_uses_shared_error_shape(client):
    response = client.get("/api/rankings", params={"page": 0})
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert set(response.json()) == {"code", "message", "details"}
```

- [ ] **Step 3: Run the focused tests and verify they fail**

Run: `python -m pytest tests/unit/test_config.py tests/integration/test_errors.py -v`

Expected: collection fails because `app.config` and `create_app` do not exist.

- [ ] **Step 4: Implement settings, session dependency, app factory, and exception handlers**

```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./mwohalgu.db"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.4-mini"
    chat_location_limit: int = Field(default=5, ge=1, le=20)
    chat_post_limit: int = Field(default=5, ge=1, le=20)
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]
```

Register handlers for `RequestValidationError` → 400 `VALIDATION_ERROR`, known `AppError` instances, and uncaught exceptions → 500 `INTERNAL_ERROR`. Configure CORS only from `cors_origin_list`; do not log request bodies.

For every SQLite connection, register a SQLAlchemy `connect` listener that executes `PRAGMA foreign_keys=ON`; use `check_same_thread=False` for FastAPI's synchronous request workers. Move the contract before staging: `mkdir -p shared && mv docs/api.yaml shared/openapi.yaml`.

- [ ] **Step 5: Verify foundation quality**

Run: `python -m pytest tests/unit/test_config.py tests/integration/test_errors.py -v && ruff check app tests && mypy app`

Expected: all tests pass and both static checks exit 0.

- [ ] **Step 6: Commit the foundation**

```bash
git add pyproject.toml .python-version .gitignore .env.example app tests shared/openapi.yaml
git commit -m "chore: bootstrap FastAPI backend"
```

---

### Task 2: Database Models and Migrations

**Files:**
- Create: `app/models.py`, `alembic.ini`, `alembic/env.py`, `alembic/versions/0001_initial_schema.py`
- Create: `tests/integration/test_models.py`, `tests/integration/test_migrations.py`
- Modify: `tests/conftest.py`

**Interfaces:**
- Consumes: `get_db()` and the SQLAlchemy declarative base from Task 1.
- Produces: `Location`, `Post`, `Comment`; foreign-key-enabled SQLite test sessions.

- [ ] **Step 1: Test constraints, indexes, cascade deletion, and UTC timestamps**

```python
def test_deleting_post_cascades_comments(db_session):
    post = Post(tag="자유", title="제목", content="본문", password="1234")
    post.comments.append(Comment(content="댓글", password="5678"))
    db_session.add(post); db_session.commit(); db_session.delete(post); db_session.commit()
    assert db_session.scalar(select(func.count(Comment.id))) == 0

def test_location_content_id_is_unique(db_session, location_factory):
    db_session.add_all([location_factory(content_id="1"), location_factory(content_id="1")])
    with pytest.raises(IntegrityError):
        db_session.commit()
```

- [ ] **Step 2: Verify the tests fail before models exist**

Run: `python -m pytest tests/integration/test_models.py tests/integration/test_migrations.py -v`

Expected: import failure for `Location`, `Post`, and `Comment`.

- [ ] **Step 3: Implement ORM models and exact indexes**

```python
class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (Index("ix_locations_category_district_order", "category", "district", "source_order"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[str] = mapped_column(String(32), unique=True)
    category: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(300))
    address1: Mapped[str | None]
    address2: Mapped[str | None]
    district: Mapped[str] = mapped_column(String(20), index=True)
    longitude: Mapped[float | None]
    latitude: Mapped[float | None]
    image_url: Mapped[str | None]
    thumbnail_url: Mapped[str | None]
    phone: Mapped[str | None]
    source_order: Mapped[int]
```

`Post` has indexes on `created_at` and `tag`; `Comment` has a composite `(post_id, created_at)` index and `ForeignKey("posts.id", ondelete="CASCADE")`. Use `datetime.now(UTC)` defaults and `onupdate` for both mutable resources.

- [ ] **Step 4: Generate and inspect the initial migration**

Run: `alembic revision --autogenerate -m "initial schema"`

Expected: one revision creating three tables, the unique constraint, required indexes, and the cascade foreign key. Rename the revision file to `0001_initial_schema.py` and replace its generated revision ID consistently.

- [ ] **Step 5: Verify migrations and model behavior**

Run: `alembic upgrade head && python -m pytest tests/integration/test_models.py tests/integration/test_migrations.py -v`

Expected: migration reaches head; all tests pass.

- [ ] **Step 6: Commit the database layer**

```bash
git add app/models.py alembic.ini alembic tests
git commit -m "feat: add initial database schema"
```

---

### Task 3: Deterministic Location Import

**Files:**
- Create: `app/locations/__init__.py`, `app/locations/importer.py`
- Create: `scripts/import_locations.py`, `data/manifest.json`
- Move: `data/*.json` → `data/raw/*.json`
- Preserve: `data/SOURCE.md`, `data/SCHEMA.md`
- Create: `tests/fixtures/locations/*.json`, `tests/unit/test_location_importer.py`, `tests/integration/test_location_import.py`

**Interfaces:**
- Consumes: `Location` and a SQLAlchemy `Session`.
- Produces: `extract_district(address: str | None) -> str`, `parse_float(value: object) -> float | None`, `import_manifest(session, manifest_path) -> ImportReport`.

- [ ] **Step 1: Write parser and idempotent-upsert tests**

```python
@pytest.mark.parametrize(("address", "expected"), [
    ("서울특별시 강남구 테헤란로", "강남구"),
    ("서울 마포구 월드컵로", "마포구"),
    (None, "기타"),
])
def test_extract_district(address, expected):
    assert extract_district(address) == expected

def test_reimport_updates_source_fields_without_duplicates(db_session, manifest_path):
    first = import_manifest(db_session, manifest_path)
    second = import_manifest(db_session, manifest_path)
    assert first.inserted == 2
    assert second.updated == 2
    assert db_session.scalar(select(func.count(Location.id))) == 2
```

- [ ] **Step 2: Run tests to confirm missing importer failures**

Run: `python -m pytest tests/unit/test_location_importer.py tests/integration/test_location_import.py -v`

Expected: import failure for `app.locations.importer`.

- [ ] **Step 3: Implement manifest validation, normalization, upsert, and count verification**

```python
DISTRICT_PATTERN = re.compile(r"(?:서울특별시|서울)\s+([가-힣]+구)(?:\s|$)")

def parse_float(value: object) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

def extract_district(address: str | None) -> str:
    match = DISTRICT_PATTERN.search(address or "")
    return match.group(1) if match else "기타"
```

For each manifest entry, verify `contentType`, `contentTypeId`, `total`, and `len(items)` against the manifest; enumerate `payload["items"]` from 1; map `contentid`, `addr1`, `addr2`, `mapx`, `mapy`, `firstimage`, `firstimage2`, and `tel`; then upsert by `content_id`. Validate unique IDs and expected category/total counts before commit; roll back the full import on mismatch. Logs contain only file, category, inserted, updated, and total counts.

- [ ] **Step 4: Add the explicit CLI**

Run interface: `python scripts/import_locations.py --manifest data/manifest.json --verify-total 6518`

Expected success output: one count line per category followed by `total=6518 verified=true`; expected failure exits non-zero without committing partial data.

- [ ] **Step 5: Run importer tests and lint**

Run: `python -m pytest tests/unit/test_location_importer.py tests/integration/test_location_import.py -v && ruff check app scripts tests`

Expected: all tests pass; lint exits 0.

- [ ] **Step 6: Commit the importer**

```bash
git add app/locations scripts data/manifest.json data/raw data/SOURCE.md data/SCHEMA.md tests/fixtures tests/unit tests/integration
git commit -m "feat: import Seoul location data"
```

---

### Task 4: Metadata and Rankings API

**Files:**
- Create: `app/locations/schemas.py`, `app/locations/service.py`, `app/locations/router.py`
- Create: `tests/integration/test_meta_api.py`, `tests/integration/test_rankings_api.py`
- Modify: `app/main.py`

**Interfaces:**
- Produces: `list_categories()`, `list_districts(session)`, `get_rankings(session, district, category, page, size)` and the `/api/meta/*`, `/api/rankings` routes.

- [ ] **Step 1: Write API tests for ordering, pagination, rank, and validation**

```python
def test_rank_continues_across_pages(client, seeded_locations):
    response = client.get("/api/rankings", params={
        "district": "강남구", "category": "관광지", "page": 2, "size": 2,
    })
    assert response.status_code == 200
    assert [item["rank"] for item in response.json()["items"]] == [3, 4]
    assert response.json()["pagination"] == {
        "page": 2, "size": 2, "total_items": 5, "total_pages": 3,
    }

def test_districts_put_other_last(client, seeded_locations):
    assert client.get("/api/meta/districts").json()["items"][-1] == "기타"
```

- [ ] **Step 2: Confirm routes initially return 404**

Run: `python -m pytest tests/integration/test_meta_api.py tests/integration/test_rankings_api.py -v`

Expected: route assertions fail with HTTP 404.

- [ ] **Step 3: Implement exact queries and response mapping**

```python
offset = (page - 1) * size
query = (select(Location)
    .where(Location.district == district, Location.category == category)
    .order_by(Location.source_order.asc(), Location.id.asc())
    .offset(offset).limit(size))
items = [RankingItem(rank=offset + index, address=" ".join(filter(None, [row.address1, row.address2])) or None, **mapped(row))
         for index, row in enumerate(session.scalars(query), start=1)]
```

Calculate `total_pages` as `ceil(total_items / size)` with zero mapping to zero. Return the seven fixed categories in contract order; sort districts ascending with `기타` explicitly last.

- [ ] **Step 4: Verify routes**

Run: `python -m pytest tests/integration/test_meta_api.py tests/integration/test_rankings_api.py -v`

Expected: all success, empty-result, invalid-enum, page, and size cases pass.

- [ ] **Step 5: Commit location query APIs**

```bash
git add app/locations app/main.py tests/integration
git commit -m "feat: add metadata and ranking APIs"
```

---

### Task 5: Post Search and CRUD

**Files:**
- Create: `app/community/__init__.py`, `app/community/schemas.py`, `app/community/posts.py`, `app/community/router.py`
- Create: `tests/integration/test_posts_api.py`, `tests/unit/test_community_schemas.py`
- Modify: `app/main.py`

**Interfaces:**
- Produces: list/create/get/update/delete post operations and `/api/posts` routes.

- [ ] **Step 1: Write tests for trimming, filters, ordering, passwords, and response secrecy**

```python
def test_post_response_never_contains_password(client):
    created = client.post("/api/posts", json={
        "tag": "자유", "title": " 제목 ", "content": " 본문 ", "password": "1234",
    })
    assert created.status_code == 201
    assert created.json()["title"] == "제목"
    assert "password" not in json.dumps(created.json())

def test_wrong_password_returns_contract_error(client, post):
    response = client.request("DELETE", f"/api/posts/{post.id}", json={"password": "9999"})
    assert response.status_code == 403
    assert response.json()["code"] == "PASSWORD_MISMATCH"
```

- [ ] **Step 2: Confirm post routes fail before implementation**

Run: `python -m pytest tests/unit/test_community_schemas.py tests/integration/test_posts_api.py -v`

Expected: missing module or HTTP 404 failures.

- [ ] **Step 3: Implement strict schemas and post service**

```python
class PostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tag: PostTag
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
    password: Annotated[str, StringConstraints(min_length=4, max_length=20)]
```

For list queries, trim `q`; omit the search predicate when it becomes empty. Otherwise apply `lower(title) LIKE lower(:pattern) OR lower(content) LIKE lower(:pattern)`, combine tag with AND, and order by `created_at DESC, id DESC`. Compare the stored password before any update/delete mutation and raise typed domain errors.

- [ ] **Step 4: Run post tests plus a password-field scan**

Run: `python -m pytest tests/unit/test_community_schemas.py tests/integration/test_posts_api.py -v`

Expected: CRUD, 404/403, combined filter, empty query, pagination, and secrecy tests all pass.

- [ ] **Step 5: Commit post APIs**

```bash
git add app/community app/main.py tests
git commit -m "feat: add anonymous post APIs"
```

---

### Task 6: Comment CRUD and Transactional Cascade

**Files:**
- Create: `app/community/comments.py`
- Create: `tests/integration/test_comments_api.py`
- Modify: `app/community/schemas.py`, `app/community/router.py`

**Interfaces:**
- Consumes: post lookup and shared domain errors from Task 5.
- Produces: list/create/update/delete comment operations and both comment route groups.

- [ ] **Step 1: Test ordering, missing parents, password checks, and cascade behavior**

```python
def test_comments_are_oldest_first(client, post, comments):
    payload = client.get(f"/api/posts/{post.id}/comments").json()
    assert [item["id"] for item in payload["items"]] == [comment.id for comment in comments]

def test_deleting_post_removes_comments_in_same_transaction(client, post, db_session):
    response = client.request("DELETE", f"/api/posts/{post.id}", json={"password": post.password})
    assert response.status_code == 204
    assert db_session.scalar(select(func.count(Comment.id))) == 0
```

- [ ] **Step 2: Confirm comment routes initially return 404**

Run: `python -m pytest tests/integration/test_comments_api.py -v`

Expected: HTTP 404 route failures.

- [ ] **Step 3: Implement comments with one commit per request**

List by `created_at ASC, id ASC`; check parent existence before list/create; map missing parents to `POST_NOT_FOUND`, missing comments to `COMMENT_NOT_FOUND`, and password mismatch to `PASSWORD_MISMATCH`. A post delete relies on the database cascade and commits once.

- [ ] **Step 4: Verify all comment flows**

Run: `python -m pytest tests/integration/test_comments_api.py tests/integration/test_posts_api.py -v`

Expected: comment CRUD and regression tests pass with no response password fields.

- [ ] **Step 5: Commit comment APIs**

```bash
git add app/community tests/integration
git commit -m "feat: add anonymous comment APIs"
```

---

### Task 7: Deterministic Chat Query Parsing and Retrieval

**Files:**
- Create: `app/chat/__init__.py`, `app/chat/schemas.py`, `app/chat/query.py`, `app/chat/retrieval.py`
- Create: `tests/unit/test_chat_query.py`, `tests/integration/test_chat_retrieval.py`

**Interfaces:**
- Produces: `ParsedQuery`, `parse_query(message)`, `retrieve_sources(session, parsed, location_limit, post_limit) -> RetrievedContext`.

- [ ] **Step 1: Write parsing and retrieval tests**

```python
def test_query_extracts_known_terms_and_remaining_keyword():
    parsed = parse_query("강남구 문화시설 전시 추천")
    assert parsed.district == "강남구"
    assert parsed.location_category == "문화시설"
    assert parsed.keywords == ("전시", "추천")

def test_zero_coordinates_are_not_sent_as_map_evidence(db_session, location_factory):
    row = location_factory(longitude=0, latitude=0)
    db_session.add(row); db_session.commit()
    context = retrieve_sources(db_session, parse_query(row.title), 5, 5)
    assert context.locations[0].longitude is None
    assert context.locations[0].latitude is None
```

- [ ] **Step 2: Verify tests fail before chat modules exist**

Run: `python -m pytest tests/unit/test_chat_query.py tests/integration/test_chat_retrieval.py -v`

Expected: import failure for `app.chat.query`.

- [ ] **Step 3: Implement deterministic parsing and parameterized retrieval**

Match all 25 Seoul districts ending in `구`, the seven location categories, and the seven community tags by longest token first. Remove recognized tokens, punctuation, and Korean stop words; keep remaining whitespace-separated terms as keywords. Search locations across title/address fields and posts across title/content/tag, applying recognized filters and configured limits. Return public source DTOs separately from the richer prompt context.

- [ ] **Step 4: Verify retrieval behavior**

Run: `python -m pytest tests/unit/test_chat_query.py tests/integration/test_chat_retrieval.py -v`

Expected: district/category/tag extraction, no-keyword fallback, limits, ordering, and source mapping pass.

- [ ] **Step 5: Commit chat retrieval**

```bash
git add app/chat tests
git commit -m "feat: retrieve grounded chat context"
```

---

### Task 8: OpenAI Provider Adapter and Chat API

**Files:**
- Create: `app/chat/provider.py`, `app/chat/service.py`, `app/chat/router.py`
- Create: `tests/unit/test_chat_service.py`, `tests/integration/test_chat_api.py`
- Modify: `app/main.py`

**Interfaces:**
- Produces: `ChatProvider` protocol, `OpenAIChatProvider.answer()`, `ChatService.answer()`, and `POST /api/chat`.

- [ ] **Step 1: Test grounded prompts and provider error mapping with a fake provider**

```python
class FakeProvider:
    def __init__(self, result="근거 기반 답변", error=None):
        self.result, self.error, self.calls = result, error, []
    def answer(self, *, instructions, input_messages):
        self.calls.append((instructions, input_messages))
        if self.error: raise self.error
        return self.result

def test_rate_limit_maps_to_contract_error(client_with_provider):
    client = client_with_provider(ProviderRateLimited())
    response = client.post("/api/chat", json={"message": "강남구 관광지"})
    assert response.status_code == 429
    assert response.json()["code"] == "CHAT_RATE_LIMITED"
```

- [ ] **Step 2: Confirm chat tests fail before provider and route exist**

Run: `python -m pytest tests/unit/test_chat_service.py tests/integration/test_chat_api.py -v`

Expected: missing provider module or HTTP 404.

- [ ] **Step 3: Implement the provider port and Responses API adapter**

```python
class OpenAIChatProvider:
    def __init__(self, client: OpenAI, model: str):
        self.client, self.model = client, model

    def answer(self, *, instructions: str, input_messages: list[dict[str, str]]) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=input_messages,
            )
            return response.output_text
        except RateLimitError as exc:
            raise ProviderRateLimited from exc
        except (APITimeoutError, APIConnectionError, APIError) as exc:
            raise ProviderUnavailable from exc
```

Define provider-neutral `ProviderRateLimited` and `ProviderUnavailable` exceptions so services and tests never depend on OpenAI exception constructors. Pass at most 10 history items, then the current message and serialized retrieved context. Instructions explicitly forbid unsupported claims and require an insufficiency response when context is empty. Missing key and `ProviderUnavailable` map to 502 `CHAT_PROVIDER_ERROR`; `ProviderRateLimited` maps to 429 `CHAT_RATE_LIMITED`. Never log prompt context or full conversation. The Responses API adapter follows the official [text generation guide](https://developers.openai.com/api/docs/guides/text) and keeps the model configurable.

- [ ] **Step 4: Implement dependency injection and the `/api/chat` route**

The app factory creates the provider only when serving a chat request; server startup succeeds without a key. Tests override `get_chat_provider` with `FakeProvider`, so they perform no network calls.

- [ ] **Step 5: Verify chat behavior and full error regression**

Run: `python -m pytest tests/unit/test_chat_service.py tests/integration/test_chat_api.py tests/integration/test_errors.py -v`

Expected: success, empty evidence, history limit, missing key, rate limit, timeout, and provider failure cases pass.

- [ ] **Step 6: Commit the chat API**

```bash
git add app/chat app/main.py tests
git commit -m "feat: add grounded chatbot API"
```

---

### Task 9: Health, Contract Tests, Observability, and Render Deployment

**Files:**
- Create: `app/health.py`, `tests/integration/test_health_api.py`, `tests/contract/test_openapi_contract.py`
- Create: `render.yaml`, `README.md`
- Modify: `app/main.py`, `.env.example`

**Interfaces:**
- Produces: `GET /api/health`, request timing logs, deploy/start/import documentation, OpenAPI contract gate.

- [ ] **Step 1: Write health, log-secrecy, and contract tests**

```python
def test_health_checks_database(client):
    assert client.get("/api/health").json() == {"status": "ok", "database": "ok"}

def test_runtime_openapi_exposes_every_contract_operation(app):
    expected = load_operations("shared/openapi.yaml")
    actual = operations_from_document(app.openapi())
    assert actual == expected
```

Contract comparison covers method/path, status codes, required fields, enums, nullability, and `additionalProperties: false`; normalize OpenAPI 3.1 `$ref` structures before comparison.

- [ ] **Step 2: Confirm health and contract checks fail**

Run: `python -m pytest tests/integration/test_health_api.py tests/contract/test_openapi_contract.py -v`

Expected: missing health route and contract mismatches.

- [ ] **Step 3: Implement health and safe request logging**

Run `SELECT 1` inside the health handler. Middleware logs method, route template when available, status code, and elapsed milliseconds; it never reads or logs request bodies. Database failure returns the shared 500 shape.

- [ ] **Step 4: Add Render configuration and operator documentation**

```yaml
services:
  - type: web
    name: mwohalgu-backend
    runtime: python
    buildCommand: pip install -e . && alembic upgrade head
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    disk:
      name: mwohalgu-data
      mountPath: /var/data
      sizeGB: 1
```

Set production `DATABASE_URL=sqlite:////var/data/mwohalgu.db`, configure `CORS_ORIGINS` with only the Netlify production origin and approved local origins, and document that location import is an explicit one-time/repeatable command after the disk is mounted. Preserve the exact attribution in `README.md`: “이 서비스는 한국관광공사 Tour API(TourAPI 4.0)의 데이터를 활용하였습니다.” plus the source URL and 공공누리 제3유형 notice from `data/SOURCE.md`.

- [ ] **Step 5: Run complete verification and coverage gate**

Run: `python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=90 && ruff check app scripts tests && ruff format --check app scripts tests && mypy app`

Expected: all tests pass, coverage is at least 90%, and every static check exits 0.

- [ ] **Step 6: Perform secret and password response scans**

Run: `git grep -nE 'sk-[A-Za-z0-9_-]{20,}|OPENAI_API_KEY=.+' -- ':!*.example'`

Expected: no output. Then run `git grep -n 'password' app | sort`; manually confirm occurrences are limited to input schemas, ORM write-only fields, and comparison logic—not output schemas or logging calls.

- [ ] **Step 7: Commit operations and contract gates**

```bash
git add app tests render.yaml README.md .env.example shared/openapi.yaml
git commit -m "chore: add deployment and contract verification"
```

## Release Acceptance Checklist

- [ ] Confirm all seven committed JSON files under `data/raw/` retain their original bytes and `data/manifest.json` totals sum to 6,518.
- [ ] Run `alembic upgrade head` against a fresh local SQLite database.
- [ ] Run `python scripts/import_locations.py --manifest data/manifest.json --verify-total 6518` twice; the second run reports updates without duplicates.
- [ ] Run the complete verification command from Task 9.
- [ ] Compare runtime `/openapi.json` with `shared/openapi.yaml` through the contract suite.
- [ ] Deploy to Render with a persistent disk and run the import against that disk once.
- [ ] Restart/redeploy Render and confirm `/api/health` remains 200 and imported location counts persist.
- [ ] Exercise one ranking page, one post/comment lifecycle, and one chat request from the deployed frontend origin.
- [ ] Confirm repository history and Render logs contain no API key, passwords, SQL statements with values, or complete chat conversations.

## Requirement Traceability

| PRD area | Plan coverage |
|---|---|
| BE-DATA-01, BE-DATA-02 | Task 3, release import checks |
| locations/posts/comments models | Task 2 |
| BE-META-01, BE-RANK-01 | Task 4 |
| BE-POST-01, BE-POST-02 | Task 5 |
| BE-COMMENT-01 | Task 6 |
| BE-CHAT-01 | Task 7 |
| BE-CHAT-02 | Task 8 |
| validation and common errors | Tasks 1, 4–8 |
| environment and secret handling | Tasks 1, 8, 9 |
| health, CORS, logs, persistence | Task 9 and release checklist |
| OpenAPI completion criteria | Tasks 1 and 9 |
