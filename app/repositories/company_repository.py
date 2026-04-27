from datetime import date, datetime, time, timezone
from uuid import UUID

from sqlalchemy import or_, select

from app.models.company_dim import CompanyVersion, DimCompany
from app.models.snapshot_fact import SnapshotFact
from app.repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository):
    def list_companies(self, limit: int = 50, offset: int = 0) -> list[DimCompany]:
        stmt = (
            select(DimCompany)
            .order_by(DimCompany.entity_name.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_company_by_id(self, company_id: UUID) -> DimCompany | None:
        stmt = select(DimCompany).where(DimCompany.company_id == company_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_current_version_for_company(
        self, company_id: UUID
    ) -> CompanyVersion | None:
        stmt = (
            select(CompanyVersion)
            .where(
                CompanyVersion.company_id == company_id,
                CompanyVersion.is_current.is_(True),
            )
            .order_by(CompanyVersion.version_number.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_versions_for_company(self, company_id: UUID) -> list[CompanyVersion]:
        stmt = (
            select(CompanyVersion)
            .where(CompanyVersion.company_id == company_id)
            .order_by(CompanyVersion.version_number.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_snapshots_for_company(self, company_id: UUID) -> list[SnapshotFact]:
        stmt = (
            select(SnapshotFact)
            .where(SnapshotFact.company_id == company_id)
            .order_by(SnapshotFact.snapshot_at.asc(), SnapshotFact.version_id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_comparison_snapshots(
        self, company_ids: list[UUID], as_of_date: date
    ) -> list[tuple[DimCompany, CompanyVersion, SnapshotFact]]:
        as_of_dt = datetime.combine(as_of_date, time.max, tzinfo=timezone.utc)
        stmt = (
            select(DimCompany, CompanyVersion, SnapshotFact)
            .join(CompanyVersion, CompanyVersion.company_id == DimCompany.company_id)
            .join(SnapshotFact, SnapshotFact.version_id == CompanyVersion.version_id)
            .where(
                DimCompany.company_id.in_(company_ids),
                CompanyVersion.valid_from <= as_of_dt,
                or_(
                    CompanyVersion.valid_to.is_(None),
                    CompanyVersion.valid_to > as_of_dt,
                ),
            )
            .order_by(
                DimCompany.company_id.asc(),
                CompanyVersion.version_number.desc(),
                SnapshotFact.snapshot_at.desc(),
            )
        )
        return list(self.db.execute(stmt).all())
