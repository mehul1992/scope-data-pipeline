"""
ORM package — import all models so SQLAlchemy registers tables on Base.metadata.

Alembic (app/db/migrations/env.py) uses ``from app.models import Base``; if models
are not imported here, autogenerate only sees a subset of tables and diffs are wrong.
"""

from app.models.base import Base
from app.models.company_dim import CompanyVersion, DimCompany
from app.models.country_dim import DimCountry
from app.models.currency_dim import DimCurrency
from app.models.date_dim import DimDate
from app.models.snapshot_fact import DataQualityReport, SnapshotFact
from app.models.upload_dim import UploadAudit

__all__ = [
    "Base",
    "CompanyVersion",
    "DataQualityReport",
    "DimCompany",
    "DimCountry",
    "DimCurrency",
    "DimDate",
    "SnapshotFact",
    "UploadAudit",
]
