import { expect, test } from '@playwright/test';

const transparentPng = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAF/gL+Xw7WAAAAAElFTkSuQmCC', 'base64');

async function mockMapApi(page) {
  await page.route('https://*.tile.openstreetmap.org/**', route => route.fulfill({ status:200, contentType:'image/png', body:transparentPng }));
  await page.route('**/api/meta/categories', route => route.fulfill({ json:{ items:['문화시설'] } }));
  await page.route('**/api/meta/districts', route => route.fulfill({ json:{ items:['마포구'] } }));
  await page.route('**/api/rankings**', route => route.fulfill({ json:{
    items:[
      { rank:1, content_id:'a', category:'문화시설', title:'문화비축기지', address:'서울 마포구', district:'마포구', longitude:126.893, latitude:37.571, image_url:null, thumbnail_url:null, phone:null, source_order:1 },
      { rank:2, content_id:'b', category:'문화시설', title:'서울생활문화센터', address:'서울 마포구', district:'마포구', longitude:126.918, latitude:37.555, image_url:null, thumbnail_url:null, phone:null, source_order:2 },
      { rank:3, content_id:'c', category:'문화시설', title:'좌표 없는 장소', address:null, district:'마포구', longitude:null, latitude:null, image_url:null, thumbnail_url:null, phone:null, source_order:3 },
    ],
    pagination:{ page:1,size:20,total_items:3,total_pages:1 },
  } }));
}

test.beforeEach(async ({ page }) => { await mockMapApi(page); });

test('전체 마커와 목록 선택을 양방향 동기화한다', async ({ page }) => {
  await page.goto('/?district=마포구&category=문화시설');
  await expect(page.locator('.ranking-marker')).toHaveCount(2);
  await expect(page.getByText('OpenStreetMap')).toBeVisible();
  await expect(page.locator('.leaflet-top.leaflet-right .leaflet-control-zoom')).toBeVisible();
  const markersClearPanel = await page.evaluate(() => {
    const panelRight = document.querySelector('.ranking-results-panel').getBoundingClientRect().right;
    return [...document.querySelectorAll('.ranking-marker')].every(marker => marker.getBoundingClientRect().left >= panelRight);
  });
  expect(markersClearPanel).toBe(true);

  const firstCard = page.locator('[data-content-id="a"]');
  await firstCard.click();
  await expect(firstCard).toHaveAttribute('aria-current','true');
  await expect(page.locator('.ranking-marker--active')).toHaveCount(1);
  await expect(page.locator('.leaflet-popup-content')).toContainText('문화비축기지');

  const markers = page.locator('.ranking-marker');
  expect(await markers.count()).toBe(2);
  await markers.nth(1).click();
  await expect(page.locator('[data-content-id="b"]')).toHaveAttribute('aria-current','true');
  await expect(page.locator('[data-content-id="c"]')).toContainText('지도 위치 없음');
});

test('모바일에서 지도 위·목록 아래 흐름을 유지한다', async ({ page }) => {
  await page.setViewportSize({ width:360,height:800 });
  await page.goto('/?district=마포구&category=문화시설');
  await expect(page.locator('.ranking-marker')).toHaveCount(2);
  const layout = await page.evaluate(() => {
    const map = document.querySelector('.ranking-map').getBoundingClientRect();
    const panel = document.querySelector('.ranking-results-panel').getBoundingClientRect();
    return { mapHeight:map.height, mapBottom:map.bottom, panelTop:panel.top, panelPosition:getComputedStyle(document.querySelector('.ranking-results-panel')).position, overflow:document.documentElement.scrollWidth <= innerWidth };
  });
  expect(layout.mapHeight).toBeGreaterThanOrEqual(310);
  expect(layout.panelTop).toBeGreaterThanOrEqual(layout.mapBottom);
  expect(layout.panelPosition).toBe('static');
  expect(layout.overflow).toBe(true);
});
