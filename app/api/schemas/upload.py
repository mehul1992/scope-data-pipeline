from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UploadListItem(BaseModel):
    upload_id: UUID
    filename: str
    file_sha256: str
    file_path: str
    uploaded_at: datetime
    processed_at: datetime | None = None
    status: str
    rows_extracted: int | None = None
    error_message: str | None = None


class UploadListResponse(BaseModel):
    items: list[UploadListItem]
    count: int


class UploadDetailResponse(BaseModel):
    upload_id: UUID
    filename: str
    file_sha256: str
    file_path: str
    uploaded_at: datetime
    processed_at: datetime | None = None
    status: str
    rows_extracted: int | None = None
    error_message: str | None = None


class UploadFileInfo(BaseModel):
    upload_id: UUID
    filename: str
    file_path: str


class UploadStatusCounts(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int


class UploadStatsResponse(BaseModel):
    total_uploads: int
    status_counts: UploadStatusCounts
    completed_uploads: int
    failed_uploads: int
    success_rate: float
    avg_rows_extracted: float
    avg_processing_seconds: float
    latest_upload_at: datetime | None = None
