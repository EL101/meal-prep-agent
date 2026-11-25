import uuid
from decimal import Decimal

from sqlalchemy import JSON, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import IdMixin, TimestampMixin


class Profile(TimestampMixin, Base):
    """One row per Supabase auth user. `user_id` is the Supabase `sub` claim."""

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)

    weekly_budget: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("75.00"))
    preferred_store: Mapped[str | None] = mapped_column(String(100))
    zip_code: Mapped[str | None] = mapped_column(String(10))

    calorie_goal: Mapped[int] = mapped_column(default=2200)
    protein_goal_g: Mapped[int] = mapped_column(default=140)

    # Defaults: cook Sunday + Wednesday, 2h per session, 1 person, basic kitchen.
    cook_days: Mapped[list[int]] = mapped_column(JSON, default=lambda: [6, 2])
    minutes_per_session: Mapped[int] = mapped_column(default=120)
    servings: Mapped[int] = mapped_column(default=1)
    equipment: Mapped[list[str]] = mapped_column(
        JSON, default=lambda: ["stovetop", "oven", "microwave"]
    )
    preferences: Mapped[list[str]] = mapped_column(JSON, default=list)


class ExcludedFood(IdMixin, TimestampMixin, Base):
    """Foods that must never appear in a plan. Enforced in code, not just prompted."""

    __tablename__ = "excluded_foods"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.user_id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(String(20), default="dislike")  # allergy | dislike
