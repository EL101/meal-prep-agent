"""Import every model here so Alembic autogenerate sees them via Base.metadata."""

from app.models.inventory import InventoryItem
from app.models.plan import MealPlan, PlannedMeal, Recipe, RecipeRating
from app.models.profile import ExcludedFood, Profile

__all__ = [
    "ExcludedFood",
    "InventoryItem",
    "MealPlan",
    "PlannedMeal",
    "Profile",
    "Recipe",
    "RecipeRating",
]
