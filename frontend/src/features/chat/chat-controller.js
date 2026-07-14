import { sendChat } from './chat-api.js';
import { createChatState, toChatHistory } from './chat-state.js';
import { renderChatSources } from './chat-sources.js';
import './chat.css';

const ERROR_MESSAGES = {
  CHAT_RATE_LIMITED: '요청이 많습니다. 잠시 후 다시 시도해 주세요.',
  CHAT_PROVIDER_ERROR: '챗봇 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.',
};

export function mountChat({ container }) {
  const state = createChatState();
  container.innerHTML = `<button class="chat-trigger" type="button" aria-expanded="false" aria-controls="chat-panel"><span aria-hidden="true">✦</span><span class="visually-hidden">챗봇 열기</span></button><section id="chat-panel" class="chat-panel" role="dialog" aria-modal="true" aria-label="지역 정보 챗봇" hidden><header><div><strong>뭐할구 가이드</strong><small>서울 장소와 동네 이야기를 물어보세요</small></div><button type="button" data-close aria-label="챗봇 닫기">×</button></header><div class="chat-log" aria-live="polite"></div><form><label for="chat-message" class="visually-hidden">메시지</label><textarea id="chat-message" name="message" rows="2" maxlength="1000" placeholder="예: 마포구에서 전시 보고 산책할 곳 알려줘"></textarea><button>전송</button></form></section>`;
  const trigger = container.querySelector('.chat-trigger');
  const panel = container.querySelector('.chat-panel');
  const log = container.querySelector('.chat-log');
  const form = container.querySelector('form');
  const input = form.elements.message;
  const background = () => document.querySelectorAll('.site-header, #route-outlet, footer');

  function draw() {
    trigger.setAttribute('aria-expanded', String(state.isOpen));
    panel.hidden = !state.isOpen;
    log.replaceChildren();
    if (!state.messages.length) {
      const intro = document.createElement('div'); intro.className = 'chat-intro';
      intro.textContent = '어디서 무엇을 하고 싶은지 알려주세요. 장소와 게시판 이야기를 함께 찾아볼게요.'; log.append(intro);
    }
    for (const message of state.messages) {
      const item = document.createElement('article'); item.className = `chat-message chat-message--${message.role}`;
      const text = document.createElement('p'); text.textContent = message.content; item.append(text);
      if (message.sources) { const sources = document.createElement('div'); sources.className = 'chat-sources'; renderChatSources(sources, message.sources); item.append(sources); }
      if (message.status === 'failed') {
        const error = document.createElement('small'); error.textContent = message.error;
        const retry = document.createElement('button'); retry.type = 'button'; retry.textContent = '다시 시도'; retry.addEventListener('click', () => transmit(message, true));
        item.append(error, retry);
      }
      log.append(item);
    }
    form.querySelector('button').disabled = state.isSending; input.disabled = state.isSending; log.scrollTop = log.scrollHeight;
  }

  function open() { state.isOpen = true; background().forEach(node => { node.inert = true; }); draw(); input.focus(); document.body.classList.add('chat-open'); }
  function close() { state.isOpen = false; background().forEach(node => { node.inert = false; }); draw(); document.body.classList.remove('chat-open'); trigger.focus(); }
  async function transmit(existing, retry = false) {
    if (state.isSending) return;
    const content = retry ? existing.content : input.value.trim();
    if (!content || content.length > 1000) return;
    if (!retry) { existing = { role:'user', content, status:'pending' }; state.messages.push(existing); input.value = ''; }
    else { existing.status = 'pending'; delete existing.error; }
    state.isSending = true; draw();
    try {
      const response = await sendChat({ message:content, history:toChatHistory(state.messages.filter(item => item !== existing)) });
      existing.status = 'sent'; state.messages.push({ role:'assistant', content:response.answer, sources:response.sources, status:'sent' });
    } catch (error) {
      if (error.name !== 'AbortError') { existing.status = 'failed'; existing.error = ERROR_MESSAGES[error.code] ?? error.message; }
    } finally { state.isSending = false; draw(); }
  }

  trigger.addEventListener('click', open);
  container.querySelector('[data-close]').addEventListener('click', close);
  panel.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); close(); return; }
    if (event.key !== 'Tab') return;
    const focusable = [...panel.querySelectorAll('button:not(:disabled),textarea:not(:disabled),a[href]')];
    if (!focusable.length) return;
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  form.addEventListener('submit', event => { event.preventDefault(); transmit(); });
  input.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); } });
  return () => { background().forEach(node => { node.inert = false; }); document.body.classList.remove('chat-open'); };
}
