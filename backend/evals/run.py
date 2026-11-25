"""Compare the three pipeline variants from the README on every case in evals/cases/.

    uv run python -m evals.run                 # all cases, all arms
    uv run python -m evals.run --arm optimizer

Arms:
  claude_only  Claude's candidates, first ones per slot, no checks
  validation   + exclusion filter
  optimizer    + exclusion filter + OR-Tools solve

Each case makes one real Claude call (shared by all arms), so a run costs real money.
Prices come from the case file to keep runs reproducible.
"""

import argparse
import asyncio
import json
from pathlib import Path

from app.schemas.llm import DraftRecipe
from app.services import claude
from app.services.exclusions import is_allowed
from app.services.optimizer import Candidate, PlanRequest, solve
from evals.metrics import PlannedServing, score

CASES = Path(__file__).parent / "cases"
SLOTS = {"breakfast": 1, "lunch": 1, "dinner": 1}
DAYS = 7


def _cost_per_serving(recipe: DraftRecipe, prices: dict[str, float], default: float) -> float:
    total = sum(
        prices.get(i.name.lower(), default) for i in recipe.ingredients if not i.from_inventory
    )
    return total / max(recipe.servings, 1)


def _serving(r: DraftRecipe, cost: float) -> PlannedServing:
    return PlannedServing(
        r.title,
        r.slot,
        r.calories_per_serving,
        r.protein_g_per_serving,
        cost,
        [i.name for i in r.ingredients],
    )


def _naive(recipes: list[DraftRecipe], costs: list[float]) -> list[PlannedServing]:
    """Round-robin Claude's recipes into every slot, like a plan with no solver."""
    out: list[PlannedServing] = []
    for slot, per_day in SLOTS.items():
        pool = [(r, c) for r, c in zip(recipes, costs, strict=True) if r.slot == slot]
        for n in range(per_day * DAYS):
            if pool:
                r, c = pool[n % len(pool)]
                out.append(_serving(r, c))
    return out


def _optimized(recipes, costs, profile) -> list[PlannedServing]:
    result = solve(
        PlanRequest(
            candidates=[
                Candidate(
                    str(i),
                    r.slot,
                    int(c * 100),
                    int(r.calories_per_serving),
                    int(r.protein_g_per_serving),
                )
                for i, (r, c) in enumerate(zip(recipes, costs, strict=True))
            ],
            slots_per_day=SLOTS,
            budget_cents=int(profile["weekly_budget"] * 100),
            calorie_goal=profile["calorie_goal"],
            protein_goal_g=profile["protein_goal_g"],
        )
    )
    return [
        _serving(recipes[int(k)], costs[int(k)])
        for k, n in result.servings.items()
        for _ in range(n)
    ]


async def run_case(case: dict, arms: list[str]) -> dict[str, dict[str, object]]:
    profile = case["profile"]
    candidates = await claude.propose_recipes(
        {
            "goals": profile,
            "excluded_foods": case["excluded_foods"],
            "inventory": case["inventory"],
            "slots_per_day": SLOTS,
            "num_candidates": 12,
        }
    )
    recipes = candidates.recipes
    allowed = [
        r for r in recipes if is_allowed([i.name for i in r.ingredients], case["excluded_foods"])
    ]

    def costs(rs: list[DraftRecipe]) -> list[float]:
        return [_cost_per_serving(r, case["prices"], case["default_price"]) for r in rs]

    plans = {
        "claude_only": lambda: _naive(recipes, costs(recipes)),
        "validation": lambda: _naive(allowed, costs(allowed)),
        "optimizer": lambda: _optimized(allowed, costs(allowed), profile),
    }
    expiring = [i["name"] for i in case["inventory"] if i.get("expires_on")]
    return {
        arm: score(
            plans[arm](),
            days=DAYS,
            budget=profile["weekly_budget"],
            calorie_goal=profile["calorie_goal"],
            protein_goal_g=profile["protein_goal_g"],
            excluded=case["excluded_foods"],
            expiring_inventory=expiring,
        ).as_dict()
        for arm in arms
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--arm", choices=["claude_only", "validation", "optimizer"], action="append"
    )
    args = parser.parse_args()
    arms = args.arm or ["claude_only", "validation", "optimizer"]
    cases = {p.stem: json.loads(p.read_text()) for p in sorted(CASES.glob("*.json"))}
    report = {name: await run_case(case, arms) for name, case in cases.items()}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
