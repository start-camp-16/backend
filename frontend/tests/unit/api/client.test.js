import { afterEach, describe, expect, it, vi } from 'vitest';
import { request } from '../../../src/api/client.js';
import { ApiError } from '../../../src/api/errors.js';

afterEach(() => vi.unstubAllGlobals());

describe('request', () => {
  it('query와 JSON body를 전송하고 JSON을 반환한다', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ ok: true }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    )));

    await expect(request('/api/x', {
      method: 'POST', query: { page: 2, empty: '' }, body: { a: 1 },
    })).resolves.toEqual({ ok: true });
    const [url, options] = fetch.mock.calls[0];
    expect(url.toString()).toContain('/api/x?page=2');
    expect(options.body).toBe('{"a":1}');
  });

  it('204는 undefined를 반환한다', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
    await expect(request('/api/x')).resolves.toBeUndefined();
  });

  it('서버 오류를 ApiError로 변환한다', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ code: 'PASSWORD_MISMATCH', message: '비밀번호가 일치하지 않습니다.', details: null }),
      { status: 403, headers: { 'Content-Type': 'application/json' } },
    )));
    await expect(request('/api/x')).rejects.toMatchObject({ status: 403, code: 'PASSWORD_MISMATCH' });
    expect(ApiError.prototype).toBeInstanceOf(Error);
  });

  it('AbortError는 변환하지 않는다', async () => {
    const abort = new DOMException('aborted', 'AbortError');
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abort));
    await expect(request('/api/x')).rejects.toBe(abort);
  });

  it('네트워크 오류는 안전한 메시지로 변환한다', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('secret host')));
    await expect(request('/api/x')).rejects.toMatchObject({ code: 'NETWORK_ERROR', message: '요청을 처리할 수 없습니다.' });
  });

  it('2xx 비-JSON 응답도 안전한 오류로 처리한다', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>fallback</html>', {
      status: 200, headers: { 'Content-Type': 'text/html' },
    })));
    await expect(request('/api/x')).rejects.toMatchObject({
      code: 'INVALID_RESPONSE', message: '서버 응답을 확인할 수 없습니다.',
    });
  });
});
