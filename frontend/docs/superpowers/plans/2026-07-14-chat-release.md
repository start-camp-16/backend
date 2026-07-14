# 뭐할구 프론트엔드 4단계: 챗봇과 출시 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 모든 라우트에서 유지되는 메모리 기반 챗봇과 근거·오류 복구를 구현하고 전체 MVP 출시 검증을 끝낸다.

**Architecture:** 앱 셸에 한 번 마운트한 controller가 state와 요청을 소유한다. view는 데스크톱 패널/모바일 오버레이를 담당하고 source renderer는 discriminator별 출력만 담당한다.

**Tech Stack:** 기존 Vite/Vanilla JS 기반, Vitest/jsdom, Playwright, Netlify

## Global Constraints

- 사용자 메시지는 trim 후 1~1,000자다.
- API history는 이전 성공 메시지 중 최근 10개이며 현재 메시지를 중복하지 않는다.
- 대화는 메모리에만 두고 새로고침 시 초기화한다.
- 장소 근거는 정보만, 게시글 근거는 `/posts/:id` 링크로 표시한다.
- 모바일 360px에서는 전체 화면 오버레이와 focus trap을 제공한다.

---

### Task 1: 채팅 상태·history·API 계약

**Files:** Create `src/features/chat/chat-state.js`, `chat-api.js`; Test `tests/unit/chat/chat-data.test.js`

**Interfaces:** Produces `createChatState()`, `toChatHistory(messages)`, `sendChat({ message, history }, { signal })`

- [ ] **Step 1: history와 요청 테스트를 작성한다**

```js
import { expect, it } from 'vitest';
import { toChatHistory } from '../../../src/features/chat/chat-state.js';
it('성공한 최근 10개만 보낸다', () => {
  const messages = Array.from({ length: 12 }, (_, i) => ({ role: i % 2 ? 'assistant' : 'user', content: String(i), status: i === 3 ? 'failed' : 'sent' }));
  const history = toChatHistory(messages);
  expect(history).toHaveLength(10); expect(history.some(x => x.content === '3')).toBe(false);
  expect(history.every(({ role, content }) => role && content)).toBe(true);
});
```

Mock `request`; assert `sendChat` posts exactly `{ message, history }` to `/api/chat` with `signal`.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/chat/chat-data.test.js`  
Expected: FAIL because chat modules are missing.

- [ ] **Step 3: 메모리 state와 adapter를 구현한다**

State is `{ isOpen:false, messages:[], isSending:false, error:null }`; no storage calls. `toChatHistory` filters `status === 'sent'`, maps only role/content, then slices `-10`.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/chat/chat-data.test.js`  
Expected: PASS.  
Commit: `git add src/features/chat tests/unit/chat/chat-data.test.js && git commit -m "feat: 챗봇 상태와 API 계약 추가"`

### Task 2: 근거 renderer와 안전한 메시지 뷰

**Files:** Create `chat-sources.js`, `chat-view.js`, `chat.css`; Test `tests/unit/chat/chat-view.test.js`

**Interfaces:** Produces `renderChatSources(container, sources)`, `renderChat(container, state, handlers)`

- [ ] **Step 1: discriminator와 XSS 테스트를 작성한다**

Render a location, post, unknown type, and title `<img onerror=...>`. Assert location has no anchor, post href is `/posts/7`, unknown is omitted, and no `<img>` exists. Assert button has `aria-expanded`, dialog label, connected textarea label, status live region.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/chat/chat-view.test.js`  
Expected: FAIL because chat view modules are missing.

- [ ] **Step 3: DOM renderer와 반응형 CSS를 구현한다**

Use `textContent`. Location fields: title/category/district and address only when present. Post fields: title/tag inside same-origin anchor. At `max-width: 600px`, panel uses `position:fixed; inset:0`; desktop uses bottom-right bounded panel. Use `100dvh`, safe-area padding, visible focus.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/chat/chat-view.test.js`  
Expected: PASS.  
Commit: `git add src/features/chat/chat-sources.js src/features/chat/chat-view.js src/features/chat/chat.css tests/unit/chat/chat-view.test.js && git commit -m "feat: 챗봇 메시지와 근거 뷰 추가"`

### Task 3: controller·검증·라우트 간 유지

**Files:** Create `chat-controller.js`; Modify `src/app/app.js`; Test `tests/unit/chat/chat-controller.test.js`

**Interfaces:** Produces `mountChat({ container }) -> cleanup`

- [ ] **Step 1: 전송·중복 방지·유지 테스트를 작성한다**

