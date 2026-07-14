import { expect, it, vi } from 'vitest';
import { renderRankingItems } from '../../../src/features/ranking/ranking-view.js';

const items = [
  { content_id:'1', rank:1, title:'좌표 장소', address:'서울', phone:null, image_url:null, thumbnail_url:null, latitude:37.5, longitude:127 },
  { content_id:'2', rank:2, title:'좌표 없는 장소', address:null, phone:null, image_url:null, thumbnail_url:null, latitude:null, longitude:null },
];

it('랭킹 항목을 키보드로 선택 가능한 버튼으로 렌더링한다', () => {
  const onSelect = vi.fn();
  renderRankingItems(document.body, items, { selectedId:'1', onSelect });
  const cards = document.querySelectorAll('.place-card');
  expect(cards[0].tagName).toBe('BUTTON');
  expect(cards[0].getAttribute('aria-current')).toBe('true');
  expect(cards[0].dataset.contentId).toBe('1');
  cards[1].click();
  expect(onSelect).toHaveBeenCalledWith('2');
  expect(cards[1].textContent).toContain('지도 위치 없음');
});
