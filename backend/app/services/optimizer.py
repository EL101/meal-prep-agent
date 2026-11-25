"""Pick the week's recipes and serving counts with Google OR-Tools (CP-SAT).

Claude proposes candidate recipes; this solver turns them into a plan that provably respects
the budget and fills every meal slot, while getting as close as possible to the user's
calorie and protein goals. Locked meals from a previous solve are held fixed.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from ortools.sat.python import cp_model


@dataclass(frozen=True)
class Candidate:
    key: str
    slot: str  # breakfast | lunch | dinner | snack
    cost_per_serving_cents: int  # only what must be bought; inventory items cost 0
    calories: int  # per serving
    protein_g: int  # per serving


@dataclass
class PlanRequest:
    candidates: list[Candidate]
    slots_per_day: dict[str, int]  # e.g. {"breakfast": 1, "lunch": 1, "dinner": 1}
    days: int = 7
    people: int = 1
    budget_cents: int = 7500
    calorie_goal: int = 2200  # per person per day
    protein_goal_g: int = 140
    max_distinct_recipes: int = 5  # keeps cook sessions manageable
    min_batch_servings: int = 2
    locked_servings: dict[str, int] = field(default_factory=dict)


@dataclass
class PlanResult:
    feasible: bool
    servings: dict[str, int]
    total_cost_cents: int
    avg_daily_calories: float
    avg_daily_protein_g: float
    status: str


def solve(req: PlanRequest, time_limit_s: float = 5.0) -> PlanResult:
    m = cp_model.CpModel()
    by_slot: dict[str, list[Candidate]] = defaultdict(list)
    for c in req.candidates:
        by_slot[c.slot].append(c)

    max_servings = req.days * req.people * max(req.slots_per_day.values(), default=1)
    x = {c.key: m.new_int_var(0, max_servings, f"x_{c.key}") for c in req.candidates}
    used = {c.key: m.new_bool_var(f"use_{c.key}") for c in req.candidates}

    for c in req.candidates:
        m.add(x[c.key] <= max_servings * used[c.key])
        m.add(x[c.key] >= req.min_batch_servings * used[c.key])
        if locked := req.locked_servings.get(c.key):
            m.add(x[c.key] >= locked)

    # Every meal slot for every person, every day, gets exactly one serving.
    for slot, per_day in req.slots_per_day.items():
        m.add(sum(x[c.key] for c in by_slot.get(slot, [])) == per_day * req.days * req.people)

    m.add(sum(used.values()) <= req.max_distinct_recipes)

    cost = sum(c.cost_per_serving_cents * x[c.key] for c in req.candidates)
    m.add(cost <= req.budget_cents)

    # Distance from weekly macro targets (per person), linearized with abs vars.
    person_days = req.days * req.people
    kcal = sum(c.calories * x[c.key] for c in req.candidates)
    protein = sum(c.protein_g * x[c.key] for c in req.candidates)
    kcal_target = req.calorie_goal * person_days
    protein_target = req.protein_goal_g * person_days

    kcal_dev = m.new_int_var(0, 10 * kcal_target + 1, "kcal_dev")
    m.add_abs_equality(kcal_dev, kcal - kcal_target)
    protein_short = m.new_int_var(0, protein_target, "protein_short")
    m.add(protein_short >= protein_target - protein)

    # Weights: 1 g protein short ≈ 10 kcal off ≈ 5 cents. Tune with evals.
    m.minimize(kcal_dev * 2 + protein_short * 20 + cost)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    status = solver.solve(m)
    feasible = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    if not feasible:
        return PlanResult(False, {}, 0, 0.0, 0.0, solver.status_name(status))

    servings = {k: int(solver.value(v)) for k, v in x.items() if solver.value(v) > 0}
    return PlanResult(
        feasible=True,
        servings=servings,
        total_cost_cents=int(solver.value(cost)),
        avg_daily_calories=solver.value(kcal) / person_days,
        avg_daily_protein_g=solver.value(protein) / person_days,
        status=solver.status_name(status),
    )
