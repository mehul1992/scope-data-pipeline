from __future__ import annotations

from typing import Any

from airflow.models.baseoperator import BaseOperator
from airflow.utils.context import Context


class ExtractOperator(BaseOperator):
    """Operator stub for extracting metadata from .xlsm files."""

    def __init__(self, input_directory: str, **kwargs: object) -> None:
        """Initialize extraction operator configuration."""
        super().__init__(**kwargs)

    def execute(self, context: Context) -> dict[str, Any]:
        """Execute extraction stage stub."""
        pass
