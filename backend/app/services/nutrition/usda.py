"""USDA FoodData Central: per-100 g nutrition facts used to check Claude's macro estimates."""

from dataclasses import dataclass

import httpx

from app.config import get_settings

SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# FDC nutrient numbers
ENERGY_KCAL = "208"
PROTEIN = "203"
FAT = "204"
CARBS = "205"


@dataclass(frozen=True)
class NutritionPer100g:
    fdc_id: int
    description: str
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float


async def lookup(client: httpx.AsyncClient, food: str) -> NutritionPer100g | None:
    resp = await client.get(
        SEARCH_URL,
        params={
            "api_key": get_settings().usda_api_key or "DEMO_KEY",
            "query": food,
            "dataType": "Foundation,SR Legacy",
            "pageSize": 1,
        },
    )
    resp.raise_for_status()
    foods = resp.json().get("foods") or []
    if not foods:
        return None
    f = foods[0]
    nutrients = {n.get("nutrientNumber"): n.get("value", 0.0) for n in f.get("foodNutrients", [])}
    return NutritionPer100g(
        fdc_id=f["fdcId"],
        description=f["description"],
        calories=nutrients.get(ENERGY_KCAL, 0.0),
        protein_g=nutrients.get(PROTEIN, 0.0),
        fat_g=nutrients.get(FAT, 0.0),
        carbs_g=nutrients.get(CARBS, 0.0),
    )
