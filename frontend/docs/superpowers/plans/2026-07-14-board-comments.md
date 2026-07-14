# 뭐할구 프론트엔드 3단계: 게시판과 댓글 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 게시글 목록·검색과 게시글/댓글 CRUD를 비밀번호 장기 저장 없이 구현한다.

**Architecture:** API adapter와 validation은 순수 모듈로 두고 각 라우트 controller가 view와 비동기 상태를 조정한다. 게시글 상세와 댓글은 독립 상태 영역을 유지한다.

**Tech Stack:** 기존 Vite/Vanilla JS 기반, Vitest/jsdom, Playwright

## Global Constraints

- 태그 순서는 `전체, 관광, 맛집, 문화, 행사, 숙박, 쇼핑, 자유`다.
- 게시글은 제목 1~100, 본문 1~5,000, 비밀번호 4~20자다.
- 댓글은 본문 1~1,000, 비밀번호 4~20자다.
- 비밀번호는 DOM 입력에서 요청 body로만 전달하며 URL·모듈 상태·Web Storage·로그에 복사하지 않는다.

---

### Task 1: API adapter와 검증 계약

**Files:** Create `src/features/board/board-api.js`, `board-constants.js`, `post-validation.js`, `comment-validation.js`; Test `tests/unit/board/contracts.test.js`

**Interfaces:** Produces all nine API functions from the design; `POST_TAGS`; `validatePost(values)`, `validateComment(values)` returning `{ field: message }`

- [ ] **Step 1: 경계값과 HTTP 계약 테스트를 작성한다**

Assert empty/101 title, empty/5001 content, 3/21 password fail and exact boundaries pass; comment 1000 passes and 1001 fails. Mock `request` and assert GET/POST/PUT/DELETE paths and bodies exactly match `shared/openapi.yaml`.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/board/contracts.test.js`  
Expected: FAIL because board modules are missing.

- [ ] **Step 3: 상수·순수 검증·API 함수를 구현한다**

Trim title/content before length validation; do not trim or return transformed password. API functions pass `signal`, use size 20 for lists, and return response data unchanged.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/board/contracts.test.js`  
Expected: PASS.  
Commit: `git add src/features/board tests/unit/board/contracts.test.js && git commit -m "feat: 게시판 API와 입력 계약 추가"`

### Task 2: 목록·태그·검색

**Files:** Create `board-list-page.js`, `board-list-view.js`, `board.css`; Modify `src/app/app.js`; Test `tests/unit/board/board-list.test.js`

**Interfaces:** Produces `mountBoardListPage(context)`, `parseBoardQuery`, `toBoardQuery`

- [ ] **Step 1: URL과 목록 테스트를 작성한다**

Assert invalid tag→전체, invalid page→1, blank submitted query removes `q`, tag+query coexist, response order is unchanged, title links to `/posts/{id}`, and all eight tabs render in the required order.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/board/board-list.test.js`  
Expected: FAIL because list modules are missing.

- [ ] **Step 3: 목록 controller/view를 구현한다**

Use URL as source of truth. Search input may differ until submit; submit trims it and navigates with page 1. Render loading/empty/error independently, format dates with `<time datetime>`, and preserve API order.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/board/board-list.test.js`  
Expected: PASS.  
Commit: `git add src/features/board src/app/app.js tests/unit/board/board-list.test.js && git commit -m "feat: 게시글 목록과 검색 구현"`

### Task 3: 게시글 생성·수정 폼

**Files:** Create `post-form-page.js`, `post-form-view.js`; Test `tests/unit/board/post-form.test.js`

**Interfaces:** Produces `mountPostFormPage(context)`, `renderPostForm(container, initialValues)`

- [ ] **Step 1: 생성·수정 테스트를 작성한다**

