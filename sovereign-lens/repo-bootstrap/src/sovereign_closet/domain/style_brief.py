from typing import Literal
from pydantic import BaseModel, Field

class StyleAxes(BaseModel):
    luxury: float = Field(0.7, ge=0, le=1)
    streetwear: float = Field(0.8, ge=0, le=1)
    boldness: float = Field(0.5, ge=0, le=1)
    flashiness_max: float = Field(0.5, ge=0, le=1)
    minimalism: float = Field(0.5, ge=0, le=1)

class StyleBrief(BaseModel):
    query: str
    occasion: str | None = None
    season: str | None = None
    budget_max: float | None = Field(default=None, gt=0)
    palette: list[str] = ["black", "charcoal", "crimson"]
    required_slots: list[str] = ["top", "bottom", "footwear"]
    optional_slots: list[str] = ["outerwear", "jewelry", "watch", "bag"]
    owned_only: bool = False
    axes: StyleAxes = StyleAxes()
