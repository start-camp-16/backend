import { expect, it } from 'vitest';
import { createChatState, toChatHistory } from '../../../src/features/chat/chat-state.js';
it('성공한 최근 메시지 10개만 history로 만든다', () => {
  const messages = Array.from({ length: 12 }, (_, i) => ({ role:i%2?'assistant':'user', content:String(i), status:i===3?'failed':'sent' }));
  const history = toChatHistory(messages);
  expect(history).toHaveLength(10); expect(history.some(x => x.content === '3')).toBe(false);
});
it('초기 채팅 상태는 닫혀 있고 비어 있다', () => expect(createChatState()).toEqual({ isOpen:false, messages:[], isSending:false, error:null }));
