# 뭐할구 프론트엔드 1단계: SPA 기반 설계

## 목적

Vite와 Vanilla JavaScript로 모든 기능이 공유할 앱 셸, 라우팅, API, UI, 스타일, 테스트 및 배포 기반을 만든다. 이 단계의 결과물은 빈 기능 화면이라도 `/`, `/posts`, `/posts/new`, `/posts/:id`, `/posts/:id/edit`에 직접 접근하고 새로고침할 수 있으며, 이후 단계가 안정된 공개 인터페이스 위에서 기능을 추가할 수 있는 SPA다.

## 범위

### 포함

- Vite 프로젝트와 npm 스크립트
- `api.yaml`을 `shared/openapi.yaml`로 이동해 API 계약의 단일 정본 확립
- History API 기반 라우터와 앱 셸
- 서비스명, 홈·게시판 내비게이션, 본문, 하단 출처, 챗봇 마운트 지점을 포함한 공통 레이아웃
- 환경변수 기반 API 클라이언트와 안전한 공통 오류 변환
- 로딩, 빈 결과, 오류·재시도, 페이지네이션, 모달 등 공통 UI
- 선택된 “실용적인 시티 가이드” 디자인 토큰과 반응형 기반
- Vitest + jsdom 및 Playwright 테스트 기반
- Netlify SPA fallback과 환경변수 예시

### 제외

- 실제 랭킹, 게시글, 댓글, 챗봇 API 연동
- 장소 상세 라우트
- 로그인, 사용자 저장 상태, 서버 대화 기록

## 기술 결정

### 구조

`src/app`은 시작과 화면 생명주기를, `src/router`는 URL 해석을, `src/api`는 HTTP 계약을, `src/ui`는 재사용 가능한 DOM UI를 담당한다. 기능 코드는 이후 `src/features/<feature>`에 추가하며 공통 기반이 기능 도메인을 참조하지 않도록 의존 방향을 고정한다.

```text
index.html
netlify.toml
shared/openapi.yaml
src/
  main.js
  app/
    app.js
    layout.js
  router/
    router.js
    routes.js
  api/
    client.js
    errors.js
  ui/
    async-state.js
    modal.js
    pagination.js
  styles/
    tokens.css
    global.css
    components.css
tests/
  unit/
  e2e/
```

각 라우트 렌더러는 `mount(context)`를 제공하고 정리 함수 `() => void`를 반환한다. 라우터는 다음 화면을 마운트하기 전에 이전 정리 함수를 호출한다. `context`는 `{ outlet, params, query, signal, navigate }`를 포함하며 화면 전환마다 새 `AbortController`를 사용한다.

### 공개 인터페이스

- `startApp({ root })`: 앱 셸과 라우터를 시작한다.
- `createRouter({ routes, outlet, onNotFound })`: 링크 가로채기, popstate 처리, 라우트 마운트·정리를 담당한다.
- `navigate(to, { replace = false })`: 동일 출처의 앱 URL을 이동한다.
- `request(path, { method = 'GET', query, body, signal })`: `VITE_API_BASE_URL`과 `/api` 경로를 결합해 요청한다.
- `ApiError`: `{ status, code, message, details }`를 가진 오류다.
- `renderAsyncState(container, { kind, message, onRetry })`: loading, empty, error 상태를 표시한다.
- `openModal({ title, content, trigger, confirmLabel, onConfirm })`: focus trap, Escape 닫기, 트리거 포커스 복귀를 보장한다.
- `renderPagination(container, { page, totalPages, onPageChange })`: 첫·이전·다음·마지막 상태와 현재 페이지를 제공한다.

### API와 보안

기본 URL은 `import.meta.env.VITE_API_BASE_URL`만 사용하며 소스에 운영 서버 주소를 넣지 않는다. `request`는 2xx를 성공으로 판단하고 `204`는 `undefined`를 반환한다. 실패 응답이 OpenAPI의 JSON 오류 형식이면 이를 `ApiError`로 바꾸고, 비-JSON 또는 네트워크 오류에는 비밀값이 없는 일반 메시지를 사용한다. `AbortError`는 그대로 전달해 화면이 사용자 오류로 렌더링하지 않게 한다.

비밀번호와 환경변수, 내부 예외 본문은 UI 메시지·URL·저장소·console 출력에 포함하지 않는다. 공통 오류 메시지는 서버 `message`를 우선 사용하되 안전하지 않은 값은 일반 안내로 대체한다.

## UI 설계

선택된 B안은 밝은 회색 앱 배경, 흰색 콘텐츠 패널, 진한 본문색, 선명한 파란색 주 액션으로 구성한다. 토큰은 색상, 간격, 반경, 그림자, 글꼴 크기, 레이어 순서를 CSS custom property로 정의한다. 시스템 글꼴을 사용해 외부 폰트 장애를 없애고, 본문 최대 폭은 데스크톱에서 제한하되 360px부터 가로 스크롤 없이 동작한다.

상단 내비게이션은 현재 위치를 텍스트와 `aria-current`로 표시한다. 하단에는 “한국관광공사 TourAPI 제공 · 공공누리 제3유형”을 모든 주요 화면에서 접근 가능하게 둔다. 동적 로딩·오류 메시지는 `aria-live`로 전달한다.

## 상태와 데이터 흐름

라우터가 `location.pathname`과 `location.search`를 파싱하고 일치하는 화면을 마운트한다. 화면이 필터나 페이지를 변경할 때 URL을 먼저 갱신하면 라우터가 새 쿼리에서 상태를 재구성한다. 새 화면 전환 시 이전 요청을 취소하고 이벤트 리스너를 제거한다. 인증 또는 사용자 상태를 브라우저 저장소에 만들지 않는다.

## 테스트

- Vitest/jsdom: 라우트 매칭·파라미터 디코딩, 같은 출처 링크 가로채기, 화면 정리, 쿼리 직렬화, API 성공/204/오류/취소, 모달 포커스, 페이지네이션 경계
- Playwright: 각 PRD 라우트 직접 진입과 새로고침, 공통 내비게이션, 360px 가로 스크롤 부재, Netlify와 같은 SPA fallback
- 빌드: `npm run build`가 정적 결과물을 생성하고 소스에 API 키 또는 고정 운영 URL이 없어야 한다.

## 완료 기준

- 모든 공통 공개 인터페이스가 단위 테스트로 고정되어 있다.
- 정의된 다섯 라우트에 직접 접근해 공통 앱 셸과 임시 화면을 볼 수 있다.
- 요청 취소 후 이전 응답이 새 화면을 덮어쓰지 않는다.
- 키보드만으로 내비게이션, 모달 열기·확인·닫기가 가능하다.
- Netlify 배포 설정이 모든 SPA 경로를 `/index.html`로 fallback한다.
- `shared/openapi.yaml`이 API 계약의 단일 정본이며 기존 `api.yaml`은 남기지 않는다.

