"""Metrics from the README: budget violations, calorie/protein error, allergen violations,
cost per day, food waste, taste ratings."""

from dataclasses import asdict, dataclass

from app.services.exclusions import violations


@dataclass
class PlannedServing:
    title: str
    slot: str
    calories: float
    protein_g: float
    cost: float  # dollars per serving
    ingredients: list[str]


@dataclass
class CaseResult:
    budget_violation: bool
    calorie_error_pct: float
    protein_error_pct: float
    allergen_violations: int
    cost_per_day: float
    food_waste_pct: float
    taste_rating: float | None  # filled from user ratings / human review, not computed here

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def score(
    servings: list[PlannedServing],
    *,
    days: int,
    budget: float,
    calorie_goal: float,
    protein_goal_g: float,
    excluded: list[str],
    expiring_inventory: list[str],
) -> CaseResult:
    total_cost = sum(s.cost for s in servings)
    kcal_per_day = sum(s.calories for s in servings) / days
    protein_per_day = sum(s.protein_g for s in servings) / days
    used = {i.lower() for s in servings for i in s.ingredients}
    wasted = [i for i in expiring_inventory if i.lower() not in used]
    return CaseResult(
        budget_violation=total_cost > budget + 1e-9,
        calorie_error_pct=abs(kcal_per_day - calorie_goal) / calorie_goal * 100,
        protein_error_pct=abs(protein_per_day - protein_goal_g) / protein_goal_g * 100,
        allergen_violations=sum(1 for s in servings if violations(s.ingredients, excluded)),
        cost_per_day=total_cost / days,
        food_waste_pct=(len(wasted) / len(expiring_inventory) * 100) if expiring_inventory else 0,
        taste_rating=None,
    )
