"""
Abstract base validator.

All validators extend BaseValidator and implement the validate() method.
The pipeline calls each validator in sequence and collects results.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """Result returned by every validator."""

    field: str
    message: str
    severity: str  # "error" blocks load | "warning" logs but continues

    model_config = {"frozen": True}


class ValidationReport(BaseModel):
    """Aggregated report from all validators for one file."""

    filename: str
    is_valid: bool
    errors: list[ValidationResult] = []
    warnings: list[ValidationResult] = []
    completeness_score: float = 0.0
    validity_score: float = 0.0

    def has_errors(self) -> bool:
        """Return True if any hard errors exist that block loading."""
        return len(self.errors) > 0

    def summary(self) -> dict[str, Any]:
        """Return a JSON-serialisable summary for logging and reporting."""
        return {
            "filename": self.filename,
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "completeness_score": self.completeness_score,
            "validity_score": self.validity_score,
            "errors": [e.model_dump() for e in self.errors],
            "warnings": [w.model_dump() for w in self.warnings],
        }


class BaseValidator(ABC):
    """
    Abstract base class for all validators.

    Each concrete validator is responsible for one category of rules:
        - RequiredFieldsValidator  — field presence
        - DataTypeValidator        — type correctness
        - BusinessRulesValidator   — domain-specific rules

    Usage:
        validator = RequiredFieldsValidator()
        results = validator.validate(parsed_data)
    """

    @abstractmethod
    def validate(
        self, data: Any
    ) -> list[ValidationResult]:
        """
        Run validation rules against parsed data.

        Returns list of ValidationResult.
        Empty list means all rules passed.
        """
        ...

    def _error(self, field: str, message: str) -> ValidationResult:
        """Convenience method for creating error results."""
        return ValidationResult(
            field=field,
            message=message,
            severity="error",
        )

    def _warning(self, field: str, message: str) -> ValidationResult:
        """Convenience method for creating warning results."""
        return ValidationResult(
            field=field,
            message=message,
            severity="warning",
        )