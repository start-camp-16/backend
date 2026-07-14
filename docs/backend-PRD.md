# 뭐할구 백엔드 PRD

## 1. 문서 정보

| 항목 | 내용 |
|---|---|
| 제품명 | 뭐할구 |
| 대상 저장소 | 백엔드 전용 저장소 |
| 기술 스택 | FastAPI, SQLAlchemy, SQLite |
| 배포 | Render |
| API 계약 | `shared/openapi.yaml` |
| 목표 | 서울 장소 랭킹, 익명 게시판·댓글, 근거 기반 챗봇 API 제공 |

## 2. 범위와 원칙

- 서버는 상태를 SQLite에 저장하며 인증·회원 기능은 제공하지 않는다.
- 장소 랭킹은 점수를 계산하지 않고 JSON 원본 순서를 사용한다.
- 게시글과 댓글 수정·삭제 권한은 각 리소스에 저장된 비밀번호 일치만 확인한다.
- 과제 요구사항에 따라 비밀번호는 평문 저장·비교한다. 단, API 응답과 로그에는 절대 기록하지 않는다.
- OpenAI API 키, DB 경로, 허용 Origin, 모델명은 환경변수로 관리한다.
- API의 경로, 스키마, 상태 코드는 `shared/openapi.yaml`과 일치해야 한다.

## 3. 원천 데이터

현재 사용 가능한 서울 JSON은 7종, 총 6,518건이다.

| 카테고리 | 건수 |
|---|---:|
| 관광지 | 783 |
| 레포츠 | 126 |
| 문화시설 | 566 |
| 쇼핑 | 4,368 |
| 숙박 | 423 |
| 여행코스 | 51 |
| 축제공연행사 | 201 |
| 합계 | 6,518 |

`SOURCE.md`에는 음식점 1,632건을 포함한 8종·8,150건이 기재되어 있지만 현재 전달 파일에는 음식점 JSON이 없다. 초기 MVP는 실제 확보한 7종만 적재한다.

출처는 한국관광공사 TourAPI 4.0이며 공공누리 제3유형 조건에 따라 출처와 원본 API URL을 서비스에 표시한다. 수집일은 제공 문서에 없으므로 임의로 작성하지 않는다.

## 4. 데이터 적재

### BE-DATA-01 초기 적재

- 각 JSON의 `items`를 순서대로 읽고 배열 인덱스를 1부터 시작하는 `source_order`로 저장한다.
- `contentid`를 장소 고유키로 사용해 중복 적재를 방지한다.
- 동일 `contentid`가 이미 있으면 원본 필드는 갱신하되 커뮤니티 데이터에는 영향을 주지 않는다.
- `mapx`, `mapy`는 숫자로 변환하며 변환 불가 값은 null로 저장한다.
- 좌표가 `0, 0`인 항목은 DB에는 보존하되 지도·챗봇 근거에서 좌표 없음으로 취급한다.
- 주소에서 `서울특별시 {구}` 또는 `서울 {구}` 패턴으로 구 이름을 추출한다.
- 구를 추출하지 못하면 `기타`로 저장한다.
- 원본 이미지 URL과 텍스트를 임의로 변경하지 않는다.

### BE-DATA-02 적재 검증

- 전체 6,518건과 카테고리별 건수를 검증한다.
- `content_id` 중복이 없어야 한다.
- 각 카테고리 안에서 `source_order`가 원본 배열 순서와 일치해야 한다.
- 적재 결과를 건수 중심으로 로그에 남기되 원문 전체와 비밀번호는 기록하지 않는다.

## 5. 데이터 모델

### locations

| 필드 | 타입 | 제약/설명 |
|---|---|---|
| `id` | integer | PK |
| `content_id` | string | unique, 원본 `contentid` |
| `category` | string | 7개 허용 카테고리 |
| `title` | string | 장소명 |
| `address1` | string nullable | 원본 `addr1`을 그대로 저장 |
| `address2` | string nullable | 원본 `addr2`를 그대로 저장 |
| `district` | string | 추출한 서울 구 또는 `기타` |
| `longitude` | float nullable | 원본 `mapx` |
| `latitude` | float nullable | 원본 `mapy` |
| `image_url` | string nullable | `firstimage` |
| `thumbnail_url` | string nullable | `firstimage2` |
| `phone` | string nullable | `tel` |
| `source_order` | integer | 카테고리 JSON 내부의 1부터 시작하는 원본 순서 |

`category`, `district`, `source_order` 복합 조회에 인덱스를 둔다.

API의 `address`는 저장된 `address1`, `address2` 중 비어 있지 않은 값을 공백으로 연결한 표시용 값이다. DB에는 두 원본 값을 분리해 보존한다.

