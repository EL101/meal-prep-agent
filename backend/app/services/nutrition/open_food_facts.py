"""Open Food Facts: allergen tags for packaged products (by barcode or search)."""

import httpx

PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
# OFF asks API clients to identify themselves with a descriptive User-Agent.
HEADERS = {"User-Agent": "MealPrepAgent/0.1"}


def _clean(tags: list[str]) -> set[str]:
    return {t.split(":", 1)[-1].replace("-", " ") for t in tags}


async def allergens_for_barcode(client: httpx.AsyncClient, barcode: str) -> set[str]:
    resp = await client.get(
        PRODUCT_URL.format(barcode=barcode),
        params={"fields": "allergens_tags,traces_tags"},
        headers=HEADERS,
    )
    resp.raise_for_status()
    product = resp.json().get("product") or {}
    return _clean(product.get("allergens_tags", []) + product.get("traces_tags", []))


async def allergens_for_name(client: httpx.AsyncClient, name: str) -> set[str]:
    resp = await client.get(
        SEARCH_URL,
        params={"search_terms": name, "json": 1, "page_size": 1, "fields": "allergens_tags"},
        headers=HEADERS,
    )
    resp.raise_for_status()
    products = resp.json().get("products") or []
    return _clean(products[0].get("allergens_tags", [])) if products else set()
