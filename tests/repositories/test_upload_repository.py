from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

from app.repositories.upload_repository import UploadRepository

from tests.conftest import execute_result_one_mapping, execute_result_scalar_one, execute_result_scalars_all


def test_list_uploads() -> None:
    u = SimpleNamespace(upload_id=UUID("33333333-3333-3333-3333-333333333333"))
    session = MagicMock()
    session.execute.return_value = execute_result_scalars_all([u])
    repo = UploadRepository(session)
    out = repo.list_uploads()
    assert len(out) == 1


def test_get_upload_by_id() -> None:
    u = SimpleNamespace(upload_id=UUID("33333333-3333-3333-3333-333333333333"))
    session = MagicMock()
    session.execute.return_value = execute_result_scalar_one(u)
    repo = UploadRepository(session)
    out = repo.get_upload_by_id(UUID("33333333-3333-3333-3333-333333333333"))
    assert out is u


def test_get_upload_stats_raw() -> None:
    session = MagicMock()
    session.execute.return_value = execute_result_one_mapping(
        {
            "total_uploads": 10,
            "pending": 1,
            "processing": 2,
            "completed": 6,
            "failed": 1,
            "avg_rows_extracted": 100.0,
            "avg_processing_seconds": 5.5,
            "latest_upload_at": None,
        }
    )
    repo = UploadRepository(session)
    stats = repo.get_upload_stats_raw()
    assert stats["total_uploads"] == 10
    assert stats["completed"] == 6
