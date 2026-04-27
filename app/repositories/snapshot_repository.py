from datetime import date, datetime, time, timezone
from uuid import UUID

from sqlalchemy import func, select

from app.models.snapshot_fact import SnapshotFact
from app.repositories.base_repository import BaseRepository


class SnapshotRepository(BaseRepository):
    def list_snapshots(
        self,
        company_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        sector: str | None = None,
        country: str | None = None,
        currency: str | None = None,
    ) -> list[SnapshotFact]:
        stmt = select(SnapshotFact)

        if company_id is not None:
            stmt = stmt.where(SnapshotFact.company_id == company_id)

        if from_date is not None:
            start_dt = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(SnapshotFact.snapshot_at >= start_dt)

        if to_date is not None:
            end_dt = datetime.combine(to_date, time.max, tzinfo=timezone.utc)
            stmt = stmt.where(SnapshotFact.snapshot_at <= end_dt)

        if sector:
            stmt = stmt.where(
                func.lower(SnapshotFact.corporate_sector) == sector.lower()
            )

        if country:
            stmt = stmt.where(
                func.lower(SnapshotFact.country_name) == country.lower()
            )

        if currency:
            stmt = stmt.where(
                func.lower(SnapshotFact.currency_code) == currency.lower()
            )

        stmt = stmt.order_by(SnapshotFact.snapshot_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def list_latest_snapshot_per_company(self) -> list[SnapshotFact]:
        rn = (
            func.row_number()
            .over(
                partition_by=SnapshotFact.company_id,
                order_by=(
                    SnapshotFact.snapshot_at.desc(),
                    SnapshotFact.snapshot_id.desc(),
                ),
            )
            .label("rn")
        )
        ranked = select(SnapshotFact.snapshot_id, rn).subquery()
        stmt = (
            select(SnapshotFact)
            .join(ranked, SnapshotFact.snapshot_id == ranked.c.snapshot_id)
            .where(ranked.c.rn == 1)
            .order_by(SnapshotFact.entity_name)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_snapshot_by_id(self, snapshot_id: UUID) -> SnapshotFact | None:
        stmt = select(SnapshotFact).where(SnapshotFact.snapshot_id == snapshot_id)
        return self.db.execute(stmt).scalar_one_or_none()
