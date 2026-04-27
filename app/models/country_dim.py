"""
DimCountry — country classification dimension.

Satisfies requirement #5: data classification for countries.
Normalised lookup table — avoids storing raw country strings
in every snapshot row.
"""
from __future__ import annotations

from uuid import UUID
from typing import TYPE_CHECKING
from sqlalchemy import Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.snapshot_fact import SnapshotFact


class DimCountry(Base, TimestampMixin):
    __tablename__ = "dim_country"

    country_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # full country name from MASTER sheet "Country of origin"
    country_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )

    # optional ISO codes for BI tool integration
    iso_alpha2: Mapped[str | None] = mapped_column(Text, nullable=True)
    iso_alpha3: Mapped[str | None] = mapped_column(Text, nullable=True)

    # region grouping for BI filtering
    region: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    snapshots: Mapped[list["SnapshotFact"]] = relationship(
        "SnapshotFact",
        foreign_keys="SnapshotFact.country_id",
        back_populates="country"
    )

    __table_args__ = (
        Index("ix_dim_country_name", "country_name"),
    )

    def __repr__(self) -> str:
        return f"<DimCountry country_name={self.country_name!r}>"