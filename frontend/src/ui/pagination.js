export function renderPagination(container, { page, totalPages, onPageChange }) {
  container.replaceChildren();
  if (totalPages < 1) return;
  const nav = document.createElement('nav');
  nav.className = 'pagination';
  nav.setAttribute('aria-label', '페이지 이동');
  const makeButton = (label, target, key, disabled) => {
    const button = document.createElement('button');
    button.type = 'button'; button.textContent = label; button.dataset.page = key; button.disabled = disabled;
    button.addEventListener('click', () => onPageChange(target));
    return button;
  };
  nav.append(makeButton('이전', page - 1, 'previous', page <= 1));
  const current = document.createElement('span'); current.textContent = `${page} / ${totalPages}`; current.setAttribute('aria-current', 'page');
  nav.append(current, makeButton('다음', page + 1, 'next', page >= totalPages));
  container.append(nav);
}