### posts

| 필드 | 타입 | 제약/설명 |
|---|---|---|
| `id` | integer | PK |
| `tag` | string | 고정 태그 7종 중 하나 |
| `title` | string | 1~100자 |
| `content` | text | 1~5,000자 |
| `password` | string | 4~20자, 평문, 응답·로그 제외 |
| `created_at` | datetime | UTC 저장 |
| `updated_at` | datetime | UTC 저장 |

게시글 목록을 위해 `created_at`에 인덱스를 둔다. 태그 필터를 위해 `tag`에도 인덱스를 둔다.

### comments

| 필드 | 타입 | 제약/설명 |
|---|---|---|
| `id` | integer | PK |
| `post_id` | integer | FK → posts.id, cascade delete |
| `content` | text | 1~1,000자 |
| `password` | string | 4~20자, 평문, 응답·로그 제외 |
| `created_at` | datetime | UTC 저장 |
| `updated_at` | datetime | UTC 저장 |

댓글 목록 조회를 위해 `post_id`, `created_at`에 인덱스를 둔다.

## 6. API 요구사항

### BE-META-01 카테고리·구

- `GET /api/meta/categories`: 적재 대상 7개 카테고리 반환
- `GET /api/meta/districts`: DB에 존재하는 구를 가나다순으로 반환하고 `기타`는 마지막에 배치

### BE-RANK-01 랭킹

- `GET /api/rankings`
- 필수 조건: `district`, `category`
- 선택 조건: `page` 기본 1, `size` 기본 20·최대 100
- 정렬: `source_order ASC`
- `rank`는 `(page - 1) * size + 페이지 내 위치 + 1`로 계산한다.
- 점수나 인기 지표는 반환하지 않는다.

### BE-POST-01 게시글 목록·검색

- `GET /api/posts`
- 선택 조건: `tag`, `q`, `page`, `size`
- 태그가 없으면 전체 태그를 조회한다.
- `q`가 있으면 제목 또는 본문에 부분 일치하는 게시글을 조회한다.
- `q`는 앞뒤 공백 제거 후 빈 문자열이면 검색 조건이 없는 것으로 처리한다.
- 검색은 SQLite MVP 범위에서 대소문자 구분 없는 `LIKE` 기반으로 구현한다.
- 태그와 검색어는 AND 조건으로 조합한다.
- 정렬은 `created_at DESC, id DESC`다.

### BE-POST-02 게시글 CRUD

- 작성 필드: 태그, 제목, 본문, 비밀번호
- 상세 응답: 태그, 제목, 본문, 작성·수정 시각
- 수정 필드: 비밀번호, 태그, 제목, 본문
- 삭제 필드: 비밀번호
- 비밀번호 불일치는 `403 PASSWORD_MISMATCH`다.
- 응답 스키마에서 `password`를 선언하지 않는다.

### BE-COMMENT-01 댓글 CRUD

- 목록은 특정 게시글의 댓글을 `created_at ASC, id ASC`로 반환한다.
- 작성 필드: 본문, 비밀번호
- 수정 필드: 비밀번호, 본문
- 삭제 필드: 비밀번호
- 존재하지 않는 게시글에 댓글을 작성하면 `404 POST_NOT_FOUND`다.
- 게시글 삭제 시 댓글을 같은 트랜잭션에서 삭제한다.

### BE-CHAT-01 챗봇 검색

- 입력은 사용자 메시지와 선택적인 최근 대화 기록이다.
- 서버는 메시지에서 서울 구, 장소 카테고리, 커뮤니티 태그, 나머지 핵심어를 추출한다.
- 장소는 제목·주소와 추출된 구·카테고리 조건으로 검색한다.
- 게시글은 제목·본문·태그에서 검색한다.
- 각 소스의 상위 결과 개수는 환경변수로 제한하며 기본값은 장소 5건, 게시글 5건이다.

### BE-CHAT-02 OpenAI 호출

- 시스템 지침은 전달된 근거만으로 서울 지역 정보를 답하도록 제한한다.
- 근거가 없으면 정보가 부족하다고 답하도록 한다.
- 모델명은 `OPENAI_MODEL` 환경변수로 관리한다.
- API 키가 없으면 서버 시작은 허용하되 챗봇 요청에 명확한 구성 오류를 반환한다.
- 타임아웃, rate limit, 제공자 오류를 공통 오류로 변환한다.
- 서버는 대화 내용을 DB에 저장하지 않는다.

## 7. 공통 입력 검증

