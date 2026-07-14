# Environment File and Feature README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the public API base URL example into a local ignored `.env`, remove `.env.example`, and rewrite the frontend README around product features and user flows.

**Architecture:** Keep runtime configuration local through the existing `.gitignore` rule for `.env`. Treat `README.md` as product-facing feature documentation, while leaving the already-deleted repository-root README and unrelated untracked directories untouched.

**Tech Stack:** Vite environment variables, Markdown, Git

## Global Constraints

- Local `.env` contains exactly `VITE_API_BASE_URL=http://localhost:8000`.
- `.env` remains ignored by Git and is never committed.
- `.env.example` is deleted.
- `README.md` contains only the service introduction, three core feature groups, and the main user flow.
- The repository-root `README.md` deletion and unrelated untracked directories remain untouched.

---

### Task 1: Move the environment example to the local file

**Files:**
- Create locally: `.env`
- Delete: `.env.example`
- Verify: `.gitignore`

**Interfaces:**
- Consumes: Vite's `VITE_API_BASE_URL` environment variable.
- Produces: A local API origin value available to the Vite development server.

- [ ] **Step 1: Create the local environment file**

Create `.env` with exactly:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

- [ ] **Step 2: Delete the tracked example file**

Delete `.env.example` without changing `.gitignore`.

- [ ] **Step 3: Verify local-only behavior**

Run:

```bash
test "$(sed -n '1p' .env)" = "VITE_API_BASE_URL=http://localhost:8000"
test ! -e .env.example
git check-ignore .env
```

Expected: all commands exit successfully and `git check-ignore` prints `.env`.

### Task 2: Rewrite the README around product features

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: Implemented ranking map, anonymous community, and grounded chatbot features.
- Produces: A concise product feature guide for readers.

- [ ] **Step 1: Replace the README content**

Use this structure and copy:

```markdown
# 뭐할구

서울의 구별 즐길 거리와 지역 정보를 한곳에서 탐색하는 서비스입니다.

## 장소 랭킹과 지도 탐색

- 구와 카테고리를 선택해 인기 장소 랭킹을 확인합니다.
- 랭킹 목록과 지도의 위치가 서로 연결되어 원하는 장소를 빠르게 찾을 수 있습니다.
- 위치 정보가 없는 장소도 목록에서 확인할 수 있습니다.

## 익명 게시판과 댓글

- 지역별 경험과 추천 정보를 익명 게시글로 공유합니다.
- 게시글에 댓글을 남기고 비밀번호로 자신의 글과 댓글을 관리합니다.
- 태그를 이용해 관심 있는 이야기를 모아볼 수 있습니다.

## 지역 정보 챗봇

- 자연어로 서울 지역과 장소에 관한 질문을 입력합니다.
- 답변과 함께 참고한 출처를 확인할 수 있습니다.
- 대화 기록을 초기화하고 새로운 질문을 이어갈 수 있습니다.

## 주요 사용 흐름

1. 구와 카테고리를 선택합니다.
2. 랭킹과 지도를 함께 보며 장소를 탐색합니다.
3. 지역 게시판에서 경험을 나누거나 댓글을 남깁니다.
4. 추가 정보가 필요하면 챗봇에 질문하고 출처를 확인합니다.
```

- [ ] **Step 2: Verify feature coverage and excluded setup content**

Run:

```bash
rg -n "장소 랭킹과 지도 탐색|익명 게시판과 댓글|지역 정보 챗봇|주요 사용 흐름" README.md
! rg -n "npm install|npm run|Netlify|Build command|Publish directory" README.md
```

Expected: each feature heading appears once and no setup/deployment text is found.

### Task 3: Validate and commit the tracked changes

**Files:**
- Delete: `.env.example`
- Modify: `README.md`
- Local-only: `.env`

**Interfaces:**
- Consumes: Outputs from Tasks 1 and 2.
- Produces: One documentation/configuration commit with no local secrets staged.

- [ ] **Step 1: Check the final tracked diff**

Run:

```bash
git diff --check
git status --short
git diff -- README.md .env.example
```

Expected: `.env.example` is deleted, `README.md` is modified, `.env` is absent from status, and unrelated user changes remain unstaged.

- [ ] **Step 2: Stage only the intended tracked files**

```bash
git add README.md .env.example
```

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: 기능 중심 README와 로컬 환경 설정 정리"
```
