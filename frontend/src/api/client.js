import { ApiError } from './errors.js';

function apiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
}

export async function request(path, {
  method = 'GET', query = {}, body, signal,
} = {}) {
  const url = new URL(`${apiBaseUrl()}${path}`, window.location.origin);
  for (const [key, value] of Object.entries(query)) {
    if (value !== '' && value !== null && value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }

  let response;
  try {
    response = await fetch(url, {
      method,
      signal,
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError();
  }

  if (response.status === 204) return undefined;

  const isJson = response.headers.get('content-type')?.includes('json');
  const data = isJson ? await response.json() : null;
  if (!response.ok) {
    throw new ApiError({
      status: response.status,
      code: data?.code ?? 'HTTP_ERROR',
      message: data?.message ?? '서버 오류가 발생했습니다.',
      details: data?.details ?? null,
    });
  }
  if (!isJson) {
    throw new ApiError({
      status: response.status,
      code: 'INVALID_RESPONSE',
      message: '서버 응답을 확인할 수 없습니다.',
    });
  }
  return data;
}