| 입력 | 규칙 |
|---|---|
| 게시글 제목 | trim 후 1~100자 |
| 게시글 본문 | trim 후 1~5,000자 |
| 댓글 본문 | trim 후 1~1,000자 |
| 비밀번호 | 4~20자 |
| 검색어 | trim 후 최대 100자 |
| 챗봇 메시지 | trim 후 1~1,000자 |
| 페이지 | 1 이상 |
| 페이지 크기 | 1~100 |

허용 게시글 태그는 `관광`, `맛집`, `문화`, `행사`, `숙박`, `쇼핑`, `자유`다.

FastAPI의 기본 요청 검증 오류도 예외 처리기를 통해 HTTP 400과 `VALIDATION_ERROR` 형식으로 변환하여 공유 명세와 일치시킨다.

## 8. 오류 규칙

모든 오류는 다음 구조를 사용한다.

```json
{
  "code": "PASSWORD_MISMATCH",
  "message": "비밀번호가 일치하지 않습니다.",
  "details": null
}
```

| HTTP | 코드 | 상황 |
|---:|---|---|
| 400 | `VALIDATION_ERROR` | 입력값 또는 쿼리 조건 오류 |
| 403 | `PASSWORD_MISMATCH` | 게시글·댓글 비밀번호 불일치 |
| 404 | `POST_NOT_FOUND` | 게시글 없음 |
| 404 | `COMMENT_NOT_FOUND` | 댓글 없음 |
| 429 | `CHAT_RATE_LIMITED` | OpenAI rate limit |
| 502 | `CHAT_PROVIDER_ERROR` | OpenAI 타임아웃·응답 실패·구성 누락 |
| 500 | `INTERNAL_ERROR` | 예상하지 못한 서버 오류 |

내부 예외 메시지, SQL, API 키, 비밀번호는 클라이언트 응답에 포함하지 않는다.

## 9. 환경변수

| 이름 | 목적 | 예시 포함 여부 |
|---|---|---|
| `DATABASE_URL` | SQLite 연결 주소 | `.env.example`에 키만 포함 |
| `OPENAI_API_KEY` | OpenAI 인증 | 실제 값 절대 커밋 금지 |
| `OPENAI_MODEL` | 사용할 모델명 | `.env.example`에 기본 예시 가능 |
| `CHAT_LOCATION_LIMIT` | 장소 근거 최대 개수 | 기본 5 |
| `CHAT_POST_LIMIT` | 게시글 근거 최대 개수 | 기본 5 |
| `CORS_ORIGINS` | 허용 프론트 Origin 목록 | 쉼표 구분 |

`.env`는 `.gitignore`에 포함하고 `.env.example`에는 비밀값을 넣지 않는다.

## 10. 테스트 요구사항

- 데이터 적재 건수·중복·원본 순서 테스트
- 구·카테고리 필터와 페이지별 rank 테스트
- 게시글 CRUD와 비밀번호 성공·실패 테스트
- 게시글 태그 필터·검색어·페이지 조합 테스트
- 댓글 CRUD, 비밀번호, 게시글 cascade 삭제 테스트
- 모든 성공 응답에 비밀번호가 없는지 테스트
- 챗봇 검색 결과 구성 테스트
- OpenAI 클라이언트를 대체한 성공·rate limit·timeout 테스트
- 공통 오류 스키마 테스트

## 11. 운영·배포

- `GET /api/health`는 DB 연결 가능 여부와 서비스 상태를 반환한다.
- Render 영구 디스크를 사용하지 않으면 SQLite 데이터가 재배포·재시작 시 유실될 수 있으므로 배포 구성에서 영속 디스크를 연결해야 한다.
- 운영 DB 초기화는 앱 시작마다 삭제·재생성하지 않는다.
- CORS는 Netlify 운영 도메인과 로컬 개발 Origin만 허용한다.
- 로그는 요청 경로, 상태 코드, 처리 시간 중심으로 남기며 요청 본문의 비밀번호와 챗봇 전체 대화를 기록하지 않는다.

## 12. MVP 제외 범위

- 회원·세션·JWT·관리자
- 조회수·좋아요·북마크
- 댓글·게시글 실시간 갱신
- 파일 업로드
- 사용자 정의·다중 태그
- 검색 엔진·벡터 DB·임베딩 저장소
- 서버 대화 기록 저장
- 고가용성·수평 확장

## 13. 완료 조건

- 실제 확보한 서울 JSON 7종·6,518건이 검증을 통과한다.
- 공유 OpenAPI의 모든 엔드포인트가 구현되고 자동 문서에 노출된다.
- 프론트와 합의한 성공·오류 스키마가 일치한다.
- 테스트 환경에서 게시글·댓글·검색·랭킹·챗봇 흐름이 통과한다.
- Render 배포 URL에서 헬스 체크와 DB 영속성을 확인한다.
- 소스와 Git 이력에 실제 비밀정보가 없다.
