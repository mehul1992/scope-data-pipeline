"""
DimCurrency — currency classification dimension.

Satisfies requirement #5: data classification for currencies.
Normalised lookup — avoids raw currency strings in every snapshot.
Supports multi-currency data (EUR, CHF from real files).
"""
from __future__ import annotations

from uuid import UUID
from typing import TYPE_CHECKING
from sqlalchemy import Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
if TYPE_CHECKING:
    from app.models.snapshot_fact import SnapshotFact


class DimCurrency(Base, TimestampMixin):
    __tablename__ = "dim_currency"

    currency_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ISO 4217 currency code — EUR, CHF, USD, GBP
    currency_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True,
    )

    currency_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    # symbol for BI display
    symbol: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    snapshots: Mapped[list["SnapshotFact"]] = relationship(
        "SnapshotFact",
        foreign_keys="SnapshotFact.currency_id",
        back_populates="currency"
    )

    __table_args__ = (
        Index("ix_dim_currency_code", "currency_code"),
    )

    def __repr__(self) -> str:
        return f"<DimCurrency currency_code={self.currency_code!r}>"