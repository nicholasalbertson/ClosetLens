# API Authentication — Sovereign Lens v0.3.6

All external calls (Gemini, Google Photos, affiliate networks) are proxied through the backend so keys and tokens never leave the server.

## Environment variables

```bash
export SOVEREIGN_API_KEY=your-secret          # optional local API key
export GEMINI_API_KEY=your-gemini-key         # server-side Gemini
export GOOGLE_CLIENT_ID=your-oauth-client-id
export GOOGLE_CLIENT_SECRET=your-oauth-secret
export GOOGLE_REDIRECT_URI=http://localhost:8080/api/auth/google/callback
export AFFILIATE_API_KEY=your-affiliate-key   # Impact / CJ / etc.
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/status` | Reports which services are configured |
| GET | `/api/auth/google/start` | Returns Google OAuth URL (photoslibrary.readonly) |
| GET | `/api/auth/google/callback` | Exchanges code for access_token |
| POST | `/api/vision` | Gemini vision proxy (image → structured items) |
| POST | `/api/photos/search` | Google Photos mediaItems.search (FASHION) |
| POST | `/api/affiliate/search` | Affiliate product search proxy |

## Google Photos OAuth flow

1. Client calls `GET /api/auth/google/start`.
2. User is redirected to the returned `auth_url`.
3. Google redirects to `/api/auth/google/callback?code=...`.
4. Backend exchanges the code for an access token (server-side).
5. Client sends the access token to `POST /api/photos/search` with body `{"access_token": "..."}`.
6. Backend calls Photos Library API with FASHION content category filter.

Scope: `https://www.googleapis.com/auth/photoslibrary.readonly`

## Gemini

`POST /api/vision` with image base64 or URL. Backend uses `GEMINI_API_KEY` to call `gemini-1.5-flash:generateContent`. Key never reaches the browser.

## Affiliate

`POST /api/affiliate/search` with `{"q": "Moncler Maya"}`. Backend uses `AFFILIATE_API_KEY` for the network call (Impact, CJ, etc.).

## Status

`GET /api/status` returns:
- `gemini_configured`
- `google_photos_configured`
- `affiliate_configured`

All proxies return 503 with `"stub": true` until the corresponding environment variable is set. No live calls are made without credentials.
