# 뭐할구 랭킹 지도 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 현재 랭킹 페이지의 장소를 Leaflet·OpenStreetMap 지도에 표시하고 목록과 마커 선택을 양방향 동기화한다.

**Architecture:** Leaflet 직접 호출은 `ranking-map-adapter.js`에 격리하고 `ranking-map.js`가 좌표 검증, 마커 수명주기, 선택 상태를 관리한다. `ranking-page.js`는 랭킹 응답과 선택된 `content_id`를 조정하며 `ranking-view.js`는 키보드로 선택 가능한 목록 DOM만 담당한다.

**Tech Stack:** Vite, Vanilla JavaScript, Leaflet, OpenStreetMap, Vitest/jsdom, Playwright

## Global Constraints

- 지도 제공자는 `Leaflet + OpenStreetMap`이며 API 키를 사용하지 않는다.
- OpenStreetMap attribution은 항상 표시한다.
- 현재 페이지의 유효 좌표 장소를 모두 마커로 표시한다.
- 좌표 없는 장소는 목록에서 제거하지 않는다.
- 데스크톱은 지도 위 플로팅 목록, 720px 이하는 지도 위·목록 아래 배치다.
- 목록과 마커는 `content_id` 기준으로 양방향 선택을 동기화한다.
- 외부 타일 네트워크 상태가 자동 테스트 결과를 바꾸지 않아야 한다.

---

### Task 1: Leaflet 의존성과 좌표 계약

**Files:**
- Modify: `package.json`, `package-lock.json`
- Create: `src/features/ranking/ranking-map.js`
- Test: `tests/unit/ranking/ranking-map.test.js`

**Interfaces:**
- Produces: `toCoordinate(item) -> [latitude, longitude] | null`

- [ ] **Step 1: Leaflet 패키지를 설치한다**

Run: `npm install leaflet`

Expected: `leaflet` is in dependencies and lockfile is updated.

- [ ] **Step 2: 좌표 범위 실패 테스트를 작성한다**

```js
import { describe, expect, it } from 'vitest';
import { toCoordinate } from '../../../src/features/ranking/ranking-map.js';

describe('toCoordinate', () => {
  it('유효한 좌표를 Leaflet 순서로 반환한다', () => {
    expect(toCoordinate({ latitude: 37.5665, longitude: 126.978 })).toEqual([37.5665, 126.978]);
  });

  it.each([
    [{ latitude: null, longitude: 126.9 }],
    [{ latitude: '37.5', longitude: 126.9 }],
    [{ latitude: 91, longitude: 126.9 }],
    [{ latitude: 37.5, longitude: 181 }],
  ])('유효하지 않은 좌표 %o를 제외한다', item => {
    expect(toCoordinate(item)).toBeNull();
  });
});
```

- [ ] **Step 3: RED를 확인한다**

Run: `npm test -- tests/unit/ranking/ranking-map.test.js`

Expected: FAIL because `ranking-map.js` does not exist.

- [ ] **Step 4: 좌표 변환을 최소 구현한다**

```js
export function toCoordinate({ latitude, longitude }) {
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;
  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) return null;
  return [latitude, longitude];
}
```

- [ ] **Step 5: GREEN과 전체 단위 테스트를 확인한다**

Run: `npm test -- tests/unit/ranking/ranking-map.test.js`

Expected: coordinate tests PASS.

### Task 2: Leaflet adapter와 지도 수명주기

**Files:**
- Create: `src/features/ranking/ranking-map-adapter.js`
- Modify: `src/features/ranking/ranking-map.js`
- Test: `tests/unit/ranking/ranking-map.test.js`

**Interfaces:**
- Produces: `createLeafletAdapter(container, options)`
- Produces: `createRankingMap({ container, onSelect, adapter }) -> { setItems, select, invalidateSize, retryTiles, destroy }`

- [ ] **Step 1: 마커 0·1·복수와 정리 테스트를 추가한다**

Use a fake adapter recording `addMarker`, `clearMarkers`, `setView`, `fitBounds`, `selectMarker`, `openPopup`, and `destroy`. Assert zero coordinates emits empty state without marker calls; one coordinate calls `setView`; multiple call `fitBounds`; second `setItems` clears prior markers; `destroy` delegates once.

- [ ] **Step 2: RED를 확인한다**

Run: `npm test -- tests/unit/ranking/ranking-map.test.js`

Expected: FAIL because `createRankingMap` is missing.

- [ ] **Step 3: adapter 경계를 구현한다**

`createLeafletAdapter` creates `L.map`, `L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')`, zoom controls, and attribution `&copy; OpenStreetMap contributors`. It exposes marker creation with default/active `L.divIcon`, tile error callback, popup, bounds, size invalidation, layer clearing, and `map.remove()`.

- [ ] **Step 4: 지도 controller를 최소 구현한다**

Store items and marker handles in Maps keyed by `String(content_id)`. `setItems` clears, filters through `toCoordinate`, registers marker click to `onSelect(id)`, and chooses empty/setView/fitBounds. `select` resets the prior marker, activates the next, optionally centers, and opens its popup. `destroy` clears state and calls adapter destroy once.

- [ ] **Step 5: GREEN을 확인한다**

Run: `npm test -- tests/unit/ranking/ranking-map.test.js`

Expected: all ranking map unit tests PASS.

### Task 3: 선택 가능한 랭킹 목록

