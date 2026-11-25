"""Request/response models for the HTTP API (mirrored in mobile/lib/types.ts)."""

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

JobStatus = Literal["queued", "running", "ready", "failed"]
PriceSource = Literal["receipt", "kroger_estimate", "bls_estimate"]
MealSlot = Literal["breakfast", "lunch", "dinner", "snack"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProfileIn(BaseModel):
    weekly_budget: Decimal = Field(ge=0)
    preferred_store: str | None = None
    zip_code: str | None = None
    calorie_goal: int = Field(gt=0)
    protein_goal_g: int = Field(ge=0)
    cook_days: list[int] = Field(default_factory=lambda: [6, 2])
    minutes_per_session: int = 120
    servings: int = 1
    equipment: list[str] = Field(default_factory=lambda: ["stovetop", "oven", "microwave"])
    preferences: list[str] = Field(default_factory=list)


class ProfileOut(ProfileIn, ORMModel):
    user_id: uuid.UUID


class ExcludedFoodIn(BaseModel):
    name: str
    reason: Literal["allergy", "dislike"] = "dislike"


class ExcludedFoodOut(ExcludedFoodIn, ORMModel):
    id: uuid.UUID


class InventoryItemIn(BaseModel):
    name: str
    quantity: float = 1
    unit: str = "each"
    expires_on: date | None = None


class InventoryItemOut(InventoryItemIn, ORMModel):
    id: uuid.UUID
    source: str
    confidence: float
    needs_confirmation: bool


class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str


class RecipeOut(ORMModel):
    id: uuid.UUID
    title: str
    servings: int
    calories_per_serving: float
    protein_g_per_serving: float
    minutes: int
    ingredients: list[Ingredient]
    steps: list[str]


class PlannedMealOut(ORMModel):
    day: int
    slot: MealSlot
    locked: bool
    recipe: RecipeOut


class GroceryItem(BaseModel):
    name: str
    quantity: float
    unit: str
    price: Decimal
    price_source: PriceSource


class MealPlanOut(ORMModel):
    id: uuid.UUID
    status: JobStatus
    week_start: date
    meals: list[PlannedMealOut]
    grocery_list: list[GroceryItem]
    estimated_total: Decimal
    error: str | None = None


class PlanEdit(BaseModel):
    """Lock or swap meals, then the worker re-solves everything that isn't locked."""

    lock: list[uuid.UUID] = Field(default_factory=list)
    unlock: list[uuid.UUID] = Field(default_factory=list)
    swap: list[uuid.UUID] = Field(default_factory=list)


class RatingIn(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: str | None = None


class JobAccepted(BaseModel):
    id: uuid.UUID
    status: JobStatus
