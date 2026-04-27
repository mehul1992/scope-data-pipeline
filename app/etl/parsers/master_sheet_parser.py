from __future__ import annotations

from pathlib import Path
from typing import Any
import logging

import openpyxl
from pydantic import BaseModel, Field
from app.core.config import settings

logger = logging.getLogger(__name__)
SHEET_NAME = settings.SHEET_NAME


SENTINEL_VALUES: set[str] = {"Locked", "No data"}

CREDIT_METRICS_LABEL = "[Scope Credit Metrics]"

CREDIT_METRIC_FIELDS: list[str] = [
    "Scope-adjusted EBITDA interest cover",
    "Scope-adjusted debt/EBITDA",
    "Scope-adjusted FFO/debt",
    "Scope-adjusted loan/value",
    "Scope-adjusted FOCF/debt",
    "Liquidity",
]

RISK_PROFILE_FIELDS: list[str] = [
    "(Blended) Industry risk profile",
    "Competitive Positioning",
    "Market share",
    "Diversification",
    "Operating profitability",
    "Sector/company-specific factors (1)",
    "Sector/company-specific factors (2)",
    "Leverage",
    "Interest cover",
    "Cash flow cover",
    "Liquidity",
]

class ParsedMasterSheet(BaseModel):
    """
    Structured representation of the MASTER sheet.
    All fields are optional — validation layer enforces required fields.
    """

    # entity metadata
    rated_entity: str | None = None
    corporate_sector: str | None = None
    rating_methodologies: list[str] = Field(default_factory=list)

    # industry risk
    industry_risk: str | None = None
    industry_risk_score: str | None = None
    industry_weight: float | None = None
    segmentation_criteria: str | None = None

    # company metadata
    currency: str | None = None
    country: str | None = None
    accounting_principles: str | None = None
    business_year_end: str | None = None

    # risk profiles
    business_risk_profile: str | None = None
    financial_risk_profile: str | None = None
    risk_sub_scores: dict[str, str | None] = Field(default_factory=dict)

    # time series stored as JSONB
    credit_metrics: dict[str, Any] = Field(default_factory=dict)

    # full raw extraction for audit lineage
    raw_data: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


class MasterSheetParser:

    def __init__(self, file_path: str) -> None:
        self.file_path = Path(file_path)

    def parse(self) -> ParsedMasterSheet:

        wb = openpyxl.load_workbook(
            self.file_path,
            read_only=True,
            keep_vba=False,
            data_only=True,
        )

        ws = wb[SHEET_NAME]
        rows = self._read_rows(ws)
        wb.close()

        logger.info("master sheet read row count=%s rows=%s", len(rows), rows)

        return ParsedMasterSheet(
            rated_entity=self._single(rows, "Rated entity"),
            corporate_sector=self._single(rows, "CorporateSector"),
            rating_methodologies=self._multiple(
                rows, "Rating methodologies applied"
            ),
            industry_risk=self._single(rows, "Industry risk"),
            industry_risk_score=self._single(rows, "Industry risk score"),
            industry_weight=self._float(rows, "Industry weight"),
            segmentation_criteria=self._single(
                rows, "Segmentation criteria"
            ),
            currency=self._single(rows, "Reporting Currency/Units"),
            country=self._single(rows, "Country of origin"),
            accounting_principles=self._single(
                rows, "Accounting principles"
            ),
            business_year_end=self._single(rows, "End of business year"),
            business_risk_profile=self._single(
                rows, "Business risk profile"
            ),
            financial_risk_profile=self._single(
                rows, "Financial risk profile"
            ),
            risk_sub_scores=self._extract_risk_sub_scores(rows),
            credit_metrics=self._extract_credit_metrics(rows),
            raw_data=rows,
        )

     # Private helpers   

    def _read_rows(self, ws: Any) -> dict[str, list[Any]]:
        
        rows: dict[str, list[Any]] = {}
        for row in ws.iter_rows(values_only=True):
            label = row[1] if len(row) > 1 else None
            if label is None:
                continue
            values = [v for v in row[2:] if v is not None]
            rows[str(label).strip()] = values
        return rows

    def _single(self, rows: dict, label: str) -> str | None:
        """Return first value for label as stripped string, or None."""
        values = rows.get(label, [])
        if not values or values[0] is None:
            return None
        return str(values[0]).strip()

    def _multiple(self, rows: dict, label: str) -> list[str]:
        """Return all values for label as list of strings."""
        return [
            str(v).strip()
            for v in rows.get(label, [])
            if v is not None
        ]

    def _float(self, rows: dict, label: str) -> float | None:
        """Return first value as float, or None if missing or invalid."""
        values = rows.get(label, [])
        if not values:
            return None
        try:
            return float(values[0])
        except (ValueError, TypeError):
            logger.warning(
                "could not parse float label=%s value=%s",
                label=label,
                value=values[0],
            )
            return None

    def _extract_risk_sub_scores(
        self, rows: dict
    ) -> dict[str, str | None]:
        """Extract all risk profile sub-scores as a flat dict."""
        return {
            field: self._single(rows, field)
            for field in RISK_PROFILE_FIELDS
        }

    def _extract_credit_metrics(
        self, rows: dict
    ) -> dict[str, Any]:
        """Extract time-series credit metrics block."""
        
        year_headers = rows.get(CREDIT_METRICS_LABEL, [])
        if not year_headers:
            logger.warning("credit metrics header row not found label=%s", CREDIT_METRICS_LABEL)
            return {}

        years = [str(y) for y in year_headers]
        metrics: dict[str, dict[str, Any]] = {}

        for metric_label in CREDIT_METRIC_FIELDS:
            values = rows.get(metric_label, [])
            if not values:
                continue

            metric_data: dict[str, Any] = {}
            for year, value in zip(years, values):
                if isinstance(value, str) and value in SENTINEL_VALUES:
                    metric_data[year] = value
                elif value is not None:
                    try:
                        metric_data[year] = round(float(value), 6)
                    except (ValueError, TypeError):
                        metric_data[year] = value

            metrics[metric_label] = metric_data

        return {
            "years": years,
            "metrics": metrics,
            "sentinels": {
                "Locked": "data locked by system",
                "No data": "metric not applicable for this period",
            },
        }    