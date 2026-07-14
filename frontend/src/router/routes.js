export const ROUTES = [
  { name: 'ranking', pattern: /^\/$/ },
  { name: 'posts', pattern: /^\/posts$/ },
  { name: 'post-new', pattern: /^\/posts\/new$/ },
  { name: 'post-edit', pattern: /^\/posts\/([1-9]\d*)\/edit$/, keys: ['id'] },
  { name: 'post-detail', pattern: /^\/posts\/([1-9]\d*)$/, keys: ['id'] },
];

export function matchRoute(pathname) {
  for (const route of ROUTES) {
    const match = pathname.match(route.pattern);
    if (!match) continue;

    const params = Object.fromEntries(
      (route.keys ?? []).map((key, index) => [key, match[index + 1]]),
    );
    return { name: route.name, params };
  }
  return null;
}
