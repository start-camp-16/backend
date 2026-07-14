import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

function markerIcon(active = false) {
  return L.divIcon({
    className: `ranking-marker${active ? ' ranking-marker--active' : ''}`,
    html: '<span aria-hidden="true"></span>',
    iconSize: active ? [34, 42] : [26, 34],
    iconAnchor: active ? [17, 42] : [13, 34],
    popupAnchor: [0, active ? -38 : -30],
  });
}

export function createLeafletAdapter(container, { onTileError = () => {} } = {}) {
  const map = L.map(container, { zoomControl: false, attributionControl: true });
  L.control.zoom({ position:'topright' }).addTo(map);
  let tileLayer;
  const markers = new Set();

  function addTiles() {
    tileLayer = L.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 19 });
    tileLayer.on('tileerror', onTileError);
    tileLayer.addTo(map);
  }
  addTiles();

  return {
    addMarker(item, coordinate, onClick) {
      const marker = L.marker(coordinate, { icon: markerIcon(false), title: `${item.rank}위 ${item.title}` });
      const popup = document.createElement('div');
      const title = document.createElement('strong'); title.textContent = `${item.rank}위 · ${item.title}`; popup.append(title);
      if (item.address) { const address = document.createElement('p'); address.textContent = item.address; popup.append(address); }
      marker.bindPopup(popup); marker.on('click', onClick); marker.addTo(map); markers.add(marker); return marker;
    },
    clearMarkers() { markers.forEach(marker => map.removeLayer(marker)); markers.clear(); },
    setView(coordinate, zoom, options) { map.setView(coordinate, zoom, options); },
    fitBounds(coordinates) {
      const desktopPanelPadding = container.clientWidth > 720
        ? Math.min(440, Math.round(container.clientWidth * .42))
        : 36;
      map.fitBounds(coordinates, {
        paddingTopLeft:[desktopPanelPadding, 36],
        paddingBottomRight:[36, 36],
        maxZoom:15,
      });
    },
    selectMarker(marker, active) { marker.setIcon(markerIcon(active)); marker.setZIndexOffset(active ? 1000 : 0); },
    openPopup(marker) { marker.openPopup(); },
    invalidateSize() { map.invalidateSize(); },
    retryTiles() { if (tileLayer) { tileLayer.off(); map.removeLayer(tileLayer); } addTiles(); },
    destroy() { markers.clear(); map.remove(); },
  };
}
