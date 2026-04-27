from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

from app.services.company_service import CompanyService


def _dt() -> datetime:
    return datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_get_company_none() -> None:
    repo = MagicMock()
    repo.get_company_by_id.return_value = None
    svc = CompanyService(repo)
    assert svc.get_company(UUID("11111111-1111-1111-1111-111111111111")) is None


def test_get_company_with_version() -> None:
    cid = UUID("11111111-1111-1111-1111-111111111111")
    company = SimpleNamespace(
        company_id=cid,
        entity_name="Acme",
        created_at=_dt(),
    )
    cv = SimpleNamespace(
        version_id=UUID("44444444-4444-4444-4444-444444444444"),
        upload_id=UUID("33333333-3333-3333-3333-333333333333"),
        version_number=1,
        valid_from=_dt(),
        valid_to=None,
        is_current=True,
        created_at=_dt(),
    )
    repo = MagicMock()
    repo.get_company_by_id.return_value = company
    repo.get_current_version_for_company.return_value = cv
    svc = CompanyService(repo)
    out = svc.get_company(cid)
    assert out is not None
    assert out.entity_name == "Acme"
    assert out.current_version is not None
    assert out.current_version.version_number == 1


def test_list_companies() -> None:
    cid = UUID("11111111-1111-1111-1111-111111111111")
    company = SimpleNamespace(company_id=cid, entity_name="Acme", created_at=_dt())
    repo = MagicMock()
    repo.list_companies.return_value = [company]
    svc = CompanyService(repo)
    out = svc.list_companies(limit=10, offset=5)
    assert out.count == 1
    assert out.limit == 10
    assert out.offset == 5
    repo.list_companies.assert_called_once_with(limit=10, offset=5)


def test_compare_companies_orders_not_found() -> None:
    cid = UUID("11111111-1111-1111-1111-111111111111")
    repo = MagicMock()
    repo.list_comparison_snapshots.return_value = []
    svc = CompanyService(repo)
    out = svc.compare_companies([cid], date(2025, 6, 1))
    assert out.count == 0
    assert out.not_found_company_ids == [cid]
