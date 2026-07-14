import { expect, it } from 'vitest';
import { renderPostLoadError } from '../../../src/features/board/post-detail-page.js';

it('게시글 상세 오류 메시지를 HTML로 해석하지 않는다', () => {
  renderPostLoadError(document.body, '<img src=x onerror=alert(1)>');
  expect(document.querySelector('img')).toBeNull();
  expect(document.body.textContent).toContain('<img src=x onerror=alert(1)>');
  expect(document.querySelector('a').getAttribute('href')).toBe('/posts');
});
