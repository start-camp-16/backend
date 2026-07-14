import { renderLayout } from './layout.js';
import { createRouter } from '../router/router.js';
import { mountRankingPage } from '../features/ranking/ranking-page.js';
import { mountBoardListPage } from '../features/board/board-list-page.js';
import { mountPostFormPage } from '../features/board/post-form-page.js';
import { mountPostDetailPage } from '../features/board/post-detail-page.js';
import { mountChat } from '../features/chat/chat-controller.js';

export function startApp({ root }) {
  const { outlet, chatRoot } = renderLayout(root);
  const stopChat = mountChat({ container: chatRoot });
  const router = createRouter({
    outlet,
    routes: {
      ranking: mountRankingPage,
      posts: mountBoardListPage,
      'post-new': context => mountPostFormPage(context, 'create'),
      'post-edit': context => mountPostFormPage(context, 'edit'),
      'post-detail': mountPostDetailPage,
    },
    onNotFound: ({ outlet: target }) => {
      target.replaceChildren();
      const section = document.createElement('section'); section.className = 'async-state';
      const title = document.createElement('h1'); title.textContent = '페이지를 찾을 수 없습니다';
      const link = document.createElement('a'); link.href = '/'; link.textContent = '홈으로 돌아가기';
      section.append(title, link); target.append(section);
    },
  });
  router.start();
  return { ...router, stop() { router.stop(); stopChat(); } };
}
