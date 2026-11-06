# API Authentication — Sovereign Lens

## Boundary

`SOVEREIGN_API_KEY` (or `python3 backend/server.py --key <secret>`) protects **only** `/api/*`.

Public, with or without a key:

- `/` and `/index.html` (the Lens page)
- `/sovereign-lens-v2.html`, `/sovereign-lens.html`, `/backend-ui.html`
- `/original-sovereign-closet.html`
- `/README.md`, `/ARCHITECTURE.md`, `/docs/*`

Not served over HTTP, so a missing key cannot fall through to a file:

- `/data/*` catalogs
- `/backend/*` source
- `/repo-bootstrap/*`

A failed check on a protected route writes **one** response:

```http
HTTP/1.0 401
Content-Type: application/json
Content-Length: …

{"error":"unauthorized","hint":"Send Authorization: Bearer <key> or X-API-Key"}
```

The handler returns after that write. It does not also send the HTML page. Static requests never take the API-key branch, including when the key is wrong or absent.

Accepted credentials, when a key is configured:

```http
Authorization: Bearer <key>
X-API-Key: <key>
```

Either header is enough. When `SOVEREIGN_API_KEY` is unset, `/api/*` is open and `GET /api/status` reports `"auth_required": false`.

`GET /api/status` is itself under `/api/*`, so it requires the key whenever auth is on. The Lens page treats network failure and HTTP 401 as **Offline fallback** and keeps the embedded seed.

CORS allows `Authorization` and `X-API-Key` on preflight. No `WWW-Authenticate` header is sent, so a browser navigation to an API URL does not open a password dialog.

## Gemini and Google Photos

Neither is part of server auth.

- Gemini remains an optional browser call with a key stored in `localStorage`. Dropping an image is what sends it. This pass does not add a proxy or a key.
- Google Photos is a placeholder button. No OAuth client and no Photos request are wired.

## Production notes (not implemented)

JWT sessions, HttpOnly cookies, mutual TLS, and an API gateway are out of scope. Do not put a real shared secret in the frontend source.
