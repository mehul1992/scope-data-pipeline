from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

from app.repositories.company_repository import CompanyRepository

from tests.conftest import execute_result_all, execute_result_scalar_one, execute_result_scalars_all


def test_list_companies() -> None:
    company = SimpleNamespace(
        company_id=UUID("11111111-1111-1111-1111-111111111111"),
        entity_name="Acme",
    )
    session = MagicMock()
    session.execute.return_value = execute_result_scalars_all([company])
    repo = CompanyRepository(session)
    out = repo.list_companies(limit=2, offset=1)
    assert len(out) == 1
    assert out[0].entity_name == "Acme"
    session.execute.assert_called_once()


def test_get_company_by_id() -> None:
    company = SimpleNamespace(company_id=UUID("11111111-1111-1111-1111-111111111111"))
    session = MagicMock()
    session.execute.return_value = execute_result_scalar_one(company)
    repo = CompanyRepository(session)
    out = repo.get_company_by_id(UUID("11111111-1111-1111-1111-111111111111"))
    assert out is company


def test_list_comparison_snapshots() -> None:
    row = (
        SimpleNamespace(company_id=UUID("11111111-1111-1111-1111-111111111111")),
        SimpleNamespace(version_id=UUID("44444444-4444-4444-4444-444444444444")),
        SimpleNamespace(snapshot_id=UUID("22222222-2222-2222-2222-222222222222")),
    )
    session = MagicMock()
    session.execute.return_value = execute_result_all([row])
    repo = CompanyRepository(session)
    from datetime import date

    out = repo.list_comparison_snapshots([UUID("11111111-1111-1111-1111-111111111111")], date(2025, 1, 1))
    assert len(out) == 1
    assert out[0][0].company_id == UUID("11111111-1111-1111-1111-111111111111")
