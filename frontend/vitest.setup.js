import { afterEach } from 'vitest';

afterEach(() => {
  document.body.innerHTML = '';
  history.replaceState({}, '', '/');
});
