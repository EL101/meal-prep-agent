from app.services.optimizer import Candidate, PlanRequest, solve

CANDIDATES = [
    Candidate("oats", "breakfast", 80, 450, 25),
    Candidate("eggs", "breakfast", 150, 400, 30),
    Candidate("chicken_rice", "lunch", 300, 700, 55),
    Candidate("bean_chili", "lunch", 180, 650, 35),
    Candidate("salmon_bowl", "dinner", 650, 750, 50),
    Candidate("turkey_pasta", "dinner", 320, 800, 50),
]


def _request(**kw):
    defaults = dict(
        candidates=CANDIDATES,
        slots_per_day={"breakfast": 1, "lunch": 1, "dinner": 1},
        budget_cents=6000,
        calorie_goal=2000,
        protein_goal_g=130,
    )
    return PlanRequest(**(defaults | kw))


def test_fills_every_slot_within_budget():
    result = solve(_request())
    assert result.feasible
    assert sum(result.servings.values()) == 21
    assert result.total_cost_cents <= 6000


def test_infeasible_budget_is_reported():
    assert not solve(_request(budget_cents=500)).feasible


def test_locked_servings_are_kept():
    result = solve(_request(budget_cents=10000, locked_servings={"salmon_bowl": 3}))
    assert result.servings.get("salmon_bowl", 0) >= 3
