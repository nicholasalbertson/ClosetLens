# API Authentication Methods — Sovereign Lens

## 1. API Key (implemented)
Simple shared secret for the local backend.

**Enable**
```bash
export SOVEREIGN_API_KEY=your-secret-key
python3 backend/server.py
# or
python3 backend/server.py --key your-secret-key
```

**Client usage**
```http
GET /api/products
Authorization: Bearer your-secret-key
# or
X-API-Key: your-secret-key
```

If the key is set and missing/incorrect → 401.

## 2. Gemini API Key (client-side, current)
Stored in browser localStorage. Sent only to Google Generative Language API.

**Production recommendation**: move the call behind the backend so the key never leaves the server.

## 3. Google Photos OAuth 2.0 (planned)
Required for real personal wardrobe ingest.

**Flow**
1. Create OAuth client in Google Cloud Console (Web application).
2. Enable Photos Library API.
3. Add authorized JavaScript origins + redirect URIs.
4. Use Google Identity Services (`google.accounts.oauth2`) in the browser.
5. Request scope: `https://www.googleapis.com/auth/photoslibrary.readonly`
6. Exchange code → access token → call `mediaItems.search` with  
   `contentFilter.includedContentCategories = ["FASHION"]`.

**Security notes**
- Never embed client secrets in frontend code.
- Prefer authorization code + PKCE for public clients.
- Store refresh tokens server-side if multi-session access is needed.

## 4. Future production options
- JWT bearer tokens (short-lived) issued after login
- Session cookies with HttpOnly + Secure + SameSite
- Mutual TLS for internal services
- API gateway (Cloudflare, AWS API Gateway) with rate limiting

## Status endpoint
`GET /api/status` returns whether auth is required and current data counts. No auth needed if key is unset.
