from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.schemas.upload import (
    UploadDetailResponse,
    UploadFileInfo,
    UploadListResponse,
    UploadStatsResponse,
    UploadStatusCounts,
)


def test_list_uploads(client: TestClient, mock_upload_service: MagicMock) -> None:
    mock_upload_service.list_uploads.return_value = UploadListResponse(items=[], count=0)
    response = client.get("/uploads")
    assert response.status_code == 200


def test_upload_stats(client: TestClient, mock_upload_service: MagicMock) -> None:
    mock_upload_service.get_upload_stats.return_value = UploadStatsResponse(
        total_uploads=0,
        status_counts=UploadStatusCounts(
            pending=0, processing=0, completed=0, failed=0
        ),
        completed_uploads=0,
        failed_uploads=0,
        success_rate=0.0,
        avg_rows_extracted=0.0,
        avg_processing_seconds=0.0,
        latest_upload_at=None,
    )
    response = client.get("/uploads/stats")
    assert response.status_code == 200
    assert response.json()["total_uploads"] == 0


def test_upload_details_404(client: TestClient, mock_upload_service: MagicMock) -> None:
    mock_upload_service.get_upload_details.return_value = None
    uid = "33333333-3333-3333-3333-333333333333"
    response = client.get(f"/uploads/{uid}/details")
    assert response.status_code == 404


def test_upload_details_200(
    client: TestClient, mock_upload_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    now = datetime.now(timezone.utc)
    mock_upload_service.get_upload_details.return_value = UploadDetailResponse(
        upload_id=sample_uuids["upload"],
        filename="f.xlsm",
        file_sha256="abc",
        file_path="/tmp/f.xlsm",
        uploaded_at=now,
        processed_at=None,
        status="pending",
        rows_extracted=None,
        error_message=None,
    )
    response = client.get(f"/uploads/{sample_uuids['upload']}/details")
    assert response.status_code == 200
    assert response.json()["filename"] == "f.xlsm"


def test_upload_file_404_when_no_upload(
    client: TestClient, mock_upload_service: MagicMock
) -> None:
    mock_upload_service.get_upload_file_info.return_value = None
    uid = "33333333-3333-3333-3333-333333333333"
    response = client.get(f"/uploads/{uid}/file")
    assert response.status_code == 404


def test_upload_file_404_when_missing_path(
    client: TestClient, mock_upload_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    mock_upload_service.get_upload_file_info.return_value = UploadFileInfo(
        upload_id=sample_uuids["upload"],
        filename="missing.xlsm",
        file_path="/nonexistent/path/missing.xlsm",
    )
    response = client.get(f"/uploads/{sample_uuids['upload']}/file")
    assert response.status_code == 404


def test_upload_file_200(
    client: TestClient,
    mock_upload_service: MagicMock,
    sample_uuids: dict[str, UUID],
    tmp_path: Path,
) -> None:
    f = tmp_path / "source.xlsm"
    f.write_bytes(b"xlsm-bytes")
    mock_upload_service.get_upload_file_info.return_value = UploadFileInfo(
        upload_id=sample_uuids["upload"],
        filename="source.xlsm",
        file_path=str(f),
    )
    response = client.get(f"/uploads/{sample_uuids['upload']}/file")
    assert response.status_code == 200
    assert response.content == b"xlsm-bytes"
