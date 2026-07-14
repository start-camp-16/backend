import { describe, expect, it, vi } from 'vitest';
import { createRankingMap, toCoordinate } from '../../../src/features/ranking/ranking-map.js';

describe('toCoordinate', () => {
  it('유효한 좌표를 Leaflet 순서로 반환한다', () => {
    expect(toCoordinate({ latitude: 37.5665, longitude: 126.978 })).toEqual([37.5665, 126.978]);
  });

  it.each([
    { latitude: null, longitude: 126.9 },
    { latitude: '37.5', longitude: 126.9 },
    { latitude: 91, longitude: 126.9 },
    { latitude: 37.5, longitude: 181 },
  ])('유효하지 않은 좌표 $latitude, $longitude를 제외한다', item => {
    expect(toCoordinate(item)).toBeNull();
  });
});

function fakeAdapter() {
  return {
    addMarker: vi.fn((item, coordinate, onClick) => ({ id:String(item.content_id), coordinate, onClick })),
    clearMarkers: vi.fn(),
    setView: vi.fn(),
    fitBounds: vi.fn(),
    selectMarker: vi.fn(),
    openPopup: vi.fn(),
    invalidateSize: vi.fn(),
    retryTiles: vi.fn(),
    destroy: vi.fn(),
  };
}

describe('createRankingMap', () => {
  it('마커 수에 따라 빈 상태, 단일 중심, bounds를 선택한다', () => {
    const adapter = fakeAdapter();
    const map = createRankingMap({ container:document.body, adapter });
    expect(map.setItems([{ content_id:'x', latitude:null, longitude:null }])).toBe(0);
    map.setItems([{ content_id:'1', latitude:37.5, longitude:127 }]);
    expect(adapter.setView).toHaveBeenCalledWith([37.5, 127], 14);
    map.setItems([{ content_id:'1', latitude:37.5, longitude:127 }, { content_id:'2', latitude:37.6, longitude:127.1 }]);
    expect(adapter.fitBounds).toHaveBeenCalledWith([[37.5,127],[37.6,127.1]]);
    expect(adapter.clearMarkers).toHaveBeenCalledTimes(3);
  });

  it('마커 클릭과 선택을 content_id로 동기화하고 정리한다', () => {
    const adapter = fakeAdapter(); const onSelect = vi.fn();
    const map = createRankingMap({ container:document.body, adapter, onSelect });
    map.setItems([{ content_id:'7', title:'장소', latitude:37.5, longitude:127 }]);
    adapter.addMarker.mock.results[0].value.onClick();
    expect(onSelect).toHaveBeenCalledWith('7');
    expect(map.select('7')).toBe(true);
    expect(adapter.selectMarker).toHaveBeenCalled(); expect(adapter.openPopup).toHaveBeenCalled();
    map.destroy(); expect(adapter.destroy).toHaveBeenCalledOnce();
  });
});
