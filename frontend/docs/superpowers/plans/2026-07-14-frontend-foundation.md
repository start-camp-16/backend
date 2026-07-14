# 뭐할구 프론트엔드 1단계: SPA 기반 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vite·Vanilla JavaScript 기반의 접근 가능한 SPA 공통 기반과 테스트·Netlify 배포 기반을 만든다.

**Architecture:** `app → router/api/ui` 방향으로만 의존하며 기능 모듈은 공통 계층의 공개 함수만 사용한다. 라우트 마운트마다 `AbortController`를 만들고 이전 화면의 요청과 이벤트를 정리한다.

**Tech Stack:** Vite, Vanilla JavaScript, HTML, CSS, Vitest, jsdom, Playwright, Netlify

## Global Constraints

- 모든 핵심 기능은 로그인 없이 동작한다.
- API 계약의 단일 정본은 `shared/openapi.yaml`이다.
- API 기본 URL은 `VITE_API_BASE_URL`만 사용하고 운영 URL·API 키를 소스에 넣지 않는다.
- 비밀번호, 내부 예외, 환경변수는 화면·URL·저장소·로그에 노출하지 않는다.
- 360px에서 가로 스크롤이 없어야 하며 모든 입력에 연결된 label을 둔다.
- TourAPI 및 공공누리 제3유형 출처는 모든 주요 화면에서 접근 가능해야 한다.

---

### Task 1: 프로젝트와 라우트 계약

**Files:**
- Create: `package.json`, `vite.config.js`, `vitest.setup.js`, `index.html`, `.env.example`, `.gitignore`
- Move: `api.yaml` → `shared/openapi.yaml`
- Create: `src/router/routes.js`
- Test: `tests/unit/router/routes.test.js`

**Interfaces:**
- Produces: `matchRoute(pathname) -> { name, params } | null`, `ROUTES`

- [ ] **Step 1: 프로젝트 설정과 API 계약 경로를 만든다**

Run: `npm init -y && npm install -D vite vitest jsdom @playwright/test && mkdir -p shared src/router tests/unit/router`

Then set scripts to `dev: vite`, `build: vite build`, `preview: vite preview`, `test: vitest run`, `test:watch: vitest`, `test:e2e: playwright test`; set `type` to `module`. Move the contract with `mv api.yaml shared/openapi.yaml`. Put only `VITE_API_BASE_URL=http://localhost:8000` in `.env.example`; ignore `node_modules/`, `dist/`, `.env`, `playwright-report/`, `test-results/`, `.superpowers/`.

- [ ] **Step 2: 라우트 매칭 실패 테스트를 작성한다**

```js
import { describe, expect, it } from 'vitest';
import { matchRoute } from '../../../src/router/routes.js';

describe('matchRoute', () => {
  it.each([
    ['/', 'ranking', {}], ['/posts', 'posts', {}], ['/posts/new', 'post-new', {}],
    ['/posts/12', 'post-detail', { id: '12' }], ['/posts/12/edit', 'post-edit', { id: '12' }],
  ])('%s를 해석한다', (path, name, params) => expect(matchRoute(path)).toEqual({ name, params }));
  it('1 미만이거나 숫자가 아닌 id를 거부한다', () => {
    expect(matchRoute('/posts/0')).toBeNull();
    expect(matchRoute('/posts/x')).toBeNull();
  });
});
```

- [ ] **Step 3: 실패를 확인한다**

Run: `npm test -- tests/unit/router/routes.test.js`  
Expected: FAIL with `Cannot find module '../../../src/router/routes.js'`.

- [ ] **Step 4: 고정·동적 라우트를 구현한다**

```js
export const ROUTES = [
  { name: 'ranking', pattern: /^\/$/ },
  { name: 'posts', pattern: /^\/posts$/ },
  { name: 'post-new', pattern: /^\/posts\/new$/ },
  { name: 'post-edit', pattern: /^\/posts\/([1-9]\d*)\/edit$/, keys: ['id'] },
  { name: 'post-detail', pattern: /^\/posts\/([1-9]\d*)$/, keys: ['id'] },
];
export function matchRoute(pathname) {
  for (const route of ROUTES) {
    const match = pathname.match(route.pattern);
    if (match) return { name: route.name, params: Object.fromEntries((route.keys ?? []).map((key, i) => [key, match[i + 1]])) };
  }
  return null;
}
```

- [ ] **Step 5: 테스트와 빌드를 확인하고 커밋한다**

Run: `npm test -- tests/unit/router/routes.test.js && npm run build`  
Expected: route tests PASS; Vite build succeeds.  
Commit: `git add package.json package-lock.json vite.config.js vitest.setup.js index.html .env.example .gitignore shared src/router tests/unit/router && git commit -m "chore: 프론트엔드 SPA 기반 초기화"`

### Task 2: API 클라이언트와 오류 변환

