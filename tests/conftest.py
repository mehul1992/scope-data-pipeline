"""Shared pytest fixtures for API, service, and repository tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_company_service, get_snapshot_service, get_upload_service
from app.main import app


@pytest.fixture
def sample_uuids() -> dict[str, UUID]:
    return {
        "company": UUID("11111111-1111-1111-1111-111111111111"),
        "snapshot": UUID("22222222-2222-2222-2222-222222222222"),
        "upload": UUID("33333333-3333-3333-3333-333333333333"),
        "version": UUID("44444444-4444-4444-4444-444444444444"),
    }


@pytest.fixture
def mock_company_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_snapshot_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_upload_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(
    mock_company_service: MagicMock,
    mock_snapshot_service: MagicMock,
    mock_upload_service: MagicMock,
) -> Any:
    app.dependency_overrides[get_company_service] = lambda: mock_company_service
    app.dependency_overrides[get_snapshot_service] = lambda: mock_snapshot_service
    app.dependency_overrides[get_upload_service] = lambda: mock_upload_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db_session() -> MagicMock:
    return MagicMock()


def execute_result_scalars_all(rows: list[Any]) -> MagicMock:
    """SQLAlchemy-style result for execute().scalars().all()."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


def execute_result_scalar_one(obj: Any | None) -> MagicMock:
    """SQLAlchemy-style result for execute().scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = obj
    return result


def execute_result_all(rows: list[Any]) -> MagicMock:
    """SQLAlchemy-style result for execute().all()."""
    result = MagicMock()
    result.all.return_value = rows
    return result


def execute_result_one_mapping(mapping: dict[str, Any]) -> MagicMock:
    """SQLAlchemy-style result for execute().one() with row._mapping."""
    row = MagicMock()
    row._mapping = mapping
    result = MagicMock()
    result.one.return_value = row
    return result
