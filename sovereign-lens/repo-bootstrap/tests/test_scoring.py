from sovereign_closet.domain.outfit import Outfit
from sovereign_closet.domain.style_brief import StyleBrief
from sovereign_closet.repositories.products import SEED_PRODUCTS
from sovereign_closet.services.scoring import score_outfit

def test_scoring_is_deterministic():
    outfit = Outfit(id="x", items=[SEED_PRODUCTS[1], SEED_PRODUCTS[2], SEED_PRODUCTS[4]])
    brief = StyleBrief(query="test")
    a = score_outfit(outfit, brief)
    b = score_outfit(outfit, brief)
    assert a == b
    assert 0 <= a.total <= 1
