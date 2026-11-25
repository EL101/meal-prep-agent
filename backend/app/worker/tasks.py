"""Background jobs run by arq. Claude calls take seconds to minutes, so they never block a request.

Pipeline for a plan (this is also what the evals compare):
  1. Claude proposes candidate recipes from profile, inventory, exclusions, and past ratings.
  2. Validation: the exclusion filter drops anything that hits an allergy or dislike.
  3. Pricing: each ingredient not already in inventory gets a receipt/Kroger/BLS quote.
  4. Optimizer: OR-Tools picks recipes and serving counts within budget and macro goals.
"""

import logging
import uuid
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import ExcludedFood, InventoryItem, MealPlan, PlannedMeal, Profile, Recipe
from app.models.plan import RecipeRating
from app.schemas.llm import DraftRecipe
from app.services import claude, storage
from app.services.exclusions import is_allowed
from app.services.optimizer import Candidate, PlanRequest, solve
from app.services.pricing import PriceProvider, best_quote
from app.services.pricing.bls import BLSPriceProvider
from app.services.pricing.kroger import KrogerPriceProvider
from app.services.pricing.receipt import ReceiptPriceProvider

log = logging.getLogger(__name__)

SLOTS_PER_DAY = {"breakfast": 1, "lunch": 1, "dinner": 1}
LOW_CONFIDENCE = 0.7


async def scan_inventory(
    ctx: dict[str, Any], user_id: str, image_path: str, media_type: str, kind: str
) -> int:
    image = await storage.download_image(image_path)
    extraction = await claude.extract_inventory(image, media_type, kind)  # type: ignore[arg-type]
    source = "receipt" if kind == "receipt" else kind
    async with SessionLocal() as session:
        for item in extraction.items:
            session.add(
                InventoryItem(
                    user_id=uuid.UUID(user_id),
                    name=item.name,
                    quantity=item.quantity,
                    unit=item.unit,
                    expires_on=item.estimated_expiry,
                    source=source,
                    confidence=item.confidence,
                    needs_confirmation=item.confidence < LOW_CONFIDENCE,
                    price_paid=Decimal(str(item.price_paid)) if item.price_paid else None,
                )
            )
        await session.commit()
    return len(extraction.items)


async def generate_plan(
    ctx: dict[str, Any], plan_id: str, swap_meal_ids: list[str] | None = None
) -> str:
    async with SessionLocal() as session:
        plan = await session.get(MealPlan, uuid.UUID(plan_id))
        if plan is None:
            return "missing"
        plan.status = "running"
        await session.commit()
        try:
            await _build_plan(session, plan, set(swap_meal_ids or []), ctx["http"])
            plan.status, plan.error = "ready", None
            result = "ready"
        except Exception as exc:  # surface any failure to the app instead of a stuck "running"
            log.exception("plan %s failed", plan_id)
            await session.rollback()
            await session.execute(
                update(MealPlan)
                .where(MealPlan.id == uuid.UUID(plan_id))
                .values(status="failed", error=str(exc))
            )
            result = "failed"
        await session.commit()
        return result


