from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories.company_repository import CompanyRepository
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.upload_repository import UploadRepository
from app.services.company_service import CompanyService
from app.services.snapshot_service import SnapshotService
from app.services.upload_service import UploadService

DbSession = Annotated[Session, Depends(get_db_session)]


def get_company_repository(db: DbSession) -> CompanyRepository:
    return CompanyRepository(db)


def get_company_service(
    repo: Annotated[CompanyRepository, Depends(get_company_repository)],
) -> CompanyService:
    return CompanyService(repo)


CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]


def get_snapshot_repository(db: DbSession) -> SnapshotRepository:
    return SnapshotRepository(db)


def get_snapshot_service(
    repo: Annotated[SnapshotRepository, Depends(get_snapshot_repository)],
) -> SnapshotService:
    return SnapshotService(repo)


SnapshotServiceDep = Annotated[SnapshotService, Depends(get_snapshot_service)]


def get_upload_repository(db: DbSession) -> UploadRepository:
    return UploadRepository(db)


def get_upload_service(
    repo: Annotated[UploadRepository, Depends(get_upload_repository)],
) -> UploadService:
    return UploadService(repo)


UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]
