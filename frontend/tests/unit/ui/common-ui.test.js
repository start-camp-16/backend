import { expect, it, vi } from 'vitest';
import { renderAsyncState } from '../../../src/ui/async-state.js';
import { openModal } from '../../../src/ui/modal.js';
import { renderPagination } from '../../../src/ui/pagination.js';

it('오류 재시도를 제공한다', () => {
  const retry = vi.fn();
  renderAsyncState(document.body, { kind: 'error', message: '실패', onRetry: retry });
  document.querySelector('button').click();
  expect(document.querySelector('[role="alert"]').textContent).toContain('실패');
  expect(retry).toHaveBeenCalledOnce();
});

it('페이지 경계를 지킨다', () => {
  const change = vi.fn();
  renderPagination(document.body, { page: 1, totalPages: 2, onPageChange: change });
  expect(document.querySelector('[data-page="previous"]').disabled).toBe(true);
  document.querySelector('[data-page="next"]').click();
  expect(change).toHaveBeenCalledWith(2);
});

it('모달을 닫으면 트리거로 포커스를 돌린다', () => {
  const trigger = document.body.appendChild(document.createElement('button'));
  trigger.focus();
  const input = document.createElement('input');
  const modal = openModal({ title: '확인', content: input, trigger, onConfirm: vi.fn() });
  expect(document.activeElement).toBe(input);
  modal.close();
  expect(document.activeElement).toBe(trigger);
});
