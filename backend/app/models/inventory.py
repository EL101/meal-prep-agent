import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import IdMixin, TimestampMixin


class InventoryItem(IdMixin, TimestampMixin, Base):
    __tablename__ = "inventory_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.user_id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[float] = mapped_column(default=1.0)
    unit: Mapped[str] = mapped_column(String(20), default="each")
    expires_on: Mapped[date | None]

    # fridge | pantry | receipt | manual | carryover
    source: Mapped[str] = mapped_column(String(20), default="manual")
    confidence: Mapped[float] = mapped_column(default=1.0)
    needs_confirmation: Mapped[bool] = mapped_column(default=False)
    price_paid: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
