"""Runs the full plan pipeline with Claude stubbed out."""

import httpx
import pytest

from app.models import ExcludedFood, MealPlan, Profile
from app.schemas.llm import DraftIngredient, DraftRecipe, RecipeCandidates
from app.worker import tasks
from tests.conftest import USER_ID


def _recipe(title, slot, kcal, protein, *ingredients):
    return DraftRecipe(
        title=title,
        servings=4,
        minutes=30,
        calories_per_serving=kcal,
        protein_g_per_serving=protein,
        slot=slot,
        steps=["Cook it."],
        ingredients=[
            DraftIngredient(name=i, quantity=1, unit="each", from_inventory=True)
            for i in ingredients
        ],
    )


CANDIDATES = RecipeCandidates(
    recipes=[
        _recipe("Overnight oats", "breakfast", 450, 25, "oats", "milk"),
        _recipe("Egg scramble", "breakfast", 400, 30, "eggs", "spinach"),
        _recipe("Chicken rice bowl", "lunch", 700, 55, "chicken breast", "rice"),
        _recipe("Peanut noodles", "lunch", 650, 25, "peanut butter", "noodles"),
        _recipe("Turkey chili", "dinner", 750, 50, "ground turkey", "beans"),
    ]
)


@pytest.fixture
def stub_claude(monkeypatch):
    async def fake_propose(context):
        assert "peanut" in context["excluded_foods"]
        return CANDIDATES

    monkeypatch.setattr(tasks.claude, "propose_recipes", fake_propose)


async def test_generate_plan_respects_exclusions(sessionmaker, monkeypatch, stub_claude):
    monkeypatch.setattr(tasks, "SessionLocal", sessionmaker)
    async with sessionmaker() as s:
        s.add(Profile(user_id=USER_ID, calorie_goal=1900, protein_goal_g=120))
        s.add(ExcludedFood(user_id=USER_ID, name="peanut", reason="allergy"))
        plan = MealPlan(user_id=USER_ID, week_start=tasks.date(2026, 11, 30))
        s.add(plan)
        await s.commit()

    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(404)))
    assert await tasks.generate_plan({"http": http}, str(plan.id)) == "ready"

    async with sessionmaker() as s:
        saved = await s.get(MealPlan, plan.id)
        assert saved is not None and saved.status == "ready"
        assert len(saved.meals) == 21
        assert all("Peanut" not in m.recipe.title for m in saved.meals)
