# Sovereign Lens — Integrated System Architecture (v2)

**Status**: v2 prototype implemented with real Gemini vision call, Digital Twin constraints, expanded Volume III seed, and Google Photos OAuth skeleton.

## What’s new in v2

| Feature | Implementation |
|---------|----------------|
| Real vision detection | Gemini 1.5 Flash vision API call on image drop. Structured JSON output (name, category, color, silhouette, confidence, search terms). Requires user-provided API key (stored locally). |
| Digital Twin constraints | Checkboxes for 4-inch tunnels, thick frames, athletic physique, tattoos. Bias scoring (+0.04–0.08) and generate exact positive/negative prompts for Midjourney/Flux/LoRA. |
| Expanded product seed | 15+ items drawn from Volume III customs, BLAIZE vest library (Milano Ghost, Celestial Ice), HALO MAX, P1 sourcing matrix (K87, PSD, AF1, Cuban, frames, tunnels). |
| Google Photos | Settings for Client ID + connect button. Documents the exact OAuth + mediaItems.search flow with FASHION content category. Ready to wire Google Identity Services. |
| Scoring | Identity alignment heavily rewards black/charcoal + twin items. |

## Files

- `sovereign-lens-v2.html` — full interactive prototype
- `sovereign-lens.html` — earlier simulated version
- `ARCHITECTURE.md` — this document

## How to use v2

1. Open `sovereign-lens-v2.html`.
2. Click **Settings** → paste a Gemini API key from [AI Studio](https://aistudio.google.com/apikey).
3. Drop any fashion photo in the **Lens / Vision** tab.
4. Toggle Digital Twin options and generate the prompt.
5. Compose looks with twin bias enabled.

## Production next steps

- Replace placeholder images with real product photography or affiliate links.
- Implement full Google Identity Services + Photos Library API (mediaItems.search + download).
- Persist wardrobe to backend (Postgres + pgvector for embeddings).
- Add shipping-country filter and live price comparison.
- Fine-tune a fashion detection model if Gemini latency/cost becomes an issue.

The domain model remains compatible with the original Sovereign Closet Python package.