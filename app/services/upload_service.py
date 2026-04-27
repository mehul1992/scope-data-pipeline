from uuid import UUID

from app.api.schemas.upload import (
    UploadDetailResponse,
    UploadFileInfo,
    UploadListItem,
    UploadListResponse,
    UploadStatsResponse,
    UploadStatusCounts,
)
from app.repositories.upload_repository import UploadRepository


class UploadService:
    def __init__(self, upload_repository: UploadRepository) -> None:
        self.upload_repository = upload_repository

    def list_uploads(self) -> UploadListResponse:
        uploads = self.upload_repository.list_uploads()
        items = [
            UploadListItem(
                upload_id=upload.upload_id,
                filename=upload.filename,
                file_sha256=upload.file_sha256,
                file_path=upload.file_path,
                uploaded_at=upload.uploaded_at,
                processed_at=upload.processed_at,
                status=upload.status,
                rows_extracted=upload.rows_extracted,
                error_message=upload.error_message,
            )
            for upload in uploads
        ]
        return UploadListResponse(items=items, count=len(items))

    def get_upload_details(self, upload_id: UUID) -> UploadDetailResponse | None:
        upload = self.upload_repository.get_upload_by_id(upload_id)
        if upload is None:
            return None
        return UploadDetailResponse(
            upload_id=upload.upload_id,
            filename=upload.filename,
            file_sha256=upload.file_sha256,
            file_path=upload.file_path,
            uploaded_at=upload.uploaded_at,
            processed_at=upload.processed_at,
            status=upload.status,
            rows_extracted=upload.rows_extracted,
            error_message=upload.error_message,
        )

    def get_upload_file_info(self, upload_id: UUID) -> UploadFileInfo | None:
        upload = self.upload_repository.get_upload_by_id(upload_id)
        if upload is None:
            return None
        return UploadFileInfo(
            upload_id=upload.upload_id,
            filename=upload.filename,
            file_path=upload.file_path,
        )

    def get_upload_stats(self) -> UploadStatsResponse:
        stats = self.upload_repository.get_upload_stats_raw()
        total = int(stats.get("total_uploads") or 0)
        pending = int(stats.get("pending") or 0)
        processing = int(stats.get("processing") or 0)
        completed = int(stats.get("completed") or 0)
        failed = int(stats.get("failed") or 0)
        success_rate = (completed / total) if total > 0 else 0.0
        avg_rows_extracted = float(stats.get("avg_rows_extracted") or 0.0)
        avg_processing_seconds = float(stats.get("avg_processing_seconds") or 0.0)

        return UploadStatsResponse(
            total_uploads=total,
            status_counts=UploadStatusCounts(
                pending=pending,
                processing=processing,
                completed=completed,
                failed=failed,
            ),
            completed_uploads=completed,
            failed_uploads=failed,
            success_rate=success_rate,
            avg_rows_extracted=avg_rows_extracted,
            avg_processing_seconds=avg_processing_seconds,
            latest_upload_at=stats.get("latest_upload_at"),
        )
