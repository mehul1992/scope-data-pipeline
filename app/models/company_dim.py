"""
DimCompany — slowly changing dimension for corporate entities.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.snapshot_fact import SnapshotFact


class DimCompany(Base, TimestampMixin):
    __tablename__ = "dim_company"

    company_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    entity_name: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True, index=True,
    )

    current_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("snapshot_fact.snapshot_id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    versions: Mapped[list["CompanyVersion"]] = relationship(
        "CompanyVersion",
        foreign_keys="CompanyVersion.company_id",      
        back_populates="company",
        order_by="CompanyVersion.version_number",
    )
    snapshots: Mapped[list["SnapshotFact"]] = relationship(
        "SnapshotFact",
        foreign_keys="SnapshotFact.company_id",
        back_populates="company",
    )

    current_snapshot: Mapped["SnapshotFact | None"] = relationship(
        "SnapshotFact",
        foreign_keys=[current_snapshot_id],
        back_populates="company",
        uselist=False,
    )

    __table_args__ = (
        Index("ix_dim_company_entity_name", "entity_name"),
    )

    def __repr__(self) -> str:
        return f"<DimCompany entity_name={self.entity_name!r}>"


class CompanyVersion(Base):
    __tablename__ = "company_versions"

    version_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("dim_company.company_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    upload_id: Mapped[UUID] = mapped_column(
        ForeignKey("upload_audit.upload_id", ondelete="RESTRICT"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )
    valid_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )

    company: Mapped["DimCompany"] = relationship(
        "DimCompany",
        foreign_keys=[company_id],       # fixed
        back_populates="versions",
    )
    snapshot: Mapped["SnapshotFact | None"] = relationship(
        "SnapshotFact",
        foreign_keys="SnapshotFact.version_id",        
        back_populates="version",
        uselist=False,
    )

    __table_args__ = (
        Index("ix_company_versions_company_id", "company_id"),
        Index("ix_company_versions_is_current", "company_id", "is_current"),
        Index(
            "ix_company_versions_temporal",
            "company_id", "valid_from", "valid_to",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyVersion company_id={self.company_id} "
            f"v{self.version_number} current={self.is_current}>"
        )