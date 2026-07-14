import { expect, it, vi } from 'vitest';
import { createRouter } from '../../../src/router/router.js';

it('재렌더 전에 이전 화면을 정리한다', () => {
  const cleanup = vi.fn();
  const router = createRouter({
    routes: { ranking: vi.fn(() => cleanup), posts: vi.fn(() => vi.fn()) },
    outlet: document.body,
  });
  router.start();
  router.navigate('/posts');
  expect(cleanup).toHaveBeenCalledOnce();
  router.stop();
});

it('찾을 수 없는 경로를 처리한다', () => {
  const onNotFound = vi.fn();
  history.replaceState({}, '', '/missing');
  const router = createRouter({ routes: {}, outlet: document.body, onNotFound });
  router.start();
  expect(onNotFound).toHaveBeenCalledOnce();
  router.stop();
});
