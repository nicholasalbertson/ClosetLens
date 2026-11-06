# Sovereign Lens — Integrated System Architecture

**Goal**: Personal wardrobe intelligence that combines:
1. Outfit Lens-style detection (any photo → individual items → shoppable similar)
2. Google Photos Wardrobe (scan library → catalog owned pieces → mix/match + try-on)
3. Sovereign Closet composer + scoring + proof jobs
4. Rap aesthetic / BLAIZE archive intelligence (documented / reconstructed / custom looks, vest & jewelry library)

## Data layers

| Layer | Source | Purpose |
|-------|--------|---------|
| Owned wardrobe | Google Photos API (or manual upload) + vision model | Items you actually own, extracted from personal photos |
| External detection | User-uploaded photo or URL | Per-item detection → similar product search (Outfit Lens model) |
| Style archive | Volume III + custom vest/jewelry library | Inspiration, scoring bias, custom design references |
| Product graph | Seed + affiliate feeds (ASOS, Nike, Moncler, etc.) | Shoppable results with price + shipping filter |
| Canon / identity | BLAIZE physical canon (tunnels, frames, tattoos, physique) | Scoring weights & digital twin constraints |

## Pipeline

1. **Ingest**
   - Google Photos: mediaItems.search with contentFilter (FASHION / PEOPLE) → download → vision.
   - Manual: drag-drop any image.
2. **Detect**
   - Fashion object detection (14+ categories) + attributes (color, silhouette, material).
   - Segment individual items (not whole-outfit blob).
3. **Match**
   - Owned: cosine / embedding match against personal wardrobe catalog.
   - External: visual search against product index or live retailer APIs.
4. **Compose**
   - Existing Sovereign Closet engine: required slots, palette, budget, owned-only flag.
   - Scoring: identity_alignment, silhouette_balance, palette_harmony, context_fit, wardrobe_leverage.
5. **Visualize**
   - Virtual try-on (Nano Banana / Flux / custom LoRA on digital twin).
   - Outfit cards + proof jobs.
6. **Output**
   - Saved looks, Throne/wishlist links, content calendar (30-day BLAIZE engine).

## Production stack (recommended)

- Vision: Google Gemini / OpenAI vision or specialized fashion model (Ximilar-style or fine-tuned).
- Storage: Google Photos Library API + own Postgres (item_master schema from Outfit Generator Database doc).
- Search: embedding index (pgvector or Pinecone) for similar items.
- Frontend: the single-file prototype as starting point; evolve to Next.js / React Native.
- Monetization: affiliate commissions (Outfit Lens model) + optional custom commission (HALO MAX, vest RFQs).

## Current prototype

`sovereign-lens.html` — single offline file that demonstrates:
- Composer + scoring (simplified but faithful)
- Simulated photo detection results
- Personal wardrobe grid
- Archive browser (artists + custom vests)
- Local history + proof jobs

Open in any browser. No backend required.

## Next concrete steps

1. Wire real vision (start with Gemini 1.5 Flash vision on uploaded images).
2. Google Photos OAuth + mediaItems.list / search.
3. Expand SEED_PRODUCTS from the full Volume III archive + product feeds.
4. Add digital twin LoRA constraints from Global Style Intelligence System.
5. Shipping-country filter + multi-retailer price comparison.

Status: Prototype ready. Architecture locked to existing Sovereign Closet domain model.
