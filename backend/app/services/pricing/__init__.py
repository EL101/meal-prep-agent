import logging

import httpx

from app.services.pricing.base import PriceProvider, PriceQuote

log = logging.getLogger(__name__)


async def best_quote(
    item: str, providers: list[PriceProvider], *, zip_code: str | None = None
) -> PriceQuote | None:
    """Try providers in order of accuracy: receipt → Kroger estimate → BLS estimate."""
    for provider in providers:
        try:
            if quote := await provider.quote(item, zip_code=zip_code):
                return quote
        except httpx.HTTPError as exc:  # one flaky source shouldn't sink the whole plan
            log.warning("%s failed for %r: %s", type(provider).__name__, item, exc)
    return None


__all__ = ["PriceProvider", "PriceQuote", "best_quote"]
