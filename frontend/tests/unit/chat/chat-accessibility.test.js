import { expect, it } from 'vitest';
import { mountChat } from '../../../src/features/chat/chat-controller.js';

it('Escape로 닫고 플로팅 버튼에 포커스를 돌린다', () => {
  const container = document.body.appendChild(document.createElement('div'));
  mountChat({ container });
  const trigger = container.querySelector('.chat-trigger');
  trigger.click();
  expect(container.querySelector('#chat-panel').hidden).toBe(false);
  container.querySelector('#chat-panel').dispatchEvent(new KeyboardEvent('keydown', { key:'Escape', bubbles:true }));
  expect(container.querySelector('#chat-panel').hidden).toBe(true);
  expect(document.activeElement).toBe(trigger);
});
