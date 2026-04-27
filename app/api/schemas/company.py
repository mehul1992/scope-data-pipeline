from datetime import date, datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel


class CompanyListItem(BaseModel):
    company_id: UUID
    entity_name: str
    current_snapshot_id: UUID | None = None
    created_at: datetime | None = None


class CompanyListResponse(BaseModel):
    items: list[CompanyListItem]
    count: int
    limit: int
    offset: int


class CompanyCurrentVersion(BaseModel):
    version_id: UUID
    upload_id: UUID
    version_number: int
    valid_from: datetime
    valid_to: datetime | None
    is_current: bool
    created_at: datetime


class CompanyDetailResponse(BaseModel):
    company_id: UUID
    entity_name: str
    created_at: datetime | None = None
    current_version: CompanyCurrentVersion | None = None


class CompanyVersionItem(BaseModel):
    version_id: UUID
    upload_id: UUID
    version_number: int
    valid_from: datetime
    valid_to: datetime | None
    is_current: bool
    created_at: datetime


class CompanyVersionsResponse(BaseModel):
    company_id: UUID
    entity_name: str
    items: list[CompanyVersionItem]
    count: int


class CompanyHistorySnapshotItem(BaseModel):
    snapshot_id: UUID
    version_id: UUID
    version_number: int
    upload_id: UUID
    snapshot_at: datetime
    credit_metrics: dict


class CompanyHistorySeries(BaseModel):
    years: list[str]
    metrics: dict
    sentinels: dict


class CompanyHistoryResponse(BaseModel):
    company_id: UUID
    entity_name: str
    series: CompanyHistorySeries
    snapshots: list[CompanyHistorySnapshotItem]
    count: int


class CompanyCompareItem(BaseModel):
    company_id: UUID
    entity_name: str
    version_id: UUID
    version_number: int
    snapshot_id: UUID
    snapshot_at: datetime
    corporate_sector: str | None = None
    country_name: str | None = None
    currency_code: str | None = None
    business_risk_profile: str | None = None
    financial_risk_profile: str | None = None
    credit_metrics: dict[str, Any]


class CompanyCompareResponse(BaseModel):
    as_of_date: date
    requested_company_ids: list[UUID]
    items: list[CompanyCompareItem]
    count: int
    not_found_company_ids: list[UUID]
