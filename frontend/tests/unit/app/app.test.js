import { expect, it } from 'vitest';
import { startApp } from '../../../src/app/app.js';

it('알 수 없는 경로에 복귀 링크를 표시한다', () => {
  history.replaceState({}, '', '/missing');
  const root = document.createElement('div');
  const app = startApp({ root });
  expect(root.textContent).toContain('페이지를 찾을 수 없습니다');
  expect(root.querySelector('a[href="/"]')).not.toBeNull();
  app.stop();
});
