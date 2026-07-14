import { POST_TAGS } from './board-constants.js';
export function validatePost({ tag, title, content, password }) {
  const errors = {}; const t = title.trim(); const c = content.trim();
  if (!POST_TAGS.includes(tag)) errors.tag = '태그를 선택해 주세요.';
  if (t.length < 1 || t.length > 100) errors.title = '제목은 1~100자로 입력해 주세요.';
  if (c.length < 1 || c.length > 5000) errors.content = '본문은 1~5,000자로 입력해 주세요.';
  if (password.length < 4 || password.length > 20) errors.password = '비밀번호는 4~20자로 입력해 주세요.';
  return errors;
}
