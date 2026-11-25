"""BLS Average Price Data (CPI-U) as a last-resort regional estimate.

Series IDs look like APU0000708111 (eggs, grade A large, per dozen, U.S. city average).
Swap the area code (0000) for a region (0100 Northeast, 0200 Midwest, 0300 South, 0400 West).
"""

from decimal import Decimal

import httpx

from app.config import get_settings
from app.services.pricing.base import PriceQuote

API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# item -> (series item code, unit). Extend as needed.
SERIES: dict[str, tuple[str, str]] = {
    "eggs": ("708111", "dozen"),
    "whole milk": ("709112", "gal"),
    "white bread": ("702111", "lb"),
    "chicken breast": ("706212", "lb"),
    "ground beef": ("703112", "lb"),
    "white rice": ("701312", "lb"),
    "bananas": ("711211", "lb"),
    "potatoes": ("712112", "lb"),
}


class BLSPriceProvider:
    def __init__(self, client: httpx.AsyncClient, area_code: str = "0000") -> None:
        self.client = client
        self.area_code = area_code

    async def quote(self, item: str, *, zip_code: str | None = None) -> PriceQuote | None:
        match = SERIES.get(item.lower())
        if match is None:
            return None
        code, unit = match
        series_id = f"APU{self.area_code}{code}"
        payload: dict[str, object] = {"seriesid": [series_id]}
        if key := get_settings().bls_api_key:
            payload["registrationkey"] = key
        resp = await self.client.post(API_URL, json=payload)
        resp.raise_for_status()
        series = resp.json().get("Results", {}).get("series", [])
        if not series or not series[0].get("data"):
            return None
        latest = series[0]["data"][0]["value"]
        return PriceQuote(item, Decimal(latest), unit, "bls_estimate")
