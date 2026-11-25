from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol

PriceSource = Literal["receipt", "kroger_estimate", "bls_estimate"]


@dataclass(frozen=True)
class PriceQuote:
    item: str
    unit_price: Decimal
    unit: str
    source: PriceSource

    @property
    def is_estimate(self) -> bool:
        return self.source != "receipt"


class PriceProvider(Protocol):
    async def quote(self, item: str, *, zip_code: str | None = None) -> PriceQuote | None: ...
