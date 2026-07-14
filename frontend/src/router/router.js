import { matchRoute } from './routes.js';

export function createRouter({ routes, outlet, onNotFound = () => {} }) {
  let active = null;

  function render() {
    active?.controller.abort();
    active?.cleanup?.();
    active = null;
    const match = matchRoute(location.pathname);
    const mount = match && routes[match.name];
    if (!mount) return onNotFound({ outlet, pathname: location.pathname });
    const controller = new AbortController();
    const cleanup = mount({
      outlet,
      params: match.params,
      query: new URLSearchParams(location.search),
      signal: controller.signal,
      navigate,
    });
    active = { controller, cleanup };
  }

  function navigate(to, { replace = false } = {}) {
    history[replace ? 'replaceState' : 'pushState']({}, '', to);
    render();
  }

  function handleClick(event) {
    const anchor = event.target.closest?.('a[href]');
    if (!anchor || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const url = new URL(anchor.href, location.href);
    if (url.origin !== location.origin || anchor.target === '_blank') return;
    event.preventDefault();
    navigate(`${url.pathname}${url.search}${url.hash}`);
  }

  function start() {
    addEventListener('popstate', render);
    document.addEventListener('click', handleClick);
    render();
  }
  function stop() {
    removeEventListener('popstate', render);
    document.removeEventListener('click', handleClick);
    active?.controller.abort();
    active?.cleanup?.();
  }
  return { start, stop, navigate, render };
}
