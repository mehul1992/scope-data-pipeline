from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

from app.services.upload_service import UploadService


def _dt() -> datetime:
    return datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_list_uploads_empty() -> None:
    repo = MagicMock()
    repo.list_uploads.return_value = []
    svc = UploadService(repo)
    out = svc.list_uploads()
    assert out.count == 0


def test_get_upload_details_none() -> None:
    repo = MagicMock()
    repo.get_upload_by_id.return_value = None
    svc = UploadService(repo)
    assert svc.get_upload_details(UUID("33333333-3333-3333-3333-333333333333")) is None


def test_get_upload_file_info() -> None:
    uid = UUID("33333333-3333-3333-3333-333333333333")
    upload = SimpleNamespace(
        upload_id=uid,
        filename="a.xlsm",
        file_path="/data/a.xlsm",
    )
    repo = MagicMock()
    repo.get_upload_by_id.return_value = upload
    svc = UploadService(repo)
    info = svc.get_upload_file_info(uid)
    assert info is not None
    assert info.filename == "a.xlsm"


def test_get_upload_stats_zero_total() -> None:
    repo = MagicMock()
    repo.get_upload_stats_raw.return_value = {
        "total_uploads": 0,
        "pending": None,
        "processing": None,
        "completed": None,
        "failed": None,
        "avg_rows_extracted": None,
        "avg_processing_seconds": None,
        "latest_upload_at": None,
    }
    svc = UploadService(repo)
    out = svc.get_upload_stats()
    assert out.total_uploads == 0
    assert out.success_rate == 0.0
