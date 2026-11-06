from copy import deepcopy
from sovereign_closet.domain.outfit import Outfit
from sovereign_closet.domain.product import Product

def replace_item(outfit: Outfit, old_product_id: str, replacement: Product) -> Outfit:
    mutated = deepcopy(outfit)
    mutated.id = f"{outfit.id}-m1"
    mutated.items = [replacement if p.id == old_product_id else p for p in outfit.items]
    mutated.score = None
    mutated.lineage = [*outfit.lineage, f"replace:{old_product_id}->{replacement.id}"]
    return mutated
