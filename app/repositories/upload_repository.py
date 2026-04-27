from uuid import UUID

from sqlalchemy import case, func, select

from app.models.upload_dim import UploadAudit
from app.repositories.base_repository import BaseRepository


class UploadRepository(BaseRepository):
    def list_uploads(self) -> list[UploadAudit]:
        stmt = select(UploadAudit).order_by(UploadAudit.uploaded_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_upload_by_id(self, upload_id: UUID) -> UploadAudit | None:
        stmt = select(UploadAudit).where(UploadAudit.upload_id == upload_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_upload_stats_raw(self) -> dict:
        duration_seconds = func.extract(
            "epoch",
            UploadAudit.processed_at - UploadAudit.uploaded_at,
        )
        stmt = select(
            func.count(UploadAudit.upload_id).label("total_uploads"),
            func.sum(case((UploadAudit.status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((UploadAudit.status == "processing", 1), else_=0)).label("processing"),
            func.sum(case((UploadAudit.status == "completed", 1), else_=0)).label("completed"),
            func.sum(case((UploadAudit.status == "failed", 1), else_=0)).label("failed"),
            func.avg(UploadAudit.rows_extracted).label("avg_rows_extracted"),
            func.avg(
                case(
                    (
                        (UploadAudit.processed_at.is_not(None))
                        & (UploadAudit.uploaded_at.is_not(None)),
                        duration_seconds,
                    ),
                    else_=None,
                )
            ).label("avg_processing_seconds"),
            func.max(UploadAudit.uploaded_at).label("latest_upload_at"),
        )
        row = self.db.execute(stmt).one()
        return dict(row._mapping)
