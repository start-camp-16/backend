import { describe, expect, it } from 'vitest';
import { matchRoute } from '../../../src/router/routes.js';

describe('matchRoute', () => {
  it.each([
    ['/', 'ranking', {}],
    ['/posts', 'posts', {}],
    ['/posts/new', 'post-new', {}],
    ['/posts/12', 'post-detail', { id: '12' }],
    ['/posts/12/edit', 'post-edit', { id: '12' }],
  ])('%s를 해석한다', (path, name, params) => {
    expect(matchRoute(path)).toEqual({ name, params });
  });

  it('1 미만이거나 숫자가 아닌 id를 거부한다', () => {
    expect(matchRoute('/posts/0')).toBeNull();
    expect(matchRoute('/posts/x')).toBeNull();
  });
});
