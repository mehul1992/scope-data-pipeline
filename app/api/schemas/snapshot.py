from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class SnapshotListItem(BaseModel):
    snapshot_id: UUID
    company_id: UUID
    version_id: UUID
    upload_id: UUID
    entity_name: str
    corporate_sector: str | None = None
    country_name: str | None = None
    currency_code: str | None = None
    snapshot_at: datetime
    business_risk_profile: str | None = None
    financial_risk_profile: str | None = None


class SnapshotFilterEcho(BaseModel):
    company_id: UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    sector: str | None = None
    country: str | None = None
    currency: str | None = None


class SnapshotListResponse(BaseModel):
    items: list[SnapshotListItem]
    count: int
    filters: SnapshotFilterEcho


class SnapshotLatestListResponse(BaseModel):
    items: list[SnapshotListItem]
    count: int


class SnapshotDetailResponse(BaseModel):
    snapshot_id: UUID
    company_id: UUID
    version_id: UUID
    upload_id: UUID
    entity_name: str
    corporate_sector: str | None = None
    country_name: str | None = None
    currency_code: str | None = None
    accounting_principles: str | None = None
    business_year_end: str | None = None
    rating_methodologies: list[str] | None = None
    industry_risk_name: str | None = None
    industry_risk_score: str | None = None
    industry_weight: float | None = None
    segmentation_criteria: str | None = None
    business_risk_profile: str | None = None
    financial_risk_profile: str | None = None
    risk_sub_scores: dict
    credit_metrics: dict
    raw_data: dict
    snapshot_at: datetime
