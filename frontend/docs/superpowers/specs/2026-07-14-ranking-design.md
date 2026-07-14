# 뭐할구 프론트엔드 2단계: 장소 랭킹 설계

## 목적

사용자가 서울의 구와 카테고리를 선택해 백엔드가 제공한 순위 그대로 장소 목록을 페이지별로 확인하게 한다. 메타데이터·랭킹 장애, 빈 결과, 이미지 누락에서도 사용자가 다음 행동을 이해할 수 있어야 한다.

## 의존성과 범위

1단계의 라우터, API 클라이언트, 비동기 상태 UI, 페이지네이션, 디자인 토큰을 사용한다. `/` 화면과 `src/features/ranking`만 소유하며 게시판과 챗봇에는 의존하지 않는다.

```text
src/features/ranking/
  ranking-page.js
  ranking-api.js
  ranking-state.js
  ranking-view.js
  ranking.css
src/assets/
  place-fallback.svg
```

### 포함

- 앱 진입 시 카테고리와 구 목록 병렬 로딩
- 구·카테고리 선택과 랭킹 요청
- 순위, 장소명, 주소, 선택적 이미지·전화번호 표시
- 기본 20개 페이지네이션
- URL 쿼리 `district`, `category`, `page` 동기화
- 대체 이미지, 빈 결과, 오류와 재시도

### 제외

- 프론트엔드 순위 계산·재정렬
- 장소 상세 화면, 지도, 즐겨찾기
- 카테고리나 구의 고정 목록 대체

## 공개 인터페이스

- `mountRankingPage(context) -> () => void`: `/` 화면을 마운트하고 요청·이벤트를 정리한다.
- `getCategories({ signal }) -> Promise<string[]>`: `GET /api/meta/categories`의 `items`를 반환한다.
- `getDistricts({ signal }) -> Promise<string[]>`: `GET /api/meta/districts`의 `items`를 반환한다.
- `getRankings({ district, category, page = 1, size = 20, signal }) -> Promise<{ items, pagination }>`
- `parseRankingQuery(searchParams) -> { district: string, category: string, page: number }`: 유효하지 않은 페이지는 1로 정규화한다.
- `toRankingQuery(state) -> URLSearchParams`: 선택되지 않은 값과 기본 페이지 1은 URL에서 생략한다.

## 화면과 상호작용

초기 화면은 설명, 구 선택, 카테고리 선택, 검색 버튼을 표시한다. 두 메타데이터가 모두 성공하기 전에는 선택 컨트롤을 사용할 수 없으며, 어느 하나라도 실패하면 전체 메타데이터 상태에 재시도를 제공한다. API가 반환한 순서를 옵션에 그대로 사용한다.

구와 카테고리를 모두 선택해야 검색할 수 있다. 제출하면 `district`, `category`, `page=1` 상태로 URL을 갱신한다. 직접 입력한 URL의 값이 로드된 메타데이터에 없으면 해당 선택만 비우고 랭킹을 요청하지 않으며 안내를 표시한다.

랭킹 카드에는 서버의 `rank`를 변형 없이 표시한다. `thumbnail_url`, `image_url`, 공통 `place-fallback.svg` 순서로 이미지를 선택하고 이미지 `error` 시 공통 대체 이미지로 한 번만 교체한다. `address`와 `phone`은 값이 있을 때만 렌더링한다. 모든 이미지에는 장소명 기반 대체 텍스트를 제공한다.

페이지 이동은 기존 필터를 유지한 채 URL의 `page`를 바꾸고 목록 영역 상단으로 포커스 또는 스크롤을 이동한다. `pagination.total_pages`가 0이면 “선택 조건에 해당하는 장소가 없습니다.”를 표시하고 페이지네이션을 숨긴다.

## 상태와 오류

상태는 `{ metadata, district, category, page, result }`로 제한하고 URL을 선택·페이지 상태의 단일 기준으로 사용한다. 새 검색과 페이지 이동은 이전 랭킹 요청을 취소한다. 취소는 오류로 보이지 않는다.

메타데이터 오류와 랭킹 오류는 별도로 관리한다. 재시도는 실패했던 요청의 구·카테고리·페이지를 유지한다. 응답의 `rank`, `source_order`, `pagination`을 프론트에서 재계산하지 않는다.

## 테스트

- 메타데이터 병렬 요청과 부분 실패 시 전체 재시도
- 두 선택 전 검색 차단, 유효·무효 URL 쿼리 복원
- `rank`와 API 배열 순서 보존
- 선택적 주소·전화 렌더링과 이미지 fallback
- 빈 결과와 `total_pages=0`, 첫·중간·마지막 페이지 동작
- 빠른 연속 검색 시 이전 요청 취소와 stale 응답 무시
- Playwright API mock으로 선택 → 조회 → 다음 페이지 → 뒤로 가기 흐름
- 360px에서 필터와 카드가 가로 스크롤 없이 표시되는지 확인

## 완료 기준

- PRD의 일곱 카테고리와 구 목록을 API 응답에서 선택할 수 있다.
- 선택 조건, 페이지, 뒤로/앞으로 가기가 URL과 화면에서 일치한다.
- 결과가 성공·빈 결과·오류 중 정확한 한 상태만 표시한다.
- 서버가 반환한 순위와 순서가 그대로 보인다.
- 이미지·주소·전화번호 누락이 레이아웃이나 탐색을 막지 않는다.

