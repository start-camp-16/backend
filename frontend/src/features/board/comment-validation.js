export function validateComment({ content, password }) {
  const errors = {}; const c = content.trim();
  if (c.length < 1 || c.length > 1000) errors.content = '댓글은 1~1,000자로 입력해 주세요.';
  if (password.length < 4 || password.length > 20) errors.password = '비밀번호는 4~20자로 입력해 주세요.';
  return errors;
}
