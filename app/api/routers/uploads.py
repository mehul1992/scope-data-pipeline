from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.deps import DbSession, UploadServiceDep
from app.api.schemas.upload import (
    UploadDetailResponse,
    UploadListResponse,
    UploadStatsResponse,
)

router = APIRouter()


@router.get("", summary="List uploads")
async def list_uploads(service: UploadServiceDep) -> UploadListResponse:
    return service.list_uploads()


@router.get("/stats", summary="Get upload stats")
async def get_upload_stats(service: UploadServiceDep) -> UploadStatsResponse:
    return service.get_upload_stats()


@router.get("/{upload_id}/details", summary="Get upload details")
async def get_upload_details(
    upload_id: UUID,
    service: UploadServiceDep,
) -> UploadDetailResponse:
    details = service.get_upload_details(upload_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    return details


@router.get("/{upload_id}/file", summary="Download upload source file")
async def get_upload_file(
    upload_id: UUID,
    service: UploadServiceDep,
) -> FileResponse:
    info = service.get_upload_file_info(upload_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    file_path = Path(info.file_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file_path), filename=info.filename)
