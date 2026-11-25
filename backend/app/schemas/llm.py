"""Structured-output schemas Claude must fill. Validated by the SDK's messages.parse()."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class DetectedItem(BaseModel):
    name: str = Field(description="Generic grocery name, e.g. 'whole milk', not a brand.")
    quantity: float
    unit: str = Field(description="One of: each, g, kg, oz, lb, ml, l, cup, tbsp, tsp")
    confidence: float = Field(ge=0, le=1, description="How sure you are this item is present.")
    estimated_expiry: date | None = None
    price_paid: float | None = Field(None, description="Only for receipts: line-item price.")


class InventoryExtraction(BaseModel):
    items: list[DetectedItem]
    store_name: str | None = None


class DraftIngredient(BaseModel):
    name: str
    quantity: float
    unit: str
    from_inventory: bool = Field(description="True if this comes from the user's inventory.")


class DraftRecipe(BaseModel):
    title: str
    servings: int
    minutes: int
    calories_per_serving: float
    protein_g_per_serving: float
    slot: Literal["breakfast", "lunch", "dinner", "snack"]
    ingredients: list[DraftIngredient]
    steps: list[str]


class RecipeCandidates(BaseModel):
    """Claude proposes more recipes than needed; the optimizer picks the final plan."""

    recipes: list[DraftRecipe]
