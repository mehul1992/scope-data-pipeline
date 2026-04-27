from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.base import Base, TimestampMixin

# Do not import snapshot_fact here — it imports UploadAudit and would create a
# circular import. relationship() targets use string forward refs below.


class UploadAudit(Base, TimestampMixin):
    __tablename__ = "upload_audit"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_upload_audit_status",
        ),
        Index("ix_upload_audit_file_sha256", "file_sha256"),
        Index("ix_upload_audit_status", "status"),
        Index("ix_upload_audit_uploaded_at", "uploaded_at"),
    )

    upload_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    rows_extracted: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    snapshots: Mapped[list["SnapshotFact"]] = relationship(
        "SnapshotFact",
        foreign_keys="SnapshotFact.upload_id",
        back_populates="upload",
        lazy="select",
    )
    quality_report: Mapped["DataQualityReport"] = relationship(
        "DataQualityReport",
        foreign_keys="DataQualityReport.upload_id",
        back_populates="upload",
        uselist=False,
        lazy="select",
    )

    def __repr__(self) -> str:
        return (
            f"<UploadAudit filename={self.filename!r} "
            f"status={self.status!r}>"
        )
