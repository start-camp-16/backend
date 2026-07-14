export function renderAsyncState(container, { kind, message, onRetry } = {}) {
  container.replaceChildren();
  const box = document.createElement('div');
  box.className = `async-state async-state--${kind}`;
  if (kind === 'error') box.setAttribute('role', 'alert');
  else box.setAttribute('role', 'status');
  const text = document.createElement('p');
  text.textContent = message;
  box.append(text);
  if (kind === 'error' && onRetry) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button button--secondary';
    button.textContent = '다시 시도';
    button.addEventListener('click', onRetry);
    box.append(button);
  }
  container.append(box);
  return box;
}
