"""Most accurate source: what the user actually paid, from scanned receipts."""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import InventoryItem
from app.services.pricing.base import PriceQuote


class ReceiptPriceProvider:
    def __init__(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def quote(self, item: str, *, zip_code: str | None = None) -> PriceQuote | None:
        row = await self.session.scalar(
            select(InventoryItem)
            .where(
                InventoryItem.user_id == self.user_id,
                InventoryItem.source == "receipt",
                InventoryItem.price_paid.is_not(None),
                InventoryItem.name.ilike(item),
            )
            .order_by(InventoryItem.created_at.desc())
            .limit(1)
        )
        if row is None or row.price_paid is None or not row.quantity:
            return None
        unit_price = (row.price_paid / Decimal(str(row.quantity))).quantize(Decimal("0.01"))
        return PriceQuote(item, unit_price, row.unit, "receipt")
