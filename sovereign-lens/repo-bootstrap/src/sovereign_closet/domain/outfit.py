from pydantic import BaseModel, Field
from .product import Product

class OutfitScore(BaseModel):
    identity_alignment: float = Field(ge=0, le=1)
    silhouette_balance: float = Field(ge=0, le=1)
    palette_harmony: float = Field(ge=0, le=1)
    context_fit: float = Field(ge=0, le=1)
    wardrobe_leverage: float = Field(ge=0, le=1)
    total: float = Field(ge=0, le=1)

class Outfit(BaseModel):
    id: str
    items: list[Product]
    score: OutfitScore | None = None
    rationale: list[str] = []
    lineage: list[str] = []
