# app/airflow/operators/validate_operator.py

from __future__ import annotations

from typing import Any

from app.etl.validators.base_validator import ValidationResult
from app.etl.validators.required_fields_validator import RequiredFieldsValidator
from app.etl.validators.data_type_validator import DataTypeValidator
from app.etl.validators.business_rules_validator import BusinessRulesValidator
from app.etl.parsers.master_sheet_parser import ParsedMasterSheet


class ValidateOperator:
    """
    Runs all validators in sequence and returns results.
    """

    def __init__(self, parsed: dict[str, Any]) -> None:
        self.parsed = parsed
        self.validators = [
            RequiredFieldsValidator(),
            DataTypeValidator(),
            BusinessRulesValidator(),
        ]

    def execute(self) -> dict[str, Any]:
        
        data = ParsedMasterSheet(**self.parsed)

        all_results: list[ValidationResult] = []
        for v in self.validators:
            all_results.extend(v.validate(data))

        errors = [r for r in all_results if r.severity == "error"]
        warnings = [r for r in all_results if r.severity == "warning"]

        return {
            "is_valid": len(errors) == 0,
            "errors": [e.model_dump() for e in errors],
            "warnings": [w.model_dump() for w in warnings],
        }