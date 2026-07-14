export function toCoordinate({ latitude, longitude }) {
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return null;
  if (latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) return null;
  return [latitude, longitude];
}

function prefersReducedMotion() {
  return globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

export function createRankingMap({ container, onSelect = () => {}, adapter }) {
  const markers = new Map();
  let selectedId = null;
  let destroyed = false;

  function setItems(items) {
    adapter.clearMarkers();
    markers.clear();
    selectedId = null;
    const coordinates = [];
    for (const item of items) {
      const coordinate = toCoordinate(item);
      if (!coordinate) continue;
      const id = String(item.content_id);
      const marker = adapter.addMarker(item, coordinate, () => onSelect(id));
      markers.set(id, { marker, item, coordinate });
      coordinates.push(coordinate);
    }
    if (coordinates.length === 1) adapter.setView(coordinates[0], 14);
    else if (coordinates.length > 1) adapter.fitBounds(coordinates);
    return coordinates.length;
  }

  function select(contentId, { focus = true } = {}) {
    const id = String(contentId);
    const next = markers.get(id);
    if (!next) return false;
    if (selectedId && markers.has(selectedId)) adapter.selectMarker(markers.get(selectedId).marker, false);
    selectedId = id;
    adapter.selectMarker(next.marker, true);
    if (focus) adapter.setView(next.coordinate, 15, { animate: !prefersReducedMotion() });
    adapter.openPopup(next.marker);
    return true;
  }

  return {
    setItems,
    select,
    invalidateSize: () => adapter.invalidateSize(),
    retryTiles: () => adapter.retryTiles(),
    destroy() {
      if (destroyed) return;
      destroyed = true;
      markers.clear();
      adapter.destroy();
    },
  };
}
