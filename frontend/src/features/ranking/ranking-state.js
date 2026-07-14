export function parseRankingQuery(params) {
  const page = Number.parseInt(params.get('page') ?? '1', 10);
  return { district: params.get('district') ?? '', category: params.get('category') ?? '', page: Number.isInteger(page) && page > 0 ? page : 1 };
}
export function toRankingQuery({ district, category, page = 1 }) {
  const params = new URLSearchParams();
  if (district) params.set('district', district); if (category) params.set('category', category); if (page > 1) params.set('page', String(page));
  return params;
}
