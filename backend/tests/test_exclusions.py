from app.services.exclusions import is_allowed, violations


def test_allergen_group_expands():
    assert violations(["cheddar cheese", "chicken breast"], ["dairy"]) == ["cheddar cheese"]


def test_plurals_match():
    assert not is_allowed(["2 large eggs"], ["egg"])
    assert not is_allowed(["fresh strawberries"], ["strawberry"])
    assert not is_allowed(["kalamata olives"], ["olive"])


def test_multi_word_exclusion_is_a_phrase():
    assert not is_allowed(["light sour cream"], ["sour cream"])
    assert is_allowed(["heavy cream", "sourdough bread"], ["sour cream"])


def test_safe_recipe():
    assert is_allowed(["rice", "black beans", "chicken thigh"], ["peanut", "shellfish"])
