from __future__ import annotations

from typing import Any

from app.etl.loaders.warehouse_loader import WarehouseLoader


class LoadOperator:
    """Operator stub for loading transformed payloads into storage."""

    def __init__(self, transformed_payload: dict[str, Any]) -> None:
        self.transformed_payload = transformed_payload

    def execute(self) -> dict[str, Any]:
        warehouse_loader = WarehouseLoader()
        return warehouse_loader.load(self.transformed_payload)
