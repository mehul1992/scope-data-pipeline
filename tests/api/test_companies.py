from datetime import date
from unittest.mock import MagicMock
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.schemas.company import (
    CompanyCompareResponse,
    CompanyDetailResponse,
    CompanyHistoryResponse,
    CompanyHistorySeries,
    CompanyListResponse,
    CompanyVersionsResponse,
)


def test_list_companies(
    client: TestClient, mock_company_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    mock_company_service.list_companies.return_value = CompanyListResponse(
        items=[],
        count=0,
        limit=50,
        offset=0,
    )
    response = client.get("/companies")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    mock_company_service.list_companies.assert_called_once()


def test_get_company_404(client: TestClient, mock_company_service: MagicMock) -> None:
    mock_company_service.get_company.return_value = None
    cid = "11111111-1111-1111-1111-111111111111"
    response = client.get(f"/companies/{cid}")
    assert response.status_code == 404


def test_get_company_200(
    client: TestClient, mock_company_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    mock_company_service.get_company.return_value = CompanyDetailResponse(
        company_id=sample_uuids["company"],
        entity_name="Acme",
        created_at=None,
        current_version=None,
    )
    response = client.get(f"/companies/{sample_uuids['company']}")
    assert response.status_code == 200
    assert response.json()["entity_name"] == "Acme"


def test_get_company_versions_404(client: TestClient, mock_company_service: MagicMock) -> None:
    mock_company_service.get_company_versions.return_value = None
    cid = "11111111-1111-1111-1111-111111111111"
    response = client.get(f"/companies/{cid}/versions")
    assert response.status_code == 404


def test_get_company_versions_200(
    client: TestClient, mock_company_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    mock_company_service.get_company_versions.return_value = CompanyVersionsResponse(
        company_id=sample_uuids["company"],
        entity_name="Acme",
        items=[],
        count=0,
    )
    response = client.get(f"/companies/{sample_uuids['company']}/versions")
    assert response.status_code == 200


def test_get_company_history_404(client: TestClient, mock_company_service: MagicMock) -> None:
    mock_company_service.get_company_history.return_value = None
    cid = "11111111-1111-1111-1111-111111111111"
    response = client.get(f"/companies/{cid}/history")
    assert response.status_code == 404


def test_get_company_history_200(
    client: TestClient, mock_company_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    mock_company_service.get_company_history.return_value = CompanyHistoryResponse(
        company_id=sample_uuids["company"],
        entity_name="Acme",
        series=CompanyHistorySeries(years=[], metrics={}, sentinels={}),
        snapshots=[],
        count=0,
    )
    response = client.get(f"/companies/{sample_uuids['company']}/history")
    assert response.status_code == 200


def test_compare_companies(
    client: TestClient, mock_company_service: MagicMock, sample_uuids: dict[str, UUID]
) -> None:
    mock_company_service.compare_companies.return_value = CompanyCompareResponse(
        as_of_date=date(2025, 1, 15),
        requested_company_ids=[sample_uuids["company"]],
        items=[],
        count=0,
        not_found_company_ids=[sample_uuids["company"]],
    )
    response = client.get(
        "/companies/compare",
        params={
            "company_ids": [str(sample_uuids["company"])],
            "as_of_date": "2025-01-15",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["as_of_date"] == "2025-01-15"