**Files:**
- Modify: `src/features/ranking/ranking-view.js`
- Test: `tests/unit/ranking/ranking-view.test.js`

**Interfaces:**
- Changes: `renderRankingItems(container, items, { selectedId, onSelect })`

- [ ] **Step 1: 목록 선택·접근성 실패 테스트를 작성한다**

Render one coordinate item and one coordinate-less item. Assert each card is a button with an accessible rank/title name; selected card has `aria-current="true"`; Enter/click calls `onSelect(content_id)`; coordinate-less card shows `지도 위치 없음`; item DOM has `data-content-id`.

- [ ] **Step 2: RED를 확인한다**

Run: `npm test -- tests/unit/ranking/ranking-view.test.js`

Expected: FAIL because the current cards are non-interactive articles.

- [ ] **Step 3: 목록 렌더러를 변경한다**

Create a `<button type="button" class="place-card panel">` per item, keep image fallback, address, phone, and rank. Set `data-content-id`, conditional `aria-current`, and click handler. Use `toCoordinate(item)` only to render the coordinate-less badge; never remove the item.

- [ ] **Step 4: GREEN과 기존 뷰 회귀를 확인한다**

Run: `npm test -- tests/unit/ranking/ranking-view.test.js tests/unit/features/views.test.js`

Expected: new and existing view tests PASS after adapting existing test calls to the optional options object.

### Task 4: 랭킹 페이지 양방향 선택과 C안 레이아웃

**Files:**
- Modify: `src/features/ranking/ranking-page.js`, `src/features/ranking/ranking.css`
- Test: `tests/unit/ranking/ranking-page-map.test.js`

**Interfaces:**
- Consumes: `createRankingMap`, extended `renderRankingItems`
- Changes: `mountRankingPage(context, { mapFactory = createRankingMap } = {}) -> cleanup`
- State: `selectedId: string | null`

- [ ] **Step 1: 목록→지도와 마커→목록 실패 테스트를 작성한다**

Inject a fake `mapFactory`. After a successful ranking response, assert `setItems(items)`; list click calls `map.select(id)` and re-renders `aria-current`; fake marker `onSelect(id)` activates the matching list item and calls its `scrollIntoView({ block:'nearest' })`; coordinate-less selection leaves map selection unchanged and announces the missing location.

- [ ] **Step 2: RED를 확인한다**

Run: `npm test -- tests/unit/ranking/ranking-page-map.test.js`

Expected: FAIL because page/map coordination is missing.

- [ ] **Step 3: page controller를 연결한다**

Create the map after rendering the shell, pass marker callback into the selection function, and destroy it in route cleanup. On every successful response reset `selectedId`, render items with selection callback, then call `map.setItems`. Marker selection reuses the same selection function with `{ source:'marker' }` to avoid duplicate center movement.

- [ ] **Step 4: C안 CSS를 구현한다**

Add `.ranking-explorer` as a positioned map canvas, `.ranking-map` filling the area, and `.ranking-results-panel` as a left floating panel with independent scrolling. At `max-width:720px`, change to grid flow with 320px map followed by unconstrained list. Style Leaflet markers with neutral and active variants, preserve attribution visibility, and respect reduced motion.

- [ ] **Step 5: GREEN과 랭킹 회귀를 확인한다**

Run: `npm test -- tests/unit/ranking`

Expected: all ranking tests PASS.

### Task 5: E2E와 시각 검증

**Files:**
- Create: `tests/e2e/ranking-map.spec.js`
- Modify: `tests/e2e/mvp.spec.js` only if shared mock extraction is needed

**Interfaces:**
- Verifies: ranking API coordinates, list/marker selection, page replacement, responsive layout

- [ ] **Step 1: deterministic map E2E를 작성한다**

Mock ranking responses with coordinates and tile requests with a local transparent image response. Assert marker count, list click active state and popup, marker click list `aria-current`, page navigation removes old marker labels, coordinate-less badge, and OSM attribution.

- [ ] **Step 2: 모바일 E2E를 추가한다**

At 360×800 assert map is before the list in visual flow, map height is about 320px, floating panel positioning is disabled, controls do not overlap attribution, and document horizontal overflow is absent.

- [ ] **Step 3: E2E의 RED를 확인한다**

Run: `npm run test:e2e -- tests/e2e/ranking-map.spec.js`

Expected: tests expose any integration gaps in marker selectors, tile mocks, or responsive CSS.

- [ ] **Step 4: integration gap만 수정한다**

Do not change the approved C layout, coordinate rules, or attribution. Apply only the minimal DOM hooks, focus, lifecycle, and CSS corrections proven by the E2E failures.

- [ ] **Step 5: 전체 검증을 수행한다**

Run: `npm test`

Expected: all unit/DOM tests PASS.

Run: `npm run build`

Expected: Vite production build succeeds with Leaflet assets.

Run: `npm run test:e2e`

Expected: existing MVP and new ranking map E2E tests PASS.

- [ ] **Step 6: 시각 QA 후 커밋한다**

Inspect 1280×800 and 360×800 in the in-app browser. Verify the floating list remains legible over real tiles, active marker/list are visually linked, attribution is unobstructed, and mobile flow matches the spec.

Commit: `git add package.json package-lock.json src/features/ranking tests/unit/ranking tests/e2e && git commit -m "feat: 랭킹 지도 탐색 추가"`
