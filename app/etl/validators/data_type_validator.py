"""
Data type validator.

Validates that extracted values have the correct types
and formats for loading into the warehouse.
"""
from __future__ import annotations

import logging
from app.etl.parsers.master_sheet_parser import ParsedMasterSheet
from app.etl.validators.base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)

VALID_CURRENCIES: set[str] = {"EUR", "CHF", "USD", "GBP"}

VALID_MONTHS: set[str] = {
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
}

# valid rating notation values
VALID_RATING_NOTATIONS: set[str] = {
    "AAA", "AA+", "AA", "AA-",
    "A+", "A", "A-",
    "BBB+", "BBB", "BBB-",
    "BB+", "BB", "BB-",
    "B+", "B", "B-",
    "CCC+", "CCC", "CCC-",
    "CC", "C", "D",
}


class DataTypeValidator(BaseValidator):
    """
    Validates types and formats of parsed fields.

    Rules:
        currency         → must be in VALID_CURRENCIES
        business_year_end → must be a valid month name
        industry_weight  → must be numeric (float)
        risk profiles    → must be valid rating notation or notch adjustment
        credit_metrics   → numeric values must be parseable as float
    """

    def validate(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        results: list[ValidationResult] = []

        results.extend(self._validate_currency(data))
        results.extend(self._validate_business_year_end(data))
        results.extend(self._validate_industry_weight_type(data))
        results.extend(self._validate_risk_profiles(data))
        results.extend(self._validate_credit_metrics_types(data))

        return results

    def _validate_currency(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        if data.currency and data.currency.upper() not in VALID_CURRENCIES:
            return [self._error(
                field="currency",
                message=(
                    f"Invalid currency '{data.currency}'. "
                    f"Must be one of {sorted(VALID_CURRENCIES)}"
                ),
            )]
        return []

    def _validate_business_year_end(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        if (
            data.business_year_end
            and data.business_year_end not in VALID_MONTHS
        ):
            return [self._error(
                field="business_year_end",
                message=(
                    f"Invalid month '{data.business_year_end}'. "
                    f"Must be a full month name e.g. 'December'"
                ),
            )]
        return []

    def _validate_industry_weight_type(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        if data.industry_weight is not None:
            if not isinstance(data.industry_weight, (int, float)):
                return [self._error(
                    field="industry_weight",
                    message=(
                        f"Industry weight must be numeric, "
                        f"got '{data.industry_weight}'"
                    ),
                )]
        return []

    def _validate_risk_profiles(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        """
        Validate risk profile scores are valid rating notations.
        Notch adjustments like '-2 notches' are allowed as warnings.
        """
        results: list[ValidationResult] = []

        profiles_to_check = {
            "business_risk_profile": data.business_risk_profile,
            "financial_risk_profile": data.financial_risk_profile,
        }

        for field, value in profiles_to_check.items():
            if value is None:
                continue
            if value not in VALID_RATING_NOTATIONS:
                # notch adjustments are valid but worth flagging
                if "notch" in value.lower():
                    results.append(self._warning(
                        field=field,
                        message=(
                            f"'{value}' is a notch adjustment — "
                            f"not a standard rating notation"
                        ),
                    ))
                else:
                    results.append(self._error(
                        field=field,
                        message=(
                            f"'{value}' is not a valid rating notation"
                        ),
                    ))

        # check risk sub scores
        for sub_field, value in data.risk_sub_scores.items():
            if value is None:
                continue
            if (
                value not in VALID_RATING_NOTATIONS
                and "notch" not in value.lower()
            ):
                results.append(self._warning(
                    field=sub_field,
                    message=f"Sub-score '{value}' is not standard notation",
                ))

        return results

    def _validate_credit_metrics_types(
        self, data: ParsedMasterSheet
    ) -> list[ValidationResult]:
        """
        Check credit metric values are numeric or valid sentinels.
        Non-numeric, non-sentinel values are flagged as warnings.
        """
        results: list[ValidationResult] = []
        metrics = data.credit_metrics.get("metrics", {})
        sentinels = {"Locked", "No data"}

        for metric_name, year_values in metrics.items():
            for year, value in year_values.items():
                if isinstance(value, str) and value in sentinels:
                    continue
                if not isinstance(value, (int, float)):
                    results.append(self._warning(
                        field=metric_name,
                        message=(
                            f"Non-numeric value '{value}' "
                            f"for year {year} in '{metric_name}'"
                        ),
                    ))

        return results