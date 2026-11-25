"""Kroger Products API (https://developer.kroger.com). Prices are labeled as estimates."""

import time
from decimal import Decimal

import httpx

from app.config import get_settings
from app.services.pricing.base import PriceQuote

TOKEN_URL = "https://api.kroger.com/v1/connect/oauth2/token"
LOCATIONS_URL = "https://api.kroger.com/v1/locations"
PRODUCTS_URL = "https://api.kroger.com/v1/products"


class KrogerPriceProvider:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client
        self._token: str | None = None
        self._token_expires = 0.0

    async def _access_token(self) -> str:
        if self._token and time.time() < self._token_expires - 60:
            return self._token
        s = get_settings()
        resp = await self.client.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials", "scope": "product.compact"},
            auth=(s.kroger_client_id, s.kroger_client_secret),
        )
        resp.raise_for_status()
        body = resp.json()
        self._token, self._token_expires = body["access_token"], time.time() + body["expires_in"]
        return self._token

    async def _location_id(self, zip_code: str, headers: dict[str, str]) -> str | None:
        resp = await self.client.get(
            LOCATIONS_URL,
            params={"filter.zipCode.near": zip_code, "filter.limit": 1},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json().get("data") or []
        return data[0]["locationId"] if data else None

    async def quote(self, item: str, *, zip_code: str | None = None) -> PriceQuote | None:
        s = get_settings()
        if not (s.kroger_client_id and s.kroger_client_secret and zip_code):
            return None
        headers = {"Authorization": f"Bearer {await self._access_token()}"}
        location = await self._location_id(zip_code, headers)
        if location is None:
            return None
        resp = await self.client.get(
            PRODUCTS_URL,
            params={"filter.term": item, "filter.locationId": location, "filter.limit": 1},
            headers=headers,
        )
        resp.raise_for_status()
        for product in resp.json().get("data", []):
            for entry in product.get("items", []):
                price = (entry.get("price") or {}).get("regular")
                if price:
                    return PriceQuote(
                        item, Decimal(str(price)), entry.get("size", "each"), "kroger_estimate"
                    )
        return None