Assert invalid submit focuses first invalid field; server failure preserves all live DOM values; create success navigates using response `id`; edit loads tag/title/content but password remains empty; `PASSWORD_MISMATCH` is attached to password.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/board/post-form.test.js`  
Expected: FAIL because form modules are missing.

- [ ] **Step 3: 공유 폼과 mode별 controller를 구현한다**

Select create mode for `/posts/new`, edit for `/posts/:id/edit`. Read password only inside submit handler and pass directly to adapter. Do not replace the form on request failure. Disable submit during request and re-enable in `finally`.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/board/post-form.test.js`  
Expected: PASS.  
Commit: `git add src/features/board/post-form* tests/unit/board/post-form.test.js && git commit -m "feat: 게시글 작성과 수정 구현"`

### Task 4: 게시글 상세와 삭제

**Files:** Create `post-detail-page.js`, `post-detail-view.js`; Test `tests/unit/board/post-detail.test.js`

**Interfaces:** Produces `mountPostDetailPage(context)` and a `#comments-root` for Task 5

- [ ] **Step 1: 안전한 본문·시각·삭제 테스트를 작성한다**

Assert `<img onerror=...>` content remains text, updated time appears only when different, delete opens password modal, mismatch keeps it open, success navigates `/posts`, and not-found shows return link.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/board/post-detail.test.js`  
Expected: FAIL because detail modules are missing.

- [ ] **Step 3: 상세·삭제를 구현한다**

Fetch post, render with `textContent` and `white-space: pre-wrap`; use common modal for deletion. Read password on confirm and return `false` on failure so modal stays open. Abort on cleanup.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/board/post-detail.test.js`  
Expected: PASS.  
Commit: `git add src/features/board/post-detail* tests/unit/board/post-detail.test.js && git commit -m "feat: 게시글 상세와 삭제 구현"`

### Task 5: 댓글 CRUD

**Files:** Create `comments-controller.js`, `comments-view.js`; Modify `post-detail-page.js`; Test `tests/unit/board/comments.test.js`

**Interfaces:** Produces `mountComments({ root, postId, signal }) -> cleanup`

- [ ] **Step 1: 독립 상태와 CRUD 테스트를 작성한다**

Assert post and comments requests start together; comment failure leaves post visible; create/update/delete each refetch comments; only one edit form opens; mismatch stays in active form/modal; duplicate submit is blocked.

- [ ] **Step 2: 실패 확인**

Run: `npm test -- tests/unit/board/comments.test.js`  
Expected: FAIL because comment modules are missing.

- [ ] **Step 3: 댓글 영역을 구현한다**

Keep comment request controller separate from post request. Render API order unchanged. Clear create form only after success. Disable only the active operation. Refresh with `getComments(postId)` after every successful mutation.

- [ ] **Step 4: 통과 확인과 커밋**

Run: `npm test -- tests/unit/board`  
Expected: all board unit tests PASS.  
Commit: `git add src/features/board tests/unit/board/comments.test.js && git commit -m "feat: 댓글 CRUD 구현"`

### Task 6: 게시판 E2E

**Files:** Create `tests/e2e/board-comments.spec.js`

**Interfaces:** Consumes all Posts and Comments OpenAPI paths

- [ ] **Step 1: mock 기반 전체 사용자 흐름을 작성한다**

Cover tag+search+clear, pagination/back, post create/edit/mismatch/delete, comment create/edit/mismatch/delete, direct route refresh, server error retry, keyboard tabs/modal, and 360×800 overflow.

- [ ] **Step 2: 실패 지점을 확인한다**

Run: `npm run test:e2e -- tests/e2e/board-comments.spec.js`  
Expected: FAIL only for integration gaps.

- [ ] **Step 3: integration gap만 최소 수정한다**

Preserve API ordering, password isolation, and independent comment error state while fixing selectors/focus/CSS.

- [ ] **Step 4: 전체 검증과 커밋**

Run: `npm test && npm run build && npm run test:e2e -- tests/e2e/board-comments.spec.js`  
Expected: all commands PASS.  
Commit: `git add src/features/board tests/e2e/board-comments.spec.js && git commit -m "test: 게시글과 댓글 사용자 흐름 검증"`

