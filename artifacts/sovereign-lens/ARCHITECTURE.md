# Sovereign Lens — Integrated System Architecture (v3)

**Status**: Expanded data + local stdlib backend added. Frontend remains fully usable offline; backend provides consistent scoring and data serving.

## Layers

| Layer | Current state |
|-------|----------------|
| Frontend | `sovereign-lens-v2.html` — Gemini vision, Digital Twin prompt gen, compose, archive browser |
| Data | `data/products.json` (20 items), `data/archive.json` (15 looks + vests) |
| Backend | `backend/server.py` — stdlib HTTP server with `/api/compose`, `/api/twin-prompt`, `/api/products`, `/api/archive` |
| Domain | Original Sovereign Closet Python package in `repo-bootstrap/` (scoring, canon, proof jobs) |
| Vision | Gemini 1.5 Flash (client-side key or future proxy) |
| Twin | Constraints bias scoring and emit generation prompts |

## Scoring (aligned with original)

- Identity alignment (black/charcoal heavily rewarded)
- Silhouette balance
- Palette harmony
- Context fit
- Wardrobe leverage
- Twin bonus (tunnels, frames, black dominance)

## Production path

1. Replace placeholder images with real product / affiliate imagery.
2. Implement Google Photos OAuth + mediaItems.search (FASHION category).
3. Move Gemini call behind backend proxy (key never in browser).
4. Add embedding index for similar-item search after vision detection.
5. Persist wardrobe and saved looks (Postgres).
6. Wire Throne / wishlist and 30-day content calendar from Global Style Intelligence System.

All custom vest and jewelry concepts remain fashion-only (no ballistic claims).