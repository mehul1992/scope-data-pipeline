from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import SnapshotServiceDep
from app.api.schemas.snapshot import (
    SnapshotDetailResponse,
    SnapshotLatestListResponse,
    SnapshotListResponse,
)

router = APIRouter()


@router.get("", summary="List snapshots")
async def list_snapshots(
    service: SnapshotServiceDep,
    company_id: UUID | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    sector: str | None = Query(None),
    country: str | None = Query(None),
    currency: str | None = Query(None),
) -> SnapshotListResponse:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=422, detail="from_date must be <= to_date")
    return service.list_snapshots(
        company_id=company_id,
        from_date=from_date,
        to_date=to_date,
        sector=sector,
        country=country,
        currency=currency,
    )


@router.get(
    "/latest",
    summary="Get latest snapshot per company",
    response_description=(
        "One row per company that has snapshots: newest snapshot_at "
        "(ties broken by snapshot_id)."
    ),
)
async def get_latest_snapshots(
    service: SnapshotServiceDep,
) -> SnapshotLatestListResponse:
    return service.list_latest_snapshots_per_company()


@router.get("/{snapshot_id}", summary="Get snapshot details")
async def get_snapshot(
    snapshot_id: UUID,
    service: SnapshotServiceDep,
) -> SnapshotDetailResponse:
    snapshot = service.get_snapshot(snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot
