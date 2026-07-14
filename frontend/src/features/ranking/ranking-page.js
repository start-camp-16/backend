import { getCategories, getDistricts, getRankings } from './ranking-api.js';
import { parseRankingQuery, toRankingQuery } from './ranking-state.js';
import { renderRankingItems } from './ranking-view.js';
import { createRankingMap } from './ranking-map.js';
import { createLeafletAdapter } from './ranking-map-adapter.js';
import { renderAsyncState } from '../../ui/async-state.js';
import { renderPagination } from '../../ui/pagination.js';
import './ranking.css';

export function mountRankingPage(
  { outlet, query, signal, navigate },
  { mapFactory = createRankingMap, adapterFactory = createLeafletAdapter } = {},
) {
  const state = parseRankingQuery(query);
  let currentItems = [];
  let selectedId = null;

  outlet.innerHTML = `<section class="ranking-hero"><p class="eyebrow">Seoul city guide</p><h1 class="page-title">서울의 즐거움,<br><span>빠르게 찾아봐요.</span></h1><p class="lede">지역과 카테고리를 선택하면 지금 둘러볼 장소를 순서대로 보여드려요.</p></section><section class="ranking-workspace panel"><form class="ranking-filter"><label>어느 구에서?<select name="district" disabled><option value="">구 선택</option></select></label><label>무엇을 할까요?<select name="category" disabled><option value="">카테고리 선택</option></select></label><button disabled>장소 찾기</button></form><div class="ranking-explorer"><div id="ranking-map" class="ranking-map" role="region" aria-label="현재 랭킹 장소 지도"></div><div id="map-status" class="map-status" aria-live="polite"></div><section class="ranking-results-panel" aria-label="장소 랭킹 목록"><div id="ranking-status" aria-live="polite"></div><div id="ranking-results" class="place-grid"></div><div id="ranking-pagination"></div></section></div></section>`;

  const form = outlet.querySelector('form');
  const status = outlet.querySelector('#ranking-status');
  const mapStatus = outlet.querySelector('#map-status');
  const results = outlet.querySelector('#ranking-results');
  const pager = outlet.querySelector('#ranking-pagination');
  const mapContainer = outlet.querySelector('#ranking-map');
  const [districtSelect, categorySelect] = form.querySelectorAll('select');
  const submit = form.querySelector('button');
  let rankingMap;

  function renderTileError() {
    mapStatus.replaceChildren();
    const message = document.createElement('span'); message.textContent = '지도를 불러오지 못했습니다.';
    const retry = document.createElement('button'); retry.type = 'button'; retry.textContent = '지도 다시 시도';
    retry.addEventListener('click', () => { mapStatus.replaceChildren(); rankingMap.retryTiles(); });
    mapStatus.append(message, retry);
  }

  const adapter = mapFactory === createRankingMap
    ? adapterFactory(mapContainer, { onTileError: renderTileError })
    : undefined;
  rankingMap = mapFactory({ container: mapContainer, adapter, onSelect:id => selectItem(id, { source:'marker' }) });

  function renderItems() {
    renderRankingItems(results, currentItems, { selectedId, onSelect:id => selectItem(id, { source:'list' }) });
  }

  function selectItem(id, { source }) {
    selectedId = String(id);
    const item = currentItems.find(candidate => String(candidate.content_id) === selectedId);
    renderItems();
    const mapped = rankingMap.select(selectedId, { focus:source === 'list' });
    if (!mapped) mapStatus.textContent = '이 장소는 지도 위치 정보가 없습니다.';
    else mapStatus.textContent = `${item?.title ?? '장소'}을(를) 지도에서 선택했습니다.`;
    if (source === 'marker') {
      [...results.querySelectorAll('[data-content-id]')]
        .find(element => element.dataset.contentId === selectedId)
        ?.scrollIntoView({ block:'nearest' });
    }
  }

  function fill(select, items, value) {
    items.forEach(item => select.add(new Option(item, item)));
    if (items.includes(value)) select.value = value;
    select.disabled = false;
  }

  async function loadRankings() {
    if (!districtSelect.value || !categorySelect.value) return;
    renderAsyncState(status, { kind:'loading', message:'장소를 찾고 있습니다…' });
    results.replaceChildren(); pager.replaceChildren(); mapStatus.replaceChildren(); rankingMap.setItems([]);
    try {
      const data = await getRankings({ district:districtSelect.value, category:categorySelect.value, page:state.page, signal });
      status.replaceChildren(); currentItems = data.items; selectedId = null;
      if (!data.items.length) {
        renderAsyncState(status, { kind:'empty', message:'선택 조건에 해당하는 장소가 없습니다.' });
        mapStatus.textContent = '현재 결과에는 표시할 위치 정보가 없습니다.';
        return;
      }
      renderItems();
      const markerCount = rankingMap.setItems(data.items);
      if (!markerCount) mapStatus.textContent = '현재 결과에는 표시할 위치 정보가 없습니다.';
      queueMicrotask(() => rankingMap.invalidateSize());
      renderPagination(pager, {
        page:data.pagination.page,
        totalPages:data.pagination.total_pages,
        onPageChange:page => navigate(`/?${toRankingQuery({ district:districtSelect.value, category:categorySelect.value, page })}`),
      });
    } catch (error) {
      if (error.name !== 'AbortError') renderAsyncState(status, { kind:'error', message:error.message, onRetry:loadRankings });
    }
  }

  async function loadMeta() {
    renderAsyncState(status, { kind:'loading', message:'지역과 카테고리를 불러오고 있습니다…' });
    try {
      const [districts, categories] = await Promise.all([getDistricts({ signal }), getCategories({ signal })]);
      fill(districtSelect, districts, state.district); fill(categorySelect, categories, state.category);
      submit.disabled = false; status.replaceChildren();
      if (districtSelect.value && categorySelect.value) await loadRankings();
    } catch (error) {
      if (error.name !== 'AbortError') renderAsyncState(status, { kind:'error', message:error.message, onRetry:loadMeta });
    }
  }

  function onSubmit(event) {
    event.preventDefault();
    if (!districtSelect.value || !categorySelect.value) {
      renderAsyncState(status, { kind:'error', message:'구와 카테고리를 모두 선택해 주세요.' }); return;
    }
    navigate(`/?${toRankingQuery({ district:districtSelect.value, category:categorySelect.value, page:1 })}`);
  }

  form.addEventListener('submit', onSubmit);
  loadMeta();
  return () => { form.removeEventListener('submit', onSubmit); rankingMap.destroy(); };
}
