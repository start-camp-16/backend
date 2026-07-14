import { expect, test } from '@playwright/test';

async function mockApi(page) {
  await page.route('**/api/meta/categories', route => route.fulfill({ json: { items: ['관광지','문화시설'] } }));
  await page.route('**/api/meta/districts', route => route.fulfill({ json: { items: ['마포구','중구'] } }));
  await page.route('**/api/rankings**', route => route.fulfill({ json: {
    items: [{ rank: 1, content_id:'1', category:'문화시설', title:'문화비축기지', address:'서울 마포구', district:'마포구', image_url:null, thumbnail_url:null, phone:null, source_order:1 }],
    pagination:{ page:1,size:20,total_items:1,total_pages:1 },
  } }));
  await page.route('**/api/posts**', route => route.fulfill({ json: { items:[{id:1,tag:'자유',title:'마포 산책 후기',created_at:'2026-07-14T09:00:00Z',updated_at:'2026-07-14T09:00:00Z'}],pagination:{page:1,size:20,total_items:1,total_pages:1} } }));
  await page.route('**/api/posts/1', route => route.fulfill({ json: { id:1,tag:'자유',title:'마포 산책 후기',content:'좋았어요.',created_at:'2026-07-14T09:00:00Z',updated_at:'2026-07-14T09:00:00Z' } }));
  await page.route('**/api/posts/1/comments', route => route.fulfill({ json: { items: [] } }));
  await page.route('**/api/chat', route => route.fulfill({ json: { answer:'문화비축기지를 추천해요.',sources:[{type:'location',content_id:'1',title:'문화비축기지',category:'문화시설',district:'마포구',address:'서울 마포구'},{type:'post',post_id:1,title:'마포 산책 후기',tag:'자유'}] } }));
}

test.beforeEach(async ({ page }) => { await mockApi(page); });

test('구와 카테고리로 장소를 찾는다', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('어느 구에서?').selectOption('마포구');
  await page.getByLabel('무엇을 할까요?').selectOption('문화시설');
  await page.getByRole('button', { name:'장소 찾기' }).click();
  await expect(page).toHaveURL(/district=.*category=/);
  await expect(page.getByText('문화비축기지')).toBeVisible();
  await expect(page.locator('.rank-number')).toHaveText('1');
});

test('게시글을 열고 챗봇 근거를 확인한다', async ({ page }) => {
  await page.goto('/posts');
  await page.getByRole('link', { name:/마포 산책 후기/ }).click();
  await expect(page.getByRole('heading', { name:'마포 산책 후기' })).toBeVisible();
  await page.getByRole('button', { name:'챗봇 열기' }).click();
  await page.getByLabel('메시지').fill('마포구 추천해줘');
  await page.getByRole('button', { name:'전송' }).click();
  await expect(page.getByText('문화비축기지를 추천해요.')).toBeVisible();
  await expect(page.locator('.chat-source').filter({ hasText:'마포 산책 후기' })).toHaveAttribute('href','/posts/1');
});

test('360px에서 가로 스크롤 없이 챗봇을 연다', async ({ page }) => {
  await page.setViewportSize({ width:360,height:800 });
  await page.goto('/');
  await page.getByRole('button', { name:'챗봇 열기' }).click();
  await expect(page.locator('#chat-panel')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