Assert blank/1001 text is rejected; Enter sends and Shift+Enter does not; second submit while pending is ignored; request history excludes current message; success appends assistant/sources; re-render caused by navigation leaves the same controller state.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/chat/chat-controller.test.js`  
Expected: FAIL because controller is missing.

- [ ] **Step 3: 앱 수명 controller를 구현한다**

Mount once after `renderLayout`; do not mount from route renderers. Read and trim textarea on submit, append one pending user entry, call `sendChat`, then mark sent and append assistant. Close does not abort; cleanup aborts. Disable input/button during send.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/chat`  
Expected: all chat unit tests PASS.  
Commit: `git add src/features/chat/chat-controller.js src/app/app.js tests/unit/chat/chat-controller.test.js && git commit -m "feat: 전역 챗봇 흐름 구현"`

### Task 4: 오류별 재시도와 focus 관리

**Files:** Modify `chat-controller.js`, `chat-view.js`; Test `tests/unit/chat/chat-errors-accessibility.test.js`

**Interfaces:** Consumes `ApiError.code`; retry updates the existing failed message

- [ ] **Step 1: 오류·재시도·포커스 테스트를 작성한다**

Assert exact Korean messages for `CHAT_RATE_LIMITED` and `CHAT_PROVIDER_ERROR`; retry does not duplicate user text and excludes failed entry from history; opening focuses textarea, Tab stays inside, Escape closes, close returns focus to floating trigger, background is inert while open.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/chat/chat-errors-accessibility.test.js`  
Expected: FAIL for missing retry/focus behavior.

- [ ] **Step 3: 기존 항목 기반 재시도와 focus trap을 구현한다**

Store no password or server internals. Failed entry gets `{ status:'failed', errorCode }`; retry changes it to pending, calls API with the same content, then replaces status without pushing another user message. Use common focus utilities or the same algorithm as modal.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/chat`  
Expected: all chat tests PASS.  
Commit: `git add src/features/chat tests/unit/chat/chat-errors-accessibility.test.js && git commit -m "feat: 챗봇 오류 복구와 접근성 완성"`

### Task 5: 챗봇 및 전체 MVP E2E

**Files:** Create `tests/e2e/chat.spec.js`; Modify `tests/e2e/navigation.spec.js`

**Interfaces:** Consumes `/api/chat` and all route renderers

- [ ] **Step 1: chat API mock E2E를 작성한다**

Cover answer plus location/post sources, route navigation preserving conversation, reload clearing it, rate-limit→retry, provider-error→retry, Enter/Shift+Enter, duplicate send, desktop panel, 360×800 full-screen overlay, keyboard focus and no overflow.

- [ ] **Step 2: 전체 E2E를 실행해 integration gap을 확인한다**

Run: `npm run test:e2e`  
Expected: FAIL only where chat or cross-feature integration is incomplete.

- [ ] **Step 3: integration gap만 수정한다**

Keep mount lifetime at app level, history max 10, location without link, and post same-origin navigation. Fix only selectors, focus, lifecycle, or responsive CSS identified by tests.

- [ ] **Step 4: E2E 통과와 커밋**

Run: `npm run test:e2e`  
Expected: ranking, board/comments, chat, navigation suites all PASS.  
Commit: `git add src/features/chat tests/e2e && git commit -m "test: 챗봇과 전체 사용자 흐름 검증"`

### Task 6: 출시 문서와 최종 게이트

**Files:** Create `README.md`; Modify `.env.example`, `netlify.toml` only if verification exposes mismatch

**Interfaces:** Produces setup, test, build, Netlify environment instructions

- [ ] **Step 1: README 인수 기준을 먼저 작성한다**

Document Node/npm prerequisite, `npm install`, `.env.example` copy, `VITE_API_BASE_URL`, `npm run dev/test/test:e2e/build`, Netlify build `npm run build`, publish `dist`, and no frontend OpenAI key.

- [ ] **Step 2: 비밀값·고정 URL·스토리지 사용을 검사한다**

Run: `rg -n "(sk-[A-Za-z0-9_-]+|api[_-]?key|localStorage|sessionStorage|indexedDB|https?://)" src .env.example README.md netlify.toml`  
Expected: no secret; storage APIs absent; only documented localhost/example URLs are reviewed and intentional.

- [ ] **Step 3: 전체 자동 검증을 수행한다**

Run: `npm test && npm run build && npm run test:e2e`  
Expected: all unit tests and four E2E suites PASS; production build succeeds.

- [ ] **Step 4: 수동 반응형·접근성 체크를 기록한다**

At 1280×800 and 360×800 verify navigation, ranking, board CRUD, comments, chat overlay, focus return, text loading/error, footer attribution, direct-route refresh. Record the checked items in the release commit body.

- [ ] **Step 5: 출시 준비를 커밋한다**

Commit: `git add README.md .env.example netlify.toml && git commit -m "docs: 프론트엔드 실행과 배포 안내 추가"`