async def _build_plan(
    session: AsyncSession, plan: MealPlan, swap_ids: set[str], http: httpx.AsyncClient
) -> None:
    profile = await session.get(Profile, plan.user_id)
    assert profile is not None
    exclusions = [
        e.name
        for e in await session.scalars(
            select(ExcludedFood).where(ExcludedFood.user_id == plan.user_id)
        )
    ]
    inventory = list(
        await session.scalars(
            select(InventoryItem).where(
                InventoryItem.user_id == plan.user_id, InventoryItem.needs_confirmation.is_(False)
            )
        )
    )
    ratings = (
        await session.execute(
            select(Recipe.title, RecipeRating.stars, RecipeRating.comment)
            .join(Recipe, Recipe.id == RecipeRating.recipe_id)
            .where(RecipeRating.user_id == plan.user_id)
            .order_by(RecipeRating.created_at.desc())
            .limit(30)
        )
    ).all()

    locked = [m for m in plan.meals if m.locked]
    swap_titles = [m.recipe.title for m in plan.meals if str(m.id) in swap_ids]
    for meal in [m for m in plan.meals if not m.locked]:
        plan.meals.remove(meal)

    # 1. Claude drafts candidates
    candidates = await claude.propose_recipes(
        {
            "goals": {
                "daily_calories": profile.calorie_goal,
                "daily_protein_g": profile.protein_goal_g,
                "servings_per_meal": profile.servings,
                "weekly_budget_usd": str(profile.weekly_budget),
                "preferred_store": profile.preferred_store,
            },
            "cooking": {
                "cook_days": profile.cook_days,
                "minutes_per_session": profile.minutes_per_session,
                "equipment": profile.equipment,
            },
            "preferences": profile.preferences,
            "excluded_foods": exclusions,
            "inventory": [
                {"name": i.name, "quantity": i.quantity, "unit": i.unit, "expires_on": i.expires_on}
                for i in inventory
            ],
            "past_ratings": [{"recipe": t, "stars": s, "comment": c} for t, s, c in ratings],
            "keep_these_locked_meals": [m.recipe.title for m in locked],
            "replace_these_meals": swap_titles,
            "slots_per_day": SLOTS_PER_DAY,
            "num_candidates": 12,
        }
    )

    # 2. Validation: hard-enforce exclusions
    drafts = [
        d for d in candidates.recipes if is_allowed([i.name for i in d.ingredients], exclusions)
    ]

    # 3. Pricing
    providers: list[PriceProvider] = [
        ReceiptPriceProvider(session, plan.user_id),
        KrogerPriceProvider(http),
        BLSPriceProvider(http),
    ]
    priced: dict[str, tuple[DraftRecipe, int, list[dict[str, Any]]]] = {}
    for idx, draft in enumerate(drafts):
        cost_cents, groceries = 0, []
        for ing in draft.ingredients:
            if ing.from_inventory:
                continue
            quote = await best_quote(ing.name, providers, zip_code=profile.zip_code)
            if quote is None:
                continue  # TODO: unknown price → ask Claude for an estimate or flag in the UI
            # TODO: proper unit conversion between recipe units and the quote's unit.
            price = (
                quote.unit_price * Decimal(str(ing.quantity))
                if quote.unit == ing.unit
                else quote.unit_price
            )
            cost_cents += int(price * 100)
            groceries.append(
                {
                    "name": ing.name,
                    "quantity": ing.quantity,
                    "unit": ing.unit,
                    "price": str(price.quantize(Decimal("0.01"))),
                    "price_source": quote.source,
                }
            )
        priced[f"d{idx}"] = (draft, max(cost_cents // max(draft.servings, 1), 0), groceries)

    # 4. Optimize
    locked_candidates = [
        Candidate(
            f"l{m.id}",
            m.slot,
            0,
            int(m.recipe.calories_per_serving),
            int(m.recipe.protein_g_per_serving),
        )
        for m in locked
    ]
    result = solve(
        PlanRequest(
            candidates=[
                Candidate(
                    k, d.slot, cost, int(d.calories_per_serving), int(d.protein_g_per_serving)
                )
                for k, (d, cost, _) in priced.items()
            ]
            + locked_candidates,
            slots_per_day=SLOTS_PER_DAY,
            people=profile.servings,
            budget_cents=int(profile.weekly_budget * 100),
            calorie_goal=profile.calorie_goal,
            protein_goal_g=profile.protein_goal_g,
            locked_servings={c.key: 1 for c in locked_candidates},
        )
    )
    if not result.feasible:
        raise RuntimeError(f"No plan fits the budget and goals ({result.status})")

    # Persist chosen recipes and lay servings out across the week.
    taken: dict[str, set[int]] = defaultdict(set)
    for m in locked:
        taken[m.slot].add(m.day)
    grocery_list: list[dict[str, Any]] = []
    for key, servings in result.servings.items():
        if key.startswith("l"):
            continue
        draft, _, groceries = priced[key]
        recipe = Recipe(
            user_id=plan.user_id,
            title=draft.title,
            servings=draft.servings,
            calories_per_serving=draft.calories_per_serving,
            protein_g_per_serving=draft.protein_g_per_serving,
            minutes=draft.minutes,
            ingredients=[i.model_dump() for i in draft.ingredients],
            steps=draft.steps,
        )
        session.add(recipe)
        await session.flush()
        free_days = [d for d in range(7) if d not in taken[draft.slot]]
        for day in free_days[: servings // max(profile.servings, 1)]:
            taken[draft.slot].add(day)
            plan.meals.append(PlannedMeal(recipe_id=recipe.id, day=day, slot=draft.slot))
        grocery_list.extend(groceries)

    plan.grocery_list = grocery_list
    plan.estimated_total = Decimal(result.total_cost_cents) / 100
    plan.cooking_timeline = _timeline(plan.week_start, profile.cook_days, plan.meals)


def _timeline(week_start: date, cook_days: list[int], meals: list[PlannedMeal]) -> list[dict]:
    """Assign each meal to the most recent cook session on or before its day."""
    days = sorted(cook_days) or [6]
    sessions: dict[int, set[str]] = defaultdict(set)
    for meal in meals:
        earlier = [d for d in days if d <= meal.day]
        sessions[earlier[-1] if earlier else days[-1]].add(str(meal.recipe_id))
    return [
        {"date": str(week_start + timedelta(days=d)), "recipe_ids": sorted(ids)}
        for d, ids in sorted(sessions.items())
    ]


async def carry_over_inventory(ctx: dict[str, Any]) -> None:
    """TODO (weekly cron): subtract what the plan used, drop expired items, keep the rest."""
