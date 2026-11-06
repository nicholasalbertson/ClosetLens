# Sovereign Lens

Local outfit studio. The Lens page and the stdlib backend are one app: the page loads the canonical product and archive catalogs from the API, and it asks the same server to compose outfits and build the Digital Twin prompt. If that server is down or rejects the key, the page keeps the previous offline composer and says so.

The identity canon in `repo-bootstrap/` is unchanged.

## Run

From the repository root:

```bash
cd sovereign-lens
python3 backend/server.py
```

Open http://127.0.0.1:8080/

The process binds to `127.0.0.1` and port `8080` unless `HOST` or `PORT` is set. Optional API key:

```bash
export SOVEREIGN_API_KEY=dev-key
python3 backend/server.py
# equivalent: python3 backend/server.py --key dev-key
```

With a key set, every `/api/*` route requires either header:

```http
Authorization: Bearer dev-key
```

or

```http
X-API-Key: dev-key
```

Static pages stay public, including `/`, `/sovereign-lens-v2.html`, and `/backend-ui.html`. Put the same key in Lens Settings (or the Backend UI) so catalog, compose, and twin calls succeed. A rejected key is one JSON 401. The Lens page then shows **Offline fallback** and uses the embedded 15-item seed.

Open mode (no `SOVEREIGN_API_KEY`) serves `/api/*` without a header. See `docs/API-AUTH.md`.

Copy `sovereign-lens/.env.example` if you want a reminder of the variable names. The server does not read a dotenv file. Do not commit a real key.

## Test

Server smoke tests use only the standard library plus pytest. Bootstrap tests are the existing six-domain checks and need the scaffold's dependencies.

```bash
python3 -m pip install pytest
pytest -q sovereign-lens/tests

python3 -m pip install -e "sovereign-lens/repo-bootstrap[dev]"
cd sovereign-lens/repo-bootstrap && pytest -q
```

`sovereign-lens/tests` starts the real `backend/server.py` process. Auth tests read the raw socket and require exactly one HTTP status line, a `Content-Length` that matches the body, and no catalog or HTML bytes on a failed protected request.

## What talks to what

| Surface | Behavior |
| --- | --- |
| `GET /` | Lens UI |
| `GET /api/products`, `GET /api/archive` | Canonical `data/products.json` and `data/archive.json` |
| `GET /api/outfit-system`, `GET /api/outfit-items` | Inventory summary, and the first 200 atomic items |
| `POST /api/compose` | Rotating outfits from the catalog. A query prefers rows whose name, brand, or tags contain the words. |
| `POST /api/twin-prompt` | Positive and negative prompt from the twin toggles |
| `data/*.json` over HTTP | Not served. Use the API. |
| Lens offline path | Embedded seed, local scorer, local twin prompt, banner says **Offline fallback** |
| Google Photos control | Placeholder. It does not make a request. |
| Gemini | Still a manual image drop with a key the user pastes locally. This pass does not call it. |

`backend-ui.html` remains a small console for status, compose, twin, and products.

## Limitations

- No Google Photos OAuth, no Gemini proxy, and no paid or third-party credentials are configured. Photos is a placeholder. Gemini runs only in the browser if you supply your own key and drop an image.
- The compose query reorders matching pieces. It is not a search engine, and an empty query keeps catalog order. The offline composer does not apply that reorder.
- `GET /api/outfit-items` returns 200 rows of the 400-row extract, not the full spreadsheet.
- Placeholder product images point at the existing `placehold.co` URLs in the catalog. They are not product photography.
- Identity canon stays in `repo-bootstrap/src/sovereign_closet/canon/identity.py` (`protected_back_text` is `RARE ONE`, gauge terminal is `5.0`). The Lens twin prompt still uses the existing 4-inch tunnel wording. Those two were not merged.
- The FastAPI scaffold under `repo-bootstrap/` is separate. It still scores its own seed products. The Lens server does not import it.
- Custom vests and jewelry in the archive are fashion descriptions only. Nothing here is ballistic protection.
