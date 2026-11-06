from sovereign_closet.domain.product import Product

SEED_PRODUCTS = [
    Product(
        id="H-001", product_type="hoodie", brand="Fear of God Essentials",
        style_name="90s Hoodie", price=120, colors=["Vintage Black"],
        materials=["Heavy Fleece"], silhouette="oversized", rarity_score=6, owned=True
    ),
    Product(
        id="T-001", product_type="tee", brand="Sovereign Closet",
        style_name="Signature Heavyweight Tee", price=80, colors=["Black"],
        materials=["Heavyweight Cotton"], silhouette="boxy", rarity_score=5, owned=True
    ),
    Product(
        id="P-001", product_type="pants", brand="Rick Owens",
        style_name="Bauhaus Cargos", price=950, colors=["Black"],
        materials=["Cotton", "Nylon"], silhouette="wide", rarity_score=7
    ),
    Product(
        id="D-001", product_type="denim", brand="Denim Tears",
        style_name="Raw Indigo Straight Denim", price=450, colors=["Black"],
        materials=["Denim"], silhouette="straight", rarity_score=7
    ),
    Product(
        id="SN-001", product_type="sneaker", brand="Nike",
        style_name="Air Jordan 1 High '85", price=250, colors=["Black", "Red"],
        materials=["Leather"], silhouette="high top", rarity_score=8
    ),
    Product(
        id="B-001", product_type="boot", brand="Guidi",
        style_name="Back-Zip Boot", price=1400, colors=["Black"],
        materials=["Leather"], silhouette="substantial", rarity_score=8
    ),
]
