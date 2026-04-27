from __future__ import annotations

from typing import Any
import logging
from airflow.exceptions import AirflowSkipException
from pathlib import Path
from app.utils.file_utils import compute_sha256
import asyncio
import asyncpg
from app.core.config import settings

logger = logging.getLogger(__name__)

class ExtractOperator:
    """Operator stub for extracting metadata from .xlsm files."""

    def __init__(self, input_directory: str) -> None:
        self.input_directory = input_directory

    def execute(self) -> list[dict[str, Any]]:
        input_directory = Path(self.input_directory)

        if not input_directory.exists():
            logger.warning("input directory not found path=%s", input_directory)
            raise AirflowSkipException(f"Input directory does not exist: {input_directory}")

        xlsm_files = list(input_directory.glob("*.xlsm"))

        if not xlsm_files:
            logger.info("no .xlsm files found path=%s", input_directory)
            raise AirflowSkipException("No .xlsm files found in input directory")

        logger.info("files discovered count=%s", len(xlsm_files))

        # compute SHA-256 for each file
        file_hashes: dict[str, str] = {}
        for file in xlsm_files:
            sha256 = compute_sha256(str(file))
            file_hashes[str(file)] = sha256
            logger.info("hash computed file=%s sha256_prefix=%s", file.name, sha256[:8])

        # query upload_audit for already completed hashes (sync bridge)
        processed_hashes: set[str] = asyncio.run(self._get_processed_hashes())
        logger.info("processed hashes loaded count=%s", len(processed_hashes))

        # filter out already processed files
        new_files: list[dict[str, Any]] = []
        for file_path, sha256 in file_hashes.items():
            if sha256 in processed_hashes:
                logger.info(
                    "skipping already processed file file=%s sha256_prefix=%s",
                    Path(file_path).name,
                    sha256[:8],
                )
            else:
                
                # register as pending in upload_audit
                upload_id = asyncio.run(
                    self._register_pending(
                        filename=Path(file_path).name,
                        sha256=sha256,
                        file_path=file_path,
                    )
                )
                logger.info("registered as pending file=%s upload_id=%s", Path(file_path).name, upload_id)
                new_files.append({"file_path": file_path, "sha256": sha256, "upload_id": upload_id})

        if not new_files:
            logger.info("all files already processed, skipping pipeline")
            raise AirflowSkipException("All files already processed")

        logger.info("new files to process count=%s files=%s", len(new_files), new_files)
        return new_files
    

    def _asyncpg_dsn(self) -> str:
        """Normalize SQLAlchemy-style URL to asyncpg/postgres DSN."""
        url = settings.database_url
        for prefix in ("postgresql+psycopg://", "postgresql+psycopg2://", "postgresql+asyncpg://"):
            if url.startswith(prefix):
                return "postgresql://" + url.split("://", 1)[1]
        return url


    async def _get_processed_hashes(self) -> set[str]:
        """Query upload_audit and return all SHA-256 hashes with status=completed."""
        conn = await asyncpg.connect(self._asyncpg_dsn())
        try:
            rows = await conn.fetch(
                "SELECT file_sha256 FROM upload_audit WHERE status = $1",
                "completed",
            )
            return {str(r["file_sha256"]) for r in rows}
        finally:
            await conn.close()


    async def _register_pending(self,filename: str, sha256: str, file_path: str) -> None:
        """Insert a new upload_audit row with status=pending."""
        conn = await asyncpg.connect(self._asyncpg_dsn())
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO upload_audit (filename, file_sha256, file_path, status)
                VALUES ($1, $2, $3, $4)
                RETURNING upload_id
                """,
                filename,
                sha256,
                file_path,
                "pending",
            )
            return str(row["upload_id"]) if row else None
        finally:
            await conn.close()
