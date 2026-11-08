from sovereign_closet.domain.outfit import Outfit, OutfitScore
from sovereign_closet.domain.style_brief import StyleBrief

def score_outfit(outfit: Outfit, brief: StyleBrief) -> OutfitScore:
    colors = {c.lower() for item in outfit.items for c in item.colors}
    preferred = {c.lower() for c in brief.palette}
    palette_harmony = 0.5 if not colors else min(1.0, 0.4 + 0.6 * len(colors & preferred) / max(1, len(colors)))

    silhouettes = [item.silhouette.lower() for item in outfit.items]
    substantial_footwear = any(
        item.product_type.lower() in {"sneaker", "boot", "footwear"}
        and item.silhouette.lower() in {"high top", "chunky", "platform", "substantial"}
        for item in outfit.items
    )
    wide_bottom = any(
        item.product_type.lower() in {"bottom", "pants", "trouser", "denim", "cargo"}
        and item.silhouette.lower() in {"wide", "relaxed", "straight", "stacked"}
        for item in outfit.items
    )
    silhouette_balance = 0.9 if (wide_bottom and substantial_footwear) else 0.75

    owned_count = sum(1 for x in outfit.items if x.owned)
    wardrobe_leverage = min(1.0, 0.5 + owned_count / max(1, len(outfit.items)) * 0.5)

    identity_alignment = 0.9 if ("black" in colors or not colors) else 0.75
    context_fit = 0.85

    total = (
        identity_alignment * 0.30
        + silhouette_balance * 0.25
        + palette_harmony * 0.15
        + context_fit * 0.15
        + wardrobe_leverage * 0.15
    )
    return OutfitScore(
        identity_alignment=identity_alignment,
        silhouette_balance=silhouette_balance,
        palette_harmony=palette_harmony,
        context_fit=context_fit,
        wardrobe_leverage=wardrobe_leverage,
        total=round(total, 4),
    )
