from unittest.mock import MagicMock
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.schemas.snapshot import (
    SnapshotDetailResponse,
    SnapshotFilterEcho,
    SnapshotLatestListResponse,
    SnapshotListResponse,
)


def test_list_snapshots(
    client: TestClient, mock_snapshot_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    mock_snapshot_service.list_snapshots.return_value = SnapshotListResponse(
        items=[],
        count=0,
        filters=SnapshotFilterEcho(company_id=sample_uuids["company"]),
    )
    response = client.get(
        "/snapshots",
        params={"company_id": str(sample_uuids["company"])},
    )
    assert response.status_code == 200
    mock_snapshot_service.list_snapshots.assert_called_once()


def test_list_snapshots_invalid_date_range(client: TestClient) -> None:
    response = client.get(
        "/snapshots",
        params={"from_date": "2025-02-01", "to_date": "2025-01-01"},
    )
    assert response.status_code == 422


def test_get_latest_snapshots(client: TestClient, mock_snapshot_service: MagicMock) -> None:
    mock_snapshot_service.list_latest_snapshots_per_company.return_value = (
        SnapshotLatestListResponse(items=[], count=0)
    )
    response = client.get("/snapshots/latest")
    assert response.status_code == 200
    assert response.json() == {"items": [], "count": 0}


def test_get_snapshot_404(client: TestClient, mock_snapshot_service: MagicMock) -> None:
    mock_snapshot_service.get_snapshot.return_value = None
    sid = "22222222-2222-2222-2222-222222222222"
    response = client.get(f"/snapshots/{sid}")
    assert response.status_code == 404


def test_get_snapshot_200(
    client: TestClient, mock_snapshot_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    from datetime import datetime, timezone

    mock_snapshot_service.get_snapshot.return_value = SnapshotDetailResponse(
        snapshot_id=sample_uuids["snapshot"],
        company_id=sample_uuids["company"],
        version_id=sample_uuids["version"],
        upload_id=sample_uuids["upload"],
        entity_name="Acme",
        risk_sub_scores={},
        credit_metrics={},
        raw_data={},
        snapshot_at=datetime.now(timezone.utc),
    )
    response = client.get(f"/snapshots/{sample_uuids['snapshot']}")
    assert response.status_code == 200
    assert response.json()["entity_name"] == "Acme"
