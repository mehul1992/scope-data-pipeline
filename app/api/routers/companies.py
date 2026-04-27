from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CompanyServiceDep
from app.api.schemas.company import (
    CompanyCompareResponse,
    CompanyDetailResponse,
    CompanyHistoryResponse,
    CompanyListResponse,
    CompanyVersionsResponse,
)

router = APIRouter()


@router.get("", summary="List companies")
async def list_companies(
    service: CompanyServiceDep,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> CompanyListResponse:
    return service.list_companies(limit=limit, offset=offset)


@router.get("/compare", summary="Compare companies as-of a date")
async def compare_companies(
    service: CompanyServiceDep,
    company_ids: list[UUID] = Query(...),
    as_of_date: date = Query(...),
) -> CompanyCompareResponse:
    return service.compare_companies(company_ids, as_of_date)


@router.get("/{company_id}", summary="Get latest company details")
async def get_company(
    company_id: UUID,
    service: CompanyServiceDep,
) -> CompanyDetailResponse:
    detail = service.get_company(company_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return detail


@router.get("/{company_id}/versions", summary="Get company versions")
async def get_company_versions(
    company_id: UUID,
    service: CompanyServiceDep,
) -> CompanyVersionsResponse:
    versions = service.get_company_versions(company_id)
    if versions is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return versions


@router.get("/{company_id}/history", summary="Get company time-series history")
async def get_company_history(
    company_id: UUID,
    service: CompanyServiceDep,
) -> CompanyHistoryResponse:
    history = service.get_company_history(company_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return history
