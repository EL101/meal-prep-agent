from evals.metrics import PlannedServing, score


def test_score_flags_allergens_budget_and_waste():
    servings = [
        PlannedServing("PB toast", "breakfast", 500, 20, 2.0, ["peanut butter", "bread"]),
        PlannedServing("Spinach eggs", "lunch", 500, 30, 1.0, ["spinach", "eggs"]),
    ]
    r = score(
        servings,
        days=1,
        budget=2.5,
        calorie_goal=1000,
        protein_goal_g=50,
        excluded=["peanut"],
        expiring_inventory=["spinach", "milk"],
    )
    assert r.allergen_violations == 1
    assert r.budget_violation
    assert r.calorie_error_pct == 0
    assert r.protein_error_pct == 0
    assert r.food_waste_pct == 50
