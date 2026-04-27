"""
Warehouse loader.

Loads transformed data into the PostgreSQL star schema using asyncpg.
No SQLAlchemy dependency — compatible with Airflow container.

Transformed payload structure (from transform_stage):
{
    "transformed_payload": {
        "upload_id": "uuid",
        "parsed_payload": { ... },
        "country_transformed": { ... },
        "currency_transformed": { ... },
        "dates_transformed": [ ... ],
        "company_transformed": {
            "company_payload": { "entity_name": ..., "is_new_company": bool },
            "version_payload": { ... },
            "is_new_company": bool,
            "previous_version_close": None | dict
        }
    }
}

Load order (FK dependency order):
  1. dim_country
  2. dim_currency
  3. dim_date
  4. dim_company
  5. company_versions  (close previous → insert new)
  6. snapshot_fact
  7. dim_company       (update current_snapshot_id)
  8. data_quality_report
  9. upload_audit      (mark completed — last step)
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import asyncpg

from app.core.config import settings

logger = logging.getLogger(__name__)


class WarehouseLoader:
    """
    Loads one file's transformed data into the star schema.

    Usage from Airflow @task:
        loader = WarehouseLoader()
        result = loader.load(transformed_item)
    """

    def load(self, transformed_item: dict[str, Any]) -> dict[str, Any]:
        """Sync entry point for Airflow @task compatibility."""
        return asyncio.run(self._load_async(transformed_item))

    async def _load_async(
        self, transformed_item: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Open one connection, run everything in one transaction.
        On failure: rollback → mark upload failed via separate connection.
        """
        # unwrap transformed_payload envelope
        logger.info("load starting transformed_item=%s", transformed_item)

        data = transformed_item["transformed_payload"]
        payload = data["validated_payload"]
        upload_id = data["upload_id"]
        entity_name = data["company_transformed"]["company_payload"]["entity_name"]

        logger.info(
            "load starting entity=%s upload_id=%s",
            entity_name,
            upload_id,
        )

        conn = await asyncpg.connect(self._dsn())
        try:
            async with conn.transaction():
                result = await self._execute_load(
                    conn=conn,
                    data=data,
                    payload=payload,
                    upload_id=upload_id
                )
            logger.info(
                "load completed entity=%s version=%s snapshot_id=%s",
                entity_name,
                result["version_number"],
                result["snapshot_id"],
            )
            return result

        except Exception as exc:
            logger.error(
                "load failed entity=%s error=%s",
                entity_name,
                str(exc),
            )
            await self._mark_failed(upload_id=upload_id, error=str(exc))
            raise

        finally:
            await conn.close()

    async def _execute_load(
        self,
        conn: asyncpg.Connection,
        data: dict[str, Any],
        payload: dict[str, Any],
        upload_id: str
    ) -> dict[str, Any]:
        """Execute all inserts in sequence inside one transaction."""

        company_transformed = data["company_transformed"]
        is_new_company = company_transformed["is_new_company"]
        company_id = company_transformed["company_payload"]["company_id"]
        entity_name = payload["rated_entity"]

        # ── Step 1: upsert dim_country ────────────────────────
        country_id = await self._upsert_country(
            conn,
            data.get("country_transformed"),
        )
        logger.info("country upserted country_id=%s", country_id)

        # ── Step 2: upsert dim_currency ───────────────────────
        currency_id = await self._upsert_currency(
            conn,
            data.get("currency_transformed"),
        )
        logger.info("currency upserted currency_id=%s", currency_id)

        # ── Step 3: upsert dim_date rows ──────────────────────
        await self._upsert_dates(
            conn,
            data.get("dates_transformed", []),
        )
        logger.info("dates upserted")

        # ── Step 4: upsert dim_company ────────────────────────
        # is_new_company already resolved in transformer
        # no need to query DB again
        if not company_id:
            company_id = await self._upsert_company(
                conn=conn,
                entity_name=entity_name,
                is_new_company=is_new_company
            )
            logger.info(
                "company resolved company_id=%s is_new=%s",
                company_id,
                is_new_company,
            )

        # ── Step 5: close previous version (SCD Type 2) ───────
        # transformer already determined if previous version exists
        if not is_new_company:
            await self._close_previous_version(conn, company_id)
            logger.info("previous version closed")

        # ── Step 6: get version_number from transformer ───────
        version_number = company_transformed["version_payload"]["version_number"]
        logger.info("version_number=%s", version_number)

        # ── Step 7: insert company_versions ───────────────────
        version_id = await self._insert_company_version(
            conn=conn,
            company_id=company_id,
            upload_id=upload_id,
            version_number=version_number,
        )
        logger.info("version inserted version_id=%s", version_id)

        # ── Step 8: insert snapshot_fact ──────────────────────
        snapshot_id = await self._insert_snapshot(
            conn=conn,
            payload=payload,
            company_id=company_id,
            version_id=version_id,
            upload_id=upload_id,
            country_id=country_id,
            currency_id=currency_id,
        )
        logger.info("snapshot inserted snapshot_id=%s", snapshot_id)

        # ── Step 9: update current_snapshot_id ───────────────
        await self._update_current_snapshot(conn, company_id, snapshot_id)
        logger.info("current_snapshot_id updated")

        # ── Step 10: insert data_quality_report ───────────────
        await self._insert_quality_report(
            conn=conn,
            upload_id=upload_id,
            snapshot_id=snapshot_id,
            validation_result=payload,
        )
        logger.info("quality report inserted")

        # ── Step 11: mark upload_audit completed ───────────────
        await self._mark_completed(
            conn=conn,
            upload_id=upload_id,
            rows_extracted=len(payload.get("raw_data", {}))
        )
        logger.info("upload marked completed upload_id=%s", upload_id)

        return {
            "snapshot_id": snapshot_id,
            "company_id": company_id,
            "version_id": version_id,
            "version_number": version_number,
            "is_new_company": is_new_company,
            "status": "completed",
        }

    # ── step helpers ──────────────────────────────────────────

    async def _upsert_country(
        self,
        conn: asyncpg.Connection,
        country_transformed: dict[str, Any] | None,
    ) -> str | None:
        """Insert or get DimCountry. Returns country_id."""
        if not country_transformed:
            return None

        row = await conn.fetchrow(
            """
            INSERT INTO dim_country
                (country_name, iso_alpha2, iso_alpha3, region)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (country_name)
            DO UPDATE SET
                country_name = EXCLUDED.country_name
            RETURNING country_id
            """,
            country_transformed["country_name"],
            country_transformed.get("iso_alpha2"),
            country_transformed.get("iso_alpha3"),
            country_transformed.get("region"),
        )
        return str(row["country_id"])

    async def _upsert_currency(
        self,
        conn: asyncpg.Connection,
        currency_transformed: dict[str, Any] | None,
    ) -> str | None:
        """Insert or get DimCurrency. Returns currency_id."""
        if not currency_transformed:
            return None

        row = await conn.fetchrow(
            """
            INSERT INTO dim_currency
                (currency_code, currency_name, symbol)
            VALUES ($1, $2, $3)
            ON CONFLICT (currency_code)
            DO UPDATE SET
                currency_code = EXCLUDED.currency_code
            RETURNING currency_id
            """,
            currency_transformed["currency_code"],
            currency_transformed.get("currency_name"),
            currency_transformed.get("symbol"),
        )
        return str(row["currency_id"])

    async def _upsert_dates(
        self,
        conn: asyncpg.Connection,
        dates_transformed: list[dict[str, Any]],
    ) -> None:
        """
        Insert DimDate rows for each year header.
        Handles 'None' string for calendar_year on estimate years.
        ON CONFLICT on year_value — skips existing years.
        """
        for date in dates_transformed:
            # calendar_year comes as "None" string for estimate years
            # must convert to actual None for PostgreSQL integer column
            calendar_year = date.get("calendar_year")
            if calendar_year == "None" or calendar_year is None:
                calendar_year = None
            else:
                calendar_year = int(calendar_year)

            await conn.execute(
                """
                INSERT INTO dim_date
                    (year_value, calendar_year, is_estimate, sort_order)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (year_value) DO NOTHING
                """,
                date["year_value"],
                calendar_year,
                date["is_estimate"],
                date["sort_order"],
            )

    async def _upsert_company(
        self,
        conn: asyncpg.Connection,
        entity_name: str,
        is_new_company: bool,
    ) -> str:
        """
        Insert new DimCompany or fetch existing.
        is_new_company already resolved by transformer —
        no extra DB query needed.
        Returns company_id.
        """
        if is_new_company:
            row = await conn.fetchrow(
                """
                INSERT INTO dim_company (entity_name)
                VALUES ($1)
                ON CONFLICT (entity_name) DO NOTHING
                RETURNING company_id
                """,
                entity_name,
            )
            if row:
                return str(row["company_id"])

            logger.info(
                "dim_company insert conflict resolved via select entity_name=%s",
                entity_name,
            )
            row = await conn.fetchrow(
                """
                SELECT company_id
                FROM dim_company
                WHERE entity_name = $1
                """,
                entity_name,
            )
            if not row:
                raise ValueError(
                    f"Company conflict fallback failed to find entity: {entity_name}"
                )
            return str(row["company_id"])

        row = await conn.fetchrow(
            """
            SELECT company_id
            FROM dim_company
            WHERE entity_name = $1
            """,
            entity_name,
        )
        if not row:
            raise ValueError(
                f"Expected existing company not found: {entity_name}"
            )
        return str(row["company_id"])

    async def _close_previous_version(
        self,
        conn: asyncpg.Connection,
        company_id: str,
    ) -> None:
        """
        SCD Type 2 — close the current active version.
        Sets valid_to=NOW() and is_current=FALSE.
        Must run before inserting the new version.
        """
        await conn.execute(
            """
            UPDATE company_versions
            SET valid_to = NOW(),
                is_current = FALSE
            WHERE company_id = $1
            AND is_current IS TRUE
            """,
            company_id,
        )

    async def _insert_company_version(
        self,
        conn: asyncpg.Connection,
        company_id: str,
        upload_id: str,
        version_number: int,
    ) -> str:
        """
        Insert new CompanyVersion row.
        valid_to=NULL means this is the current open version.
        Returns version_id.
        """
        row = await conn.fetchrow(
            """
            INSERT INTO company_versions
                (company_id, upload_id, version_number,
                 valid_from, valid_to, is_current, created_at)
            VALUES ($1, $2, $3, NOW(), NULL, TRUE, NOW())
            RETURNING version_id
            """,
            company_id,
            upload_id,
            version_number,
        )
        return str(row["version_id"])

    async def _insert_snapshot(
        self,
        conn: asyncpg.Connection,
        payload: dict[str, Any],
        company_id: str,
        version_id: str,
        upload_id: str,
        country_id: str | None,
        currency_id: str | None,
    ) -> str:
        """
        Insert SnapshotFact row with all MASTER sheet data.
        JSONB fields serialised to JSON strings for asyncpg.
        Returns snapshot_id.
        """
        # fix Liquidity risk sub-score
        # raw value is numeric string "4.862" — should be "-2 notches"
        # extract correct string value from raw_data
        risk_sub_scores = self._fix_risk_sub_scores(
            payload.get("risk_sub_scores", {}),
            payload.get("raw_data", {}),
        )

        row = await conn.fetchrow(
            """
            INSERT INTO snapshot_fact (
                company_id,
                version_id,
                upload_id,
                country_id,
                currency_id,
                entity_name,
                corporate_sector,
                country_name,
                currency_code,
                accounting_principles,
                business_year_end,
                rating_methodologies,
                industry_risk_name,
                industry_risk_score,
                industry_weight,
                segmentation_criteria,
                business_risk_profile,
                financial_risk_profile,
                risk_sub_scores,
                credit_metrics,
                raw_data,
                snapshot_at
            ) VALUES (
                $1,  $2,  $3,  $4,  $5,
                $6,  $7,  $8,  $9,  $10,
                $11, $12, $13, $14,
                $15, $16, $17, $18,
                $19, $20, $21,
                NOW()
            )
            RETURNING snapshot_id
            """,
            # foreign keys
            company_id,
            version_id,
            upload_id,
            country_id,
            currency_id,
            # entity metadata
            payload.get("rated_entity"),
            payload.get("corporate_sector"),
            payload.get("country"),
            payload.get("currency"),
            payload.get("accounting_principles"),
            payload.get("business_year_end"),
            # TEXT[] array
            payload.get("rating_methodologies", []),
            # industry risk
            payload.get("industry_risk"),
            payload.get("industry_risk_score"),
            payload.get("industry_weight"),
            payload.get("segmentation_criteria"),
            # risk profiles
            payload.get("business_risk_profile"),
            payload.get("financial_risk_profile"),
            # JSONB — serialise to JSON string for asyncpg
            json.dumps(risk_sub_scores),
            json.dumps(payload.get("credit_metrics", {})),
            json.dumps(payload.get("raw_data", {})),
        )
        return str(row["snapshot_id"])

    async def _update_current_snapshot(
        self,
        conn: asyncpg.Connection,
        company_id: str,
        snapshot_id: str,
    ) -> None:
        """Update DimCompany.current_snapshot_id to latest snapshot."""
        await conn.execute(
            """
            UPDATE dim_company
            SET current_snapshot_id = $1
            WHERE company_id = $2
            """,
            snapshot_id,
            company_id,
        )

    async def _insert_quality_report(
        self,
        conn: asyncpg.Connection,
        upload_id: str,
        snapshot_id: str,
        validation_result: dict[str, Any],
    ) -> None:
        """Insert DataQualityReport row."""
        errors = validation_result.get("errors", [])
        warnings = validation_result.get("warnings", [])
        total_fields = 12
        error_count = len(errors)
        present_fields = total_fields - error_count
        completeness = round(present_fields / total_fields, 3)
        validity = round(present_fields / total_fields, 3)

        await conn.execute(
            """
            INSERT INTO data_quality_report (
                upload_id,
                snapshot_id,
                completeness_score,
                validity_score,
                total_fields,
                present_fields,
                error_count,
                warning_count,
                errors,
                warnings,
                created_at
            ) VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                NOW()
            )
            """,
            upload_id,
            snapshot_id,
            completeness,
            validity,
            total_fields,
            present_fields,
            error_count,
            len(warnings),
            json.dumps(errors),
            json.dumps(warnings),
        )

    async def _mark_completed(
        self,
        conn: asyncpg.Connection,
        upload_id: str,
        rows_extracted: int,
    ) -> None:
        """Mark upload_audit as completed. Last step in transaction."""
        await conn.execute(
            """
            UPDATE upload_audit
            SET status = 'completed',
                processed_at = NOW(),
                rows_extracted = $1
            WHERE upload_id = $2
            """,
            rows_extracted,
            upload_id,
        )

    async def _mark_failed(
        self,
        upload_id: str,
        error: str,
    ) -> None:
        """
        Mark upload_audit as failed using a SEPARATE connection.
        The main transaction has already rolled back by the time
        this is called — a new connection guarantees the failure
        is recorded regardless.
        """
        conn = await asyncpg.connect(self._dsn())
        try:
            await conn.execute(
                """
                UPDATE upload_audit
                SET status = 'failed',
                    processed_at = NOW(),
                    error_message = $1
                WHERE upload_id = $2
                """,
                error[:500],
                upload_id,
            )
        except Exception as exc:
            logger.error(
                "failed to mark upload as failed upload_id=%s error=%s",
                upload_id,
                str(exc),
            )
        finally:
            await conn.close()

    # ── private utilities ─────────────────────────────────────

    def _fix_risk_sub_scores(
        self,
        risk_sub_scores: dict[str, Any],
        raw_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Fix Liquidity value in risk_sub_scores.

        The parser stores the numeric credit metric value '4.862'
        for Liquidity instead of the risk notation '-2 notches'.
        The correct value is in raw_data['Liquidity'] as a string.
        """
        fixed = dict(risk_sub_scores)

        liquidity_raw = raw_data.get("Liquidity", [])
        string_values = [
            v for v in liquidity_raw
            if isinstance(v, str) and v not in {"Locked", "No data"}
        ]
        if string_values:
            fixed["Liquidity"] = string_values[0]

        # fix "None" string values → actual None
        for key, value in fixed.items():
            if value == "None":
                fixed[key] = None

        return fixed

    def _dsn(self) -> str:
        """Convert SQLAlchemy-style URL to asyncpg DSN."""
        url = str(settings.database_url)
        for prefix in (
            "postgresql+psycopg://",
            "postgresql+psycopg2://",
            "postgresql+asyncpg://",
        ):
            if url.startswith(prefix):
                return "postgresql://" + url.split("://", 1)[1]
        return url