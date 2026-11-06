# Outfit System Integration

The Sovereign Lens project now includes a condensed extract from the **Outfit System Image Search Inventory** (200 looks, 1669 atomic item options).

## Source
`Outfit_System_Image_Search_Inventory_2_Moncler_Pilot_Final.xlsx`

- 200 outfits (053–252)
- Capsules I–XX (Quiet-Luxury Command through Archive/Future Collector)
- Slots: hero, top, bottom, shoes, accents
- Sourcing classifications: Exact Model, Product Family, Vintage/Archival, Ambiguous/Custom, Generic/Unbranded
- Brand index covering 100+ brands (Moncler, Loro Piana, Cartier, Rolex, Rick Owens, Balenciaga, etc.)

## Extracted data (in `data/`)
- `outfit_system_items.json` — first 400 atomic items with id, outfit, slot, brand, category, color, search query, classification
- `outfit_system_summary.json` — first 50 full outfit summaries

## API endpoints (backend)
- `GET /api/outfit-system` — outfit summaries
- `GET /api/outfit-items` — atomic items (limited)

## Relation to existing systems
- Complements the Volume III rap aesthetic archive and BLAIZE custom vest library
- Provides a named-product sourcing layer for the composer
- Search queries and official anchors (Moncler Maya, Purple Brand P001, Prada Re-Nylon, AMIRI MX1, LV Trainer, Dior B30, etc.) can feed vision + affiliate matching
- Capsule structure maps to the 30-day content calendar and Digital Twin progression

## Next steps
- Full import of all 1669 items (or on-demand query)
- Link vision detections to nearest inventory items via embedding or search query
- Add capsule filter and slot-aware compose in the UI
- Wire official anchor URLs into the product seed
