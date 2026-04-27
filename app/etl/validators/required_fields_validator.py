"""
Required fields validator.

Checks that all mandatory fields are present and non-empty
in the parsed MASTER sheet data.
"""
from __future__ import annotations

import logging
from app.etl.parsers.master_sheet_parser import ParsedMasterSheet
from app.etl.validators.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)

# fields that MUST be present to allow loading
REQUIRED_FIELDS: dict[str, str] = {
    "rated_entity": "Rated entity",
    "corporate_sector": "CorporateSector",
    "currency": "Reporting Currency/Units",
    "country": "Country of origin",
    "accounting_principles": "Accounting principles",
    "business_year_end": "End of business year",
    "business_risk_profile": "Business risk profile",
    "financial_risk_profile": "Financial risk profile",
    "industry_risk_score": "Industry risk score",
}

# fields that SHOULD be present but are not blocking
RECOMMENDED_FIELDS: dict[str, str] = {
    "industry_risk": "Industry risk",
    "industry_weight": "Industry weight",
    "segmentation_criteria": "Segmentation criteria",
}


class RequiredFieldsValidator(BaseValidator):
    """
    Validates presence of required and recommended fields.

    Required fields missing → error (blocks load)
    Recommended fields missing → warning (logs, does not block)
    Empty rating_methodologies list → error
    """

    def validate(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        results: list[ValidationResult] = []

        # check required fields
        for attr, label in REQUIRED_FIELDS.items():
            value = getattr(data, attr, None)
            if not value:
                results.append(
                    self._error(
                        field=label,
                        message=f"Required field '{label}' is missing or empty",
                    )
                )
                logger.warning("missing required field label=%s", label)

        # check rating methodologies separately — it is a list
        if not data.rating_methodologies:
            results.append(
                self._error(
                    field="Rating methodologies applied",
                    message="At least one rating methodology must be specified",
                )
            )

        # check recommended fields — warnings only
        for attr, label in RECOMMENDED_FIELDS.items():
            value = getattr(data, attr, None)
            if value is None:
                results.append(
                    self._warning(
                        field=label,
                        message=f"Recommended field '{label}' is missing",
                    )
                )

        return results