**Files:**
- Create: `src/api/errors.js`, `src/api/client.js`
- Test: `tests/unit/api/client.test.js`

**Interfaces:**
- Produces: `request(path, { method, query, body, signal })`, `ApiError`

- [ ] **Step 1: 성공·204·오류·취소 테스트를 작성한다**

```js
import { afterEach, expect, it, vi } from 'vitest';
import { request } from '../../../src/api/client.js';
import { ApiError } from '../../../src/api/errors.js';
afterEach(() => vi.unstubAllGlobals());
it('query와 JSON body를 전송한다', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'Content-Type': 'application/json' } })));
  await expect(request('/api/x', { method: 'POST', query: { page: 2, empty: '' }, body: { a: 1 } })).resolves.toEqual({ ok: true });
  expect(fetch.mock.calls[0][0]).toContain('/api/x?page=2');
});
it('204는 undefined다', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
  await expect(request('/api/x')).resolves.toBeUndefined();
});
it('서버 오류를 ApiError로 바꾼다', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ code: 'PASSWORD_MISMATCH', message: '비밀번호가 일치하지 않습니다.', details: null }), { status: 403 })));
  await expect(request('/api/x')).rejects.toMatchObject({ status: 403, code: 'PASSWORD_MISMATCH' });
  expect(ApiError.prototype).toBeInstanceOf(Error);
});
```

- [ ] **Step 2: 테스트 실패를 확인한다**

Run: `npm test -- tests/unit/api/client.test.js`  
Expected: FAIL because API modules do not exist.

- [ ] **Step 3: 최소 API 계층을 구현한다**

```js
// errors.js
export class ApiError extends Error {
  constructor({ status = 0, code = 'NETWORK_ERROR', message = '요청을 처리할 수 없습니다.', details = null }) {
    super(message); Object.assign(this, { name: 'ApiError', status, code, details });
  }
}
```

```js
// client.js
import { ApiError } from './errors.js';
const base = () => (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
export async function request(path, { method = 'GET', query = {}, body, signal } = {}) {
  const url = new URL(`${base()}${path}`, window.location.origin);
  Object.entries(query).forEach(([k, v]) => { if (v !== '' && v != null) url.searchParams.set(k, String(v)); });
  let response;
  try { response = await fetch(url, { method, signal, headers: body ? { 'Content-Type': 'application/json' } : {}, body: body ? JSON.stringify(body) : undefined }); }
  catch (error) { if (error.name === 'AbortError') throw error; throw new ApiError({}); }
  if (response.status === 204) return undefined;
  const data = response.headers.get('content-type')?.includes('json') ? await response.json() : null;
  if (!response.ok) throw new ApiError({ status: response.status, code: data?.code ?? 'HTTP_ERROR', message: data?.message ?? '서버 오류가 발생했습니다.', details: data?.details ?? null });
  return data;
}
```

- [ ] **Step 4: 테스트를 통과시키고 커밋한다**

Run: `npm test -- tests/unit/api/client.test.js`  
Expected: PASS.  
Commit: `git add src/api tests/unit/api && git commit -m "feat: 공통 API 클라이언트 추가"`

### Task 3: 라우터 생명주기

**Files:**
- Create: `src/router/router.js`
- Test: `tests/unit/router/router.test.js`

**Interfaces:**
- Consumes: `matchRoute(pathname)`
- Produces: `createRouter({ routes, outlet, onNotFound })`, `navigate(to, { replace })`

- [ ] **Step 1: 이전 화면 정리와 링크 이동 테스트를 작성한다**

```js
import { expect, it, vi } from 'vitest';
import { createRouter } from '../../../src/router/router.js';
it('재렌더 전에 cleanup과 abort를 수행한다', () => {
  history.replaceState({}, '', '/'); const cleanup = vi.fn();
  const router = createRouter({ routes: { ranking: vi.fn(() => cleanup), posts: vi.fn(() => vi.fn()) }, outlet: document.body });
  router.start(); router.navigate('/posts');
  expect(cleanup).toHaveBeenCalledOnce();
  router.stop();
});
```

- [ ] **Step 2: 실패를 확인한다**

Run: `npm test -- tests/unit/router/router.test.js`  
Expected: FAIL because `router.js` is missing.

- [ ] **Step 3: start/render/navigate/stop을 구현한다**

Implement one active `{ controller, cleanup }`; `render()` aborts and cleans it, calls `matchRoute`, creates `{ outlet, params, query: new URLSearchParams(location.search), signal, navigate }`, and stores the returned cleanup. `navigate()` uses `pushState` or `replaceState`, then renders. Intercept only unmodified left-clicks on same-origin `<a>` elements; listen to `popstate`.

- [ ] **Step 4: 생명주기 테스트를 통과시키고 커밋한다**

Run: `npm test -- tests/unit/router`  
Expected: all router tests PASS.  
Commit: `git add src/router/router.js tests/unit/router/router.test.js && git commit -m "feat: History API 라우터 구현"`

### Task 4: 공통 UI와 접근성

**Files:**
- Create: `src/ui/async-state.js`, `src/ui/modal.js`, `src/ui/pagination.js`
- Test: `tests/unit/ui/common-ui.test.js`

**Interfaces:**
- Produces: `renderAsyncState`, `openModal`, `renderPagination`

- [ ] **Step 1: 오류 재시도·페이지 경계·모달 포커스 테스트를 작성한다**

Test that error text has `role="alert"`, retry invokes `onRetry`, page 1 disables previous, `totalPages=0` renders nothing, modal focuses its first input, Escape closes it, and focus returns to `trigger`.

- [ ] **Step 2: 실패를 확인한다**

Run: `npm test -- tests/unit/ui/common-ui.test.js`  
Expected: FAIL because UI modules are missing.

- [ ] **Step 3: DOM 생성만 담당하는 세 모듈을 구현한다**

Use `textContent` for messages; return cleanup functions for attached listeners. `openModal` uses `<dialog>`, traps Tab between focusable descendants, and calls `onConfirm` without closing when it returns `false`. `renderPagination` emits previous/next buttons and `페이지 X / Y` text and calls `onPageChange` only inside `[1, totalPages]`.

- [ ] **Step 4: UI 테스트를 통과시키고 커밋한다**

Run: `npm test -- tests/unit/ui/common-ui.test.js`  
Expected: PASS.  
Commit: `git add src/ui tests/unit/ui && git commit -m "feat: 접근 가능한 공통 UI 추가"`

### Task 5: 앱 셸과 디자인 시스템

**Files:**
- Create: `src/main.js`, `src/app/app.js`, `src/app/layout.js`
- Create: `src/styles/tokens.css`, `src/styles/global.css`, `src/styles/components.css`
- Modify: `index.html`
- Test: `tests/unit/app/layout.test.js`

**Interfaces:**
- Produces: `startApp({ root })`, `renderLayout(root) -> { outlet, chatRoot }`

- [ ] **Step 1: 앱 셸 구조 테스트를 작성한다**

Assert service name, `/` and `/posts` links, `<main id="route-outlet">`, `#chat-root`, and footer text `한국관광공사 TourAPI 제공 · 공공누리 제3유형`.

- [ ] **Step 2: 테스트 실패를 확인한다**

Run: `npm test -- tests/unit/app/layout.test.js`  
Expected: FAIL because layout is missing.

- [ ] **Step 3: 앱 셸과 B안 스타일을 구현한다**

Use CSS variables `--color-bg:#f7f8fb`, `--color-surface:#fff`, `--color-primary:#315cfd`, `--color-text:#131722`; max content width `72rem`; visible focus ring; responsive header and no fixed pixel content width. Register temporary route renderers with route title and later plans replace them.

- [ ] **Step 4: DOM 테스트와 전체 빌드를 확인하고 커밋한다**

Run: `npm test && npm run build`  
Expected: all unit tests PASS and build succeeds.  
Commit: `git add index.html src/main.js src/app src/styles tests/unit/app && git commit -m "feat: 앱 셸과 시티 가이드 디자인 적용"`

### Task 6: Netlify와 브라우저 기준선

**Files:**
- Create: `netlify.toml`, `playwright.config.js`, `tests/e2e/navigation.spec.js`

**Interfaces:**
- Consumes: production build and five SPA routes

- [ ] **Step 1: 직접 접근·모바일 overflow E2E를 작성한다**

```js
import { expect, test } from '@playwright/test';
for (const path of ['/', '/posts', '/posts/new', '/posts/12', '/posts/12/edit']) {
  test(`${path} 직접 접근`, async ({ page }) => { await page.goto(path); await expect(page.locator('main')).toBeVisible(); });
}
test('360px에서 가로 스크롤이 없다', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 }); await page.goto('/');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
```

- [ ] **Step 2: 실패를 확인한다**

Run: `npx playwright install chromium && npm run test:e2e -- tests/e2e/navigation.spec.js`  
Expected: FAIL until Playwright webServer and SPA fallback are configured.

- [ ] **Step 3: 배포·E2E 설정을 구현한다**

Set Playwright `webServer.command` to `npm run dev -- --host 127.0.0.1 --port 4173`, `baseURL` to `http://127.0.0.1:4173`, and use Chromium. In `netlify.toml`, set build command `npm run build`, publish `dist`, and redirect `/*` to `/index.html` with status `200`.

- [ ] **Step 4: 전체 검증과 커밋을 수행한다**

Run: `npm test && npm run build && npm run test:e2e`  
Expected: all unit/E2E tests PASS and build succeeds.  
Commit: `git add netlify.toml playwright.config.js tests/e2e/navigation.spec.js && git commit -m "chore: Netlify와 E2E 기반 추가"`
