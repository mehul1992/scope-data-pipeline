"""
DimDate — date dimension for time-series analysis.

Satisfies requirement #6: time-series data availability.
Satisfies requirement #3: time-series analysis of individual companies.

Pre-populated with dates for the credit metrics year range (2018-2030).
Enables efficient date-based filtering in BI tools without date parsing.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DimDate(Base):
    __tablename__ = "dim_date"

    date_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # year value — integer for actual years, string for estimates
    year_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True,
    )

    # actual calendar year (NULL for estimated years like 2025E)
    calendar_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # whether this is a forecast/estimate year (2025E, 2026E, 2027E)
    is_estimate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # sort order for time-series display
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_dim_date_year_value", "year_value"),
        Index("ix_dim_date_sort_order", "sort_order"),
    )

    def __repr__(self) -> str:
        return (
            f"<DimDate year_value={self.year_value!r} "
            f"is_estimate={self.is_estimate}>"
        )