"""Hard enforcement of excluded foods (allergies and dislikes).

The prompt asks Claude to avoid these, but this module is the guarantee: any recipe whose
ingredients match an exclusion is dropped before the optimizer ever sees it.
"""

import re
from collections.abc import Iterable

# Expand common allergen categories into ingredient words. Extend as needed, and use
# Open Food Facts (services/nutrition/open_food_facts.py) for packaged-product allergens.
ALLERGEN_GROUPS: dict[str, set[str]] = {
    "dairy": {"milk", "cheese", "butter", "cream", "yogurt", "whey", "casein", "ghee"},
    "egg": {"egg", "mayonnaise", "meringue"},
    "peanut": {"peanut"},
    "tree nut": {"almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut", "macadamia"},
    "shellfish": {"shrimp", "crab", "lobster", "prawn", "scallop", "clam", "mussel", "oyster"},
    "fish": {"salmon", "tuna", "cod", "tilapia", "anchovy", "sardine", "fish"},
    "soy": {"soy", "tofu", "edamame", "tempeh", "miso"},
    "gluten": {"wheat", "flour", "bread", "pasta", "barley", "rye", "couscous", "seitan"},
    "sesame": {"sesame", "tahini"},
}


def _variants(word: str) -> set[str]:
    """The word plus its likely singular forms ("berries" -> "berry", "olives" -> "olive")."""
    w = word.lower()
    out = {w}
    if w.endswith("ies") and len(w) > 4:
        out.add(w[:-3] + "y")
    if w.endswith("es") and len(w) > 3:
        out.add(w[:-2])
    if w.endswith("s") and len(w) > 2:
        out.add(w[:-1])
    return out


def _words(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z]+", text)]


def expand_exclusions(excluded: Iterable[str]) -> list[tuple[str, ...]]:
    """Turn user exclusions into word phrases. Allergen groups expand to their members."""
    phrases: list[tuple[str, ...]] = []
    for item in excluded:
        key = item.lower().strip()
        group = ALLERGEN_GROUPS.get(key) or ALLERGEN_GROUPS.get(key.rstrip("s"))
        if group:
            phrases.extend((member,) for member in group)
        elif words := _words(key):
            phrases.append(tuple(words))
    return phrases


def _matches(ingredient: str, phrase: tuple[str, ...]) -> bool:
    forms = set().union(*(_variants(w) for w in _words(ingredient))) if ingredient else set()
    return all(_variants(w) & forms for w in phrase)


def violations(ingredient_names: Iterable[str], excluded: Iterable[str]) -> list[str]:
    """Return the ingredient names that hit an exclusion (empty list means safe)."""
    phrases = expand_exclusions(excluded)
    return [name for name in ingredient_names if any(_matches(name, p) for p in phrases)]


def is_allowed(ingredient_names: Iterable[str], excluded: Iterable[str]) -> bool:
    return not violations(ingredient_names, excluded)
