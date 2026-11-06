from itertools import product as cartesian_product
from uuid import uuid4
from sovereign_closet.domain.outfit import Outfit
from sovereign_closet.domain.product import Product
from sovereign_closet.domain.style_brief import StyleBrief
from sovereign_closet.services.scoring import score_outfit

SLOT_ALIASES = {
    "top": {"top", "tee", "hoodie", "shirt", "tank"},
    "bottom": {"bottom", "pants", "trouser", "denim", "cargo"},
    "footwear": {"footwear", "sneaker", "boot", "shoe"},
    "outerwear": {"outerwear", "jacket", "coat", "bomber"},
}

def compose_outfits(products: list[Product], brief: StyleBrief, limit: int = 10) -> list[Outfit]:
    pools: list[list[Product]] = []
    for slot in brief.required_slots:
        allowed = SLOT_ALIASES.get(slot, {slot})
        matches = [p for p in products if p.available and p.product_type.lower() in allowed]
        if brief.owned_only:
            matches = [p for p in matches if p.owned]
        if not matches:
            return []
        pools.append(matches[:8])

    results: list[Outfit] = []
    for combo in cartesian_product(*pools):
        if brief.budget_max is not None and sum(p.price for p in combo) > brief.budget_max:
            continue
        outfit = Outfit(id=f"look-{uuid4().hex[:10]}", items=list(combo))
        outfit.score = score_outfit(outfit, brief)
        outfit.rationale = [
            "Preserves protected identity constraints.",
            "Uses deterministic silhouette and palette scoring.",
            "Eligible products satisfy required slots and availability."
        ]
        results.append(outfit)

    results.sort(key=lambda x: x.score.total if x.score else 0, reverse=True)
    return results[:limit]
