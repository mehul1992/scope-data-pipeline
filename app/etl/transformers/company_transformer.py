"""
Company transformer.

Handles SCD Type 2 logic for DimCompany and CompanyVersion.

Rules:
  - New entity_name → create DimCompany, version_number = 1
  - Existing entity_name → increment version_number,
    close previous version (set valid_to, is_current=False)
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import asyncpg
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class CompanyTransformer:
    """
    Transforms parsed company data into DimCompany
    and CompanyVersion payloads.
    """

    def transform(
        self,
        company_entity: str,
        upload_id: str,
    ) -> dict[str, Any]:
        """
        Build DimCompany and CompanyVersion payloads.

        Args:
            company_entity: entity_name from MASTER sheet
            upload_id:      UUID of current upload_audit row

        Returns:
            dict with keys:
                company_payload        → for dim_company upsert
                version_payload        → for company_versions insert
                is_new_company         → bool
                previous_version_close → payload to close previous version
        """
        now = datetime.now(timezone.utc)

        # asyncpg query — no SQLAlchemy
        company_details = asyncio.run(
            self._is_new_company(company_entity)
        )

        is_new = company_details["is_new_company"]
        company_id = company_details["company_id"]
        version_number = self._get_version_number(company_details)

        company_payload = {
            "company_id": company_id,
            "entity_name": company_entity,
            "is_new_company": is_new,
        }

        version_payload = {
            "upload_id": upload_id,
            "version_number": version_number,
            "valid_from": now,
            "valid_to": None,
            "is_current": True,
            "created_at": now,
        }

        previous_version_close = None
        if not is_new:
            previous_version_close = {
                "version_number": company_details["version_number"],
                "valid_to": now,
                "is_current": False,
            }

        logger.info(
            "company version transformed entity=%s version=%s is_new=%s",
            company_entity,
            version_number,
            is_new,
        )

        return {
            "company_payload": company_payload,
            "version_payload": version_payload,
            "is_new_company": is_new,
            "previous_version_close": previous_version_close,
        }

    def _get_version_number(
        self, company_details: dict[str, Any]
    ) -> int:
        """Return 1 for new company, else increment existing version."""
        if company_details["is_new_company"]:
            return 1
        return company_details["version_number"] + 1

    async def _is_new_company(
        self, company_entity: str
    ) -> dict[str, Any]:
        """
        Query dim_company + company_versions to check if company exists.

        Returns:
            is_new_company: True if no record found
            version_number: current version_number or 0 if new
        """
        conn = await asyncpg.connect(self._dsn())
        try:
            row = await conn.fetchrow(
                """
                SELECT dc.entity_name, cv.version_number
                FROM dim_company dc
                INNER JOIN company_versions cv
                    ON dc.company_id = cv.company_id
                WHERE dc.entity_name = $1
                AND cv.is_current IS TRUE
                """,
                company_entity,
            )
            return {
                "is_new_company": row is None,
                "company_id": row["company_id"] if row else None,
                "version_number": row["version_number"] if row else 0,
            }
        finally:
            await conn.close()

    def _dsn(self) -> str:
        url = str(settings.database_url)
        for prefix in (
            "postgresql+psycopg://",
            "postgresql+psycopg2://",
            "postgresql+asyncpg://",
        ):
            if url.startswith(prefix):
                return "postgresql://" + url.split("://", 1)[1]
        return url