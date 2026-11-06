# Sovereign Lens — local app

The browser UI in `sovereign-lens-v2.html` and `backend/server.py` are one local app.

| Piece | Role |
| --- | --- |
| Lens page | Compose, wardrobe, archive, and Digital Twin. Loads `/api/products` and `/api/archive`. Compose and twin prompt call `/api/compose` and `/api/twin-prompt`. If those calls fail, the embedded seed and local functions run and the banner says **Offline fallback**. |
| `data/products.json`, `data/archive.json` | Canonical catalogs (55 products, 31 archive entries in the current files). Not served as static files. |
| `data/outfit_system_*.json` | Inventory extract exposed at `/api/outfit-system` and `/api/outfit-items`. |
| `backend/server.py` | Stdlib server. Optional API key on `/api/*` only. Static HTML stays public. |
| `backend-ui.html` | Small API console. |
| `repo-bootstrap/` | Separate FastAPI scaffold and identity canon. Not imported by the Lens server. Canon files were not edited. |
| Gemini | Optional client call on image drop. Not invoked by the server and not required to compose. |
| Google Photos | Placeholder control. No OAuth in this build. |

Scoring on the Lens server still rewards black and charcoal, palette overlap, owned pieces, and a twin bonus for tunnels, frames, and black. That bonus is separate from the bootstrap package's scorer.

A query on `/api/compose` moves catalog rows whose name, brand, or tags contain the words to the front of each slot. It does not replace the slot rotation.

Custom vest and jewelry language stays fashion-only.
