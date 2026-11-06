from pydantic import BaseModel, Field

class Product(BaseModel):
    id: str
    product_type: str
    brand: str
    style_name: str
    price: float = Field(ge=0)
    colors: list[str] = []
    materials: list[str] = []
    silhouette: str = "regular"
    rarity_score: int = Field(default=5, ge=1, le=10)
    owned: bool = False
    available: bool = True
    metadata_confidence: float = Field(default=1.0, ge=0, le=1)
