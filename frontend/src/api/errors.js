export class ApiError extends Error {
  constructor({
    status = 0,
    code = 'NETWORK_ERROR',
    message = '요청을 처리할 수 없습니다.',
    details = null,
  } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}
