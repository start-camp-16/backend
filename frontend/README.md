# 뭐할구 프론트엔드

서울 구별 장소 랭킹, 익명 게시판·댓글, 근거 기반 지역 정보 챗봇을 제공하는 Vite 기반 SPA입니다.

## 실행

Node.js와 npm이 필요합니다.

```bash
npm install
cp .env.example .env
npm run dev
```

`VITE_API_BASE_URL`에는 백엔드 origin만 설정합니다. OpenAI 키는 프론트엔드에 설정하지 않습니다.

## 검증

```bash
npm test
npm run build
npm run test:e2e
```

## Netlify

- Build command: `npm run build`
- Publish directory: `dist`
- Environment: `VITE_API_BASE_URL`

SPA fallback은 `netlify.toml`에 포함되어 있습니다. 공유 API 계약은 `shared/openapi.yaml`입니다.
