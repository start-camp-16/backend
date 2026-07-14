import { expect, it } from 'vitest';
import { parseRankingQuery, toRankingQuery } from '../../../src/features/ranking/ranking-state.js';
it('랭킹 쿼리를 정규화한다', () => expect(parseRankingQuery(new URLSearchParams('district=마포구&category=문화시설&page=0'))).toEqual({ district:'마포구', category:'문화시설', page:1 }));
it('기본 페이지를 URL에서 생략한다', () => {
  const query = toRankingQuery({ district:'마포구', category:'문화시설', page:1 });
  expect(query.get('district')).toBe('마포구'); expect(query.get('category')).toBe('문화시설'); expect(query.has('page')).toBe(false);
});
