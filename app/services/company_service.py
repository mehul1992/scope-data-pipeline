from datetime import date
from uuid import UUID

from app.api.schemas.company import (
    CompanyCompareItem,
    CompanyCompareResponse,
    CompanyCurrentVersion,
    CompanyDetailResponse,
    CompanyHistoryResponse,
    CompanyHistorySeries,
    CompanyHistorySnapshotItem,
    CompanyListItem,
    CompanyListResponse,
    CompanyVersionItem,
    CompanyVersionsResponse,
)
from app.repositories.company_repository import CompanyRepository


class CompanyService:
    def __init__(self, company_repository: CompanyRepository) -> None:
        self.company_repository = company_repository

    def get_company(self, company_id: UUID) -> CompanyDetailResponse | None:
        company = self.company_repository.get_company_by_id(company_id)
        if company is None:
            return None
        cv = self.company_repository.get_current_version_for_company(company_id)
        current = None
        if cv is not None:
            current = CompanyCurrentVersion(
                version_id=cv.version_id,
                upload_id=cv.upload_id,
                version_number=cv.version_number,
                valid_from=cv.valid_from,
                valid_to=cv.valid_to,
                is_current=cv.is_current,
                created_at=cv.created_at,
            )
        return CompanyDetailResponse(
            company_id=company.company_id,
            entity_name=company.entity_name,
            created_at=getattr(company, "created_at", None),
            current_version=current,
        )

    def get_company_versions(
        self, company_id: UUID
    ) -> CompanyVersionsResponse | None:
        company = self.company_repository.get_company_by_id(company_id)
        if company is None:
            return None
        versions = self.company_repository.list_versions_for_company(company_id)
        items = [
            CompanyVersionItem(
                version_id=version.version_id,
                upload_id=version.upload_id,
                version_number=version.version_number,
                valid_from=version.valid_from,
                valid_to=version.valid_to,
                is_current=version.is_current,
                created_at=version.created_at,
            )
            for version in versions
        ]
        return CompanyVersionsResponse(
            company_id=company.company_id,
            entity_name=company.entity_name,
            items=items,
            count=len(items),
        )

    def get_company_history(self, company_id: UUID) -> CompanyHistoryResponse | None:
        company = self.company_repository.get_company_by_id(company_id)
        if company is None:
            return None
        versions = self.company_repository.list_versions_for_company(company_id)
        version_numbers = {
            version.version_id: version.version_number
            for version in versions
        }
        snapshots = self.company_repository.list_snapshots_for_company(company_id)
        snapshot_items = [
            CompanyHistorySnapshotItem(
                snapshot_id=snapshot.snapshot_id,
                version_id=snapshot.version_id,
                version_number=version_numbers.get(snapshot.version_id, 0),
                upload_id=snapshot.upload_id,
                snapshot_at=snapshot.snapshot_at,
                credit_metrics=snapshot.credit_metrics or {},
            )
            for snapshot in snapshots
        ]
        series_data = snapshots[-1].credit_metrics if snapshots else {}
        series = CompanyHistorySeries(
            years=series_data.get("years", []),
            metrics=series_data.get("metrics", {}),
            sentinels=series_data.get("sentinels", {}),
        )
        return CompanyHistoryResponse(
            company_id=company.company_id,
            entity_name=company.entity_name,
            series=series,
            snapshots=snapshot_items,
            count=len(snapshot_items),
        )

    def compare_companies(
        self, company_ids: list[UUID], as_of_date: date
    ) -> CompanyCompareResponse:
        rows = self.company_repository.list_comparison_snapshots(company_ids, as_of_date)
        latest_by_company: dict[UUID, CompanyCompareItem] = {}
        for company, version, snapshot in rows:
            if company.company_id in latest_by_company:
                continue
            latest_by_company[company.company_id] = CompanyCompareItem(
                company_id=company.company_id,
                entity_name=company.entity_name,
                version_id=version.version_id,
                version_number=version.version_number,
                snapshot_id=snapshot.snapshot_id,
                snapshot_at=snapshot.snapshot_at,
                corporate_sector=snapshot.corporate_sector,
                country_name=snapshot.country_name,
                currency_code=snapshot.currency_code,
                business_risk_profile=snapshot.business_risk_profile,
                financial_risk_profile=snapshot.financial_risk_profile,
                credit_metrics=snapshot.credit_metrics or {},
            )

        items = [latest_by_company[cid] for cid in company_ids if cid in latest_by_company]
        not_found_company_ids = [cid for cid in company_ids if cid not in latest_by_company]

        return CompanyCompareResponse(
            as_of_date=as_of_date,
            requested_company_ids=company_ids,
            items=items,
            count=len(items),
            not_found_company_ids=not_found_company_ids,
        )

    def list_companies(self, limit: int = 50, offset: int = 0) -> CompanyListResponse:
        companies = self.company_repository.list_companies(limit=limit, offset=offset)
        items = [
            CompanyListItem(
                company_id=company.company_id,
                entity_name=company.entity_name,
                # current_snapshot_id=company.current_snapshot_id,
                created_at=getattr(company, "created_at", None),
            )
            for company in companies
        ]
        return CompanyListResponse(
            items=items,
            count=len(items),
            limit=limit,
            offset=offset,
        )
