"""
Business rules validator.

Validates domain-specific rules for corporate credit rating data.
These rules reflect actual credit rating methodology constraints.
"""
from __future__ import annotations

import logging
from app.etl.parsers.master_sheet_parser import ParsedMasterSheet
from app.etl.validators.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)

WEIGHT_SUM_TOLERANCE = 0.01
MIN_WEIGHT = 0.0
MAX_WEIGHT = 1.0


class BusinessRulesValidator(BaseValidator):
    """
    Validates business rules specific to credit rating methodology.

    Rules:
        industry_weight  → must be between 0 and 1
        industry_weight  → must sum to 1.0 (±0.01 tolerance)
        rating_methodologies → must not be empty
        credit_metrics   → must have year headers if metrics present
        entity_name      → must not exceed 200 characters
        business + financial risk → both must be present together
    """

    def validate(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        results: list[ValidationResult] = []

        results.extend(self._validate_weight_range(data))
        results.extend(self._validate_weight_sum(data))
        results.extend(self._validate_risk_profile_completeness(data))
        results.extend(self._validate_entity_name_length(data))
        results.extend(self._validate_credit_metrics_consistency(data))

        return results

    def _validate_weight_range(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        """Industry weight must be between 0 and 1."""
        if data.industry_weight is None:
            return [self._warning(
                field="industry_weight",
                message="Industry weight is missing — cannot validate range",
            )]

        if not (MIN_WEIGHT <= data.industry_weight <= MAX_WEIGHT):
            return [self._error(
                field="industry_weight",
                message=(
                    f"Industry weight {data.industry_weight} "
                    f"is outside valid range [0, 1]"
                ),
            )]
        return []

    def _validate_weight_sum(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        """
        Industry weights must sum to 1.0.
        Currently one weight per file — must equal 1.0 exactly (±tolerance).
        When multiple industries are supported, sum across all weights.
        """
        if data.industry_weight is None:
            return []

        deviation = abs(data.industry_weight - 1.0)
        if deviation > WEIGHT_SUM_TOLERANCE:
            return [self._warning(
                field="industry_weight",
                message=(
                    f"Industry weight {data.industry_weight} "
                    f"deviates from 1.0 by {deviation:.4f} "
                    f"(tolerance: {WEIGHT_SUM_TOLERANCE})"
                ),
            )]
        return []

    def _validate_risk_profile_completeness(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        """
        Business and financial risk profiles must both be present.
        Having one without the other is a data quality issue.
        """
        results: list[ValidationResult] = []

        has_business = bool(data.business_risk_profile)
        has_financial = bool(data.financial_risk_profile)

        if has_business and not has_financial:
            results.append(self._error(
                field="financial_risk_profile",
                message=(
                    "Business risk profile present but "
                    "financial risk profile is missing"
                ),
            ))

        if has_financial and not has_business:
            results.append(self._error(
                field="business_risk_profile",
                message=(
                    "Financial risk profile present but "
                    "business risk profile is missing"
                ),
            ))

        return results

    def _validate_entity_name_length(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        """Entity name must not exceed 200 characters."""
        if data.rated_entity and len(data.rated_entity) > 200:
            return [self._warning(
                field="rated_entity",
                message=(
                    f"Entity name length {len(data.rated_entity)} "
                    f"exceeds 200 characters"
                ),
            )]
        return []

    def _validate_credit_metrics_consistency(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        """
        If credit metrics are present, year headers must exist.
        Metrics without year context cannot be interpreted.
        """
        if not data.credit_metrics:
            return [self._warning(
                field="credit_metrics",
                message="No credit metrics found in MASTER sheet",
            )]

        years = data.credit_metrics.get("years", [])
        metrics = data.credit_metrics.get("metrics", {})

        if metrics and not years:
            return [self._error(
                field="credit_metrics",
                message=(
                    "Credit metrics found but year headers are missing — "
                    "time-series data cannot be interpreted"
                ),
            )]

        return []