# 뭐할구 Backend

서울 구별 장소 랭킹, 익명 게시글·댓글, 저장소 근거 기반 챗봇을 제공하는 FastAPI 서비스입니다.

## Local Development

Python 3.12와 [uv](https://docs.astral.sh/uv/)가 필요합니다.

```bash
uv sync --dev
cp .env.example .env
uv run alembic upgrade head
uv run python scripts/import_locations.py --manifest data/manifest.json --verify-total 6518
uv run uvicorn app.main:app --reload
```

API 문서는 서버 실행 후 `http://localhost:8000/docs`에서 확인합니다. API 계약의 기준 파일은 `shared/openapi.yaml`입니다.

## Verification

```bash
uv run pytest --cov=app --cov-report=term-missing
uv run ruff check app scripts tests
uv run ruff format --check app scripts tests
uv run mypy app scripts
```

## Configuration

`.env.example`을 복사해 DB URL, CORS origin, OpenAI 모델을 설정합니다. 실제 `OPENAI_API_KEY`, `.env`, SQLite 파일은 커밋하지 않습니다. 운영 SQLite는 Render 영속 디스크의 `/var/data/mwohalgu.db`를 사용합니다. 장소 적재 명령은 재실행 가능하며 기존 `content_id`를 갱신합니다.

## Data Source

이 서비스는 한국관광공사 Tour API(TourAPI 4.0)의 데이터를 활용하였습니다.

- 출처: 한국관광공사 ([공공데이터포털 원본 API](https://www.data.go.kr/data/15101578/openapi.do))
- 라이선스: 공공누리 제3유형(출처 표시 + 변경 금지)
- 상세 조건: `data/SOURCE.md`
