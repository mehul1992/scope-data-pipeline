from datetime import date
from uuid import UUID

from app.api.schemas.snapshot import (
    SnapshotDetailResponse,
    SnapshotFilterEcho,
    SnapshotLatestListResponse,
    SnapshotListItem,
    SnapshotListResponse,
)
from app.repositories.snapshot_repository import SnapshotRepository


class SnapshotService:
    def __init__(self, snapshot_repository: SnapshotRepository) -> None:
        self.snapshot_repository = snapshot_repository

    def list_snapshots(
        self,
        company_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        sector: str | None = None,
        country: str | None = None,
        currency: str | None = None,
    ) -> SnapshotListResponse:
        snapshots = self.snapshot_repository.list_snapshots(
            company_id=company_id,
            from_date=from_date,
            to_date=to_date,
            sector=sector,
            country=country,
            currency=currency,
        )
        items = [
            SnapshotListItem(
                snapshot_id=snapshot.snapshot_id,
                company_id=snapshot.company_id,
                version_id=snapshot.version_id,
                upload_id=snapshot.upload_id,
                entity_name=snapshot.entity_name,
                corporate_sector=snapshot.corporate_sector,
                country_name=snapshot.country_name,
                currency_code=snapshot.currency_code,
                snapshot_at=snapshot.snapshot_at,
                business_risk_profile=snapshot.business_risk_profile,
                financial_risk_profile=snapshot.financial_risk_profile,
            )
            for snapshot in snapshots
        ]
        return SnapshotListResponse(
            items=items,
            count=len(items),
            filters=SnapshotFilterEcho(
                company_id=company_id,
                from_date=from_date,
                to_date=to_date,
                sector=sector,
                country=country,
                currency=currency,
            ),
        )

    def list_latest_snapshots_per_company(self) -> SnapshotLatestListResponse:
        snapshots = self.snapshot_repository.list_latest_snapshot_per_company()
        items = [
            SnapshotListItem(
                snapshot_id=s.snapshot_id,
                company_id=s.company_id,
                version_id=s.version_id,
                upload_id=s.upload_id,
                entity_name=s.entity_name,
                corporate_sector=s.corporate_sector,
                country_name=s.country_name,
                currency_code=s.currency_code,
                snapshot_at=s.snapshot_at,
                business_risk_profile=s.business_risk_profile,
                financial_risk_profile=s.financial_risk_profile,
            )
            for s in snapshots
        ]
        return SnapshotLatestListResponse(items=items, count=len(items))

    def get_snapshot(self, snapshot_id: UUID) -> SnapshotDetailResponse | None:
        snapshot = self.snapshot_repository.get_snapshot_by_id(snapshot_id)
        if snapshot is None:
            return None
        return SnapshotDetailResponse(
            snapshot_id=snapshot.snapshot_id,
            company_id=snapshot.company_id,
            version_id=snapshot.version_id,
            upload_id=snapshot.upload_id,
            entity_name=snapshot.entity_name,
            corporate_sector=snapshot.corporate_sector,
            country_name=snapshot.country_name,
            currency_code=snapshot.currency_code,
            accounting_principles=snapshot.accounting_principles,
            business_year_end=snapshot.business_year_end,
            rating_methodologies=snapshot.rating_methodologies,
            industry_risk_name=snapshot.industry_risk_name,
            industry_risk_score=snapshot.industry_risk_score,
            industry_weight=snapshot.industry_weight,
            segmentation_criteria=snapshot.segmentation_criteria,
            business_risk_profile=snapshot.business_risk_profile,
            financial_risk_profile=snapshot.financial_risk_profile,
            risk_sub_scores=snapshot.risk_sub_scores or {},
            credit_metrics=snapshot.credit_metrics or {},
            raw_data=snapshot.raw_data or {},
            snapshot_at=snapshot.snapshot_at,
        )
