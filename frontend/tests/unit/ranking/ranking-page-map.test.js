import { beforeEach, expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  getCategories: vi.fn(), getDistricts: vi.fn(), getRankings: vi.fn(),
}));
vi.mock('../../../src/features/ranking/ranking-api.js', () => api);

import { mountRankingPage } from '../../../src/features/ranking/ranking-page.js';

const items = [
  { content_id:'1', rank:1, title:'지도 장소', address:'서울', phone:null, image_url:null, thumbnail_url:null, latitude:37.5, longitude:127 },
  { content_id:'2', rank:2, title:'좌표 없음', address:null, phone:null, image_url:null, thumbnail_url:null, latitude:null, longitude:null },
];

beforeEach(() => {
  api.getCategories.mockResolvedValue(['문화시설']);
  api.getDistricts.mockResolvedValue(['마포구']);
  api.getRankings.mockResolvedValue({ items, pagination:{ page:1, total_pages:1 } });
  Element.prototype.scrollIntoView = vi.fn();
});

it('목록과 마커 선택을 같은 content_id로 동기화한다', async () => {
  const map = { setItems:vi.fn(() => 1), select:vi.fn(id => id === '1'), destroy:vi.fn(), invalidateSize:vi.fn(), retryTiles:vi.fn() };
  let markerSelect;
  const mapFactory = vi.fn(({ onSelect }) => { markerSelect = onSelect; return map; });
  const outlet = document.body.appendChild(document.createElement('main'));
  const cleanup = mountRankingPage({
    outlet,
    query:new URLSearchParams('district=마포구&category=문화시설'),
    signal:new AbortController().signal,
    navigate:vi.fn(),
  }, { mapFactory });

  await vi.waitFor(() => expect(map.setItems).toHaveBeenCalledWith(items));
  outlet.querySelector('[data-content-id="1"]').click();
  expect(map.select).toHaveBeenCalledWith('1', { focus:true });
  expect(outlet.querySelector('[data-content-id="1"]').getAttribute('aria-current')).toBe('true');

  markerSelect('1');
  expect(map.select).toHaveBeenLastCalledWith('1', { focus:false });
  expect(Element.prototype.scrollIntoView).toHaveBeenCalledWith({ block:'nearest' });

  outlet.querySelector('[data-content-id="2"]').click();
  expect(outlet.querySelector('#map-status').textContent).toContain('지도 위치 정보가 없습니다');
  cleanup();
  expect(map.destroy).toHaveBeenCalledOnce();
});
