"""
SnapshotFact — central fact table of the star schema.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ARRAY, DateTime, ForeignKey, Index, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.company_dim import CompanyVersion, DimCompany
    from app.models.country_dim import DimCountry
    from app.models.currency_dim import DimCurrency
    from app.models.upload_dim import UploadAudit


class SnapshotFact(Base):
    __tablename__ = "snapshot_fact"

    snapshot_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ── foreign keys ──────────────────────────────────────────
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("company_versions.version_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("dim_company.company_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    upload_id: Mapped[UUID] = mapped_column(
        ForeignKey("upload_audit.upload_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    country_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dim_country.country_id", ondelete="SET NULL"),
        nullable=True,
    )
    currency_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dim_currency.currency_id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── entity metadata ───────────────────────────────────────
    entity_name: Mapped[str] = mapped_column(Text, nullable=False)
    corporate_sector: Mapped[str | None] = mapped_column(Text, nullable=True)
    country_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    accounting_principles: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_year_end: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── rating methodology ────────────────────────────────────
    rating_methodologies: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text), nullable=True,
    )

    # ── industry risk ─────────────────────────────────────────
    industry_risk_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry_risk_score: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry_weight: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    segmentation_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── risk profiles ─────────────────────────────────────────
    business_risk_profile: Mapped[str | None] = mapped_column(Text, nullable=True)
    financial_risk_profile: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── JSONB fields ──────────────────────────────────────────
    risk_sub_scores: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb"),
    )
    credit_metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb"),
    )
    raw_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=True, server_default=text("'{}'::jsonb"),
    )

    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )

    # ── relationships — all with explicit foreign_keys ────────
    company: Mapped["DimCompany"] = relationship(
        "DimCompany",
        foreign_keys=[company_id],
        back_populates="snapshots",
    )
    version: Mapped["CompanyVersion"] = relationship(
        "CompanyVersion",
        foreign_keys=[version_id],
        back_populates="snapshot",
    )
    upload: Mapped["UploadAudit"] = relationship(
        "UploadAudit",
        foreign_keys=[upload_id],
        back_populates="snapshots",
    )
    country: Mapped["DimCountry | None"] = relationship(
        "DimCountry",
        foreign_keys=[country_id],
        back_populates="snapshots",
    )
    currency: Mapped["DimCurrency | None"] = relationship(
        "DimCurrency",
        foreign_keys=[currency_id],
        back_populates="snapshots",
    )
    quality_report: Mapped["DataQualityReport | None"] = relationship(
        "DataQualityReport",
        foreign_keys="DataQualityReport.snapshot_id",
        back_populates="snapshot",
        uselist=False,
    )

    # ── indexes ───────────────────────────────────────────────
    __table_args__ = (
        Index("ix_snapshot_company_id", "company_id"),
        Index("ix_snapshot_at", "snapshot_at"),
        Index("ix_snapshot_sector", "corporate_sector"),
        Index("ix_snapshot_country", "country_name"),
        Index("ix_snapshot_currency", "currency_code"),
        Index("ix_snapshot_company_time", "company_id", "snapshot_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<SnapshotFact entity={self.entity_name!r} "
            f"snapshot_at={self.snapshot_at}>"
        )


class DataQualityReport(Base):
    __tablename__ = "data_quality_report"

    report_id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    upload_id: Mapped[UUID] = mapped_column(
        ForeignKey("upload_audit.upload_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("snapshot_fact.snapshot_id", ondelete="RESTRICT"),
        nullable=True,
    )
    completeness_score: Mapped[float] = mapped_column(
        Numeric(4, 3), nullable=False, default=0.0,
    )
    validity_score: Mapped[float] = mapped_column(
        Numeric(4, 3), nullable=False, default=0.0,
    )
    total_fields: Mapped[int] = mapped_column(nullable=False, default=0)
    present_fields: Mapped[int] = mapped_column(nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(nullable=False, default=0)
    errors: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"),
    )
    warnings: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("NOW()"),
        nullable=False,
    )

    # relationships — explicit foreign_keys on both
    upload: Mapped["UploadAudit"] = relationship(
        foreign_keys=[upload_id],
        back_populates="quality_report",
    )
    snapshot: Mapped["SnapshotFact | None"] = relationship(
        foreign_keys=[snapshot_id],
        back_populates="quality_report",
    )

    def __repr__(self) -> str:
        return (
            f"<DataQualityReport upload_id={self.upload_id} "
            f"completeness={self.completeness_score}>"
        )