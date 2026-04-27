from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

from app.services.snapshot_service import SnapshotService


def _snap(**kwargs: object) -> SimpleNamespace:
    defaults = dict(
        snapshot_id=UUID("22222222-2222-2222-2222-222222222222"),
        company_id=UUID("11111111-1111-1111-1111-111111111111"),
        version_id=UUID("44444444-4444-4444-4444-444444444444"),
        upload_id=UUID("33333333-3333-3333-3333-333333333333"),
        entity_name="Acme",
        corporate_sector=None,
        country_name=None,
        currency_code=None,
        snapshot_at=datetime.now(timezone.utc),
        business_risk_profile=None,
        financial_risk_profile=None,
        accounting_principles=None,
        business_year_end=None,
        rating_methodologies=None,
        industry_risk_name=None,
        industry_risk_score=None,
        industry_weight=None,
        segmentation_criteria=None,
        risk_sub_scores=None,
        credit_metrics=None,
        raw_data=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_list_snapshots_empty() -> None:
    repo = MagicMock()
    repo.list_snapshots.return_value = []
    svc = SnapshotService(repo)
    out = svc.list_snapshots(company_id=UUID("11111111-1111-1111-1111-111111111111"))
    assert out.count == 0
    assert out.filters.company_id == UUID("11111111-1111-1111-1111-111111111111")


def test_list_latest() -> None:
    repo = MagicMock()
    repo.list_latest_snapshot_per_company.return_value = [_snap()]
    svc = SnapshotService(repo)
    out = svc.list_latest_snapshots_per_company()
    assert out.count == 1
    assert out.items[0].entity_name == "Acme"


def test_get_snapshot_none() -> None:
    repo = MagicMock()
    repo.get_snapshot_by_id.return_value = None
    svc = SnapshotService(repo)
    assert svc.get_snapshot(UUID("22222222-2222-2222-2222-222222222222")) is None


def test_get_snapshot_detail() -> None:
    sid = UUID("22222222-2222-2222-2222-222222222222")
    repo = MagicMock()
    repo.get_snapshot_by_id.return_value = _snap(snapshot_id=sid, credit_metrics={"years": []})
    svc = SnapshotService(repo)
    out = svc.get_snapshot(sid)
    assert out is not None
    assert out.snapshot_id == sid
    assert out.credit_metrics == {"years": []}
