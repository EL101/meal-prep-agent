import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.base import IdMixin, TimestampMixin


class Recipe(IdMixin, TimestampMixin, Base):
    __tablename__ = "recipes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.user_id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    servings: Mapped[int] = mapped_column(default=1)
    calories_per_serving: Mapped[float]
    protein_g_per_serving: Mapped[float]
    minutes: Mapped[int] = mapped_column(default=30)
    ingredients: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    steps: Mapped[list[str]] = mapped_column(JSON, default=list)


class MealPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "meal_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.user_id", ondelete="CASCADE"), index=True
    )
    week_start: Mapped[date]
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|running|ready|failed
    error: Mapped[str | None] = mapped_column(Text)

    estimated_total: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    grocery_list: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    cooking_timeline: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    meals: Mapped[list["PlannedMeal"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", lazy="selectin"
    )


class PlannedMeal(IdMixin, Base):
    __tablename__ = "planned_meals"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meal_plans.id", ondelete="CASCADE"), index=True
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id"))
    day: Mapped[int]  # 0 = Monday
    slot: Mapped[str] = mapped_column(String(20))  # breakfast | lunch | dinner | snack
    locked: Mapped[bool] = mapped_column(default=False)

    plan: Mapped[MealPlan] = relationship(back_populates="meals")
    recipe: Mapped[Recipe] = relationship(lazy="selectin")


class RecipeRating(IdMixin, TimestampMixin, Base):
    """1-5 stars plus an optional "what I didn't like". Fed back into future generations."""

    __tablename__ = "recipe_ratings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.user_id", ondelete="CASCADE"), index=True
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), index=True
    )
    stars: Mapped[int]
    comment: Mapped[str | None] = mapped_column(Text)
