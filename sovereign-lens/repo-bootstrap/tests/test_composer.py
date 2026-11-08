from sovereign_closet.domain.style_brief import StyleBrief
from sovereign_closet.repositories.products import SEED_PRODUCTS
from sovereign_closet.services.composer import compose_outfits

def test_composer_returns_ranked_looks():
    brief = StyleBrief(query="black streetwear", budget_max=2000)
    looks = compose_outfits(SEED_PRODUCTS, brief)
    assert looks
    assert looks[0].score is not None
    assert all(sum(p.price for p in look.items) <= 2000 for look in looks)
