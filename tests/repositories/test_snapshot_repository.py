from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

from app.repositories.snapshot_repository import SnapshotRepository

from tests.conftest import execute_result_scalar_one, execute_result_scalars_all


def test_list_snapshots_returns_rows() -> None:
    snap = SimpleNamespace(
        snapshot_id=UUID("22222222-2222-2222-2222-222222222222"),
        company_id=UUID("11111111-1111-1111-1111-111111111111"),
        entity_name="Acme",
    )
    session = MagicMock()
    session.execute.return_value = execute_result_scalars_all([snap])
    repo = SnapshotRepository(session)
    out = repo.list_snapshots()
    assert len(out) == 1
    assert out[0].entity_name == "Acme"


def test_get_snapshot_by_id() -> None:
    snap = SimpleNamespace(snapshot_id=UUID("22222222-2222-2222-2222-222222222222"))
    session = MagicMock()
    session.execute.return_value = execute_result_scalar_one(snap)
    repo = SnapshotRepository(session)
    out = repo.get_snapshot_by_id(UUID("22222222-2222-2222-2222-222222222222"))
    assert out is snap


def test_list_latest_snapshot_per_company() -> None:
    snap = SimpleNamespace(entity_name="Beta")
    session = MagicMock()
    session.execute.return_value = execute_result_scalars_all([snap])
    repo = SnapshotRepository(session)
    out = repo.list_latest_snapshot_per_company()
    assert out == [snap]
