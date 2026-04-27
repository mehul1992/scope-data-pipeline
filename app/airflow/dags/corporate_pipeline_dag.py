from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import asyncpg
import pendulum
from airflow.exceptions import AirflowSkipException
from airflow.sdk import dag, task
# from app.airflow.sensors.file_arrival_sensor import FileArrivalSensor
from app.etl.parsers.master_sheet_parser import ParsedMasterSheet, MasterSheetParser
from app.airflow.operators.validate_operator import ValidateOperator
from app.airflow.operators.transform_operator import TransformOperator
from app.airflow.operators.load_operator import LoadOperator
from app.core.config import settings
from app.utils.file_utils import compute_sha256

logger = logging.getLogger(__name__)


def _asyncpg_dsn() -> str:
    """Normalize SQLAlchemy-style URL to asyncpg/postgres DSN."""
    url = settings.database_url
    for prefix in ("postgresql+psycopg://", "postgresql+psycopg2://", "postgresql+asyncpg://"):
        if url.startswith(prefix):
            return "postgresql://" + url.split("://", 1)[1]
    return url


async def _get_processed_hashes() -> set[str]:
    """Query upload_audit and return all SHA-256 hashes with status=completed."""
    conn = await asyncpg.connect(_asyncpg_dsn())
    try:
        rows = await conn.fetch(
            "SELECT file_sha256 FROM upload_audit WHERE status = $1",
            "completed",
        )
        return {str(r["file_sha256"]) for r in rows}
    finally:
        await conn.close()


async def _register_pending(filename: str, sha256: str, file_path: str) -> None:
    """Insert a new upload_audit row with status=pending."""
    conn = await asyncpg.connect(_asyncpg_dsn())
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO upload_audit (filename, file_sha256, file_path, status)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (file_sha256)
            DO UPDATE SET
                status = 'pending',
                error_message = NULL,
                processed_at = NULL
            WHERE upload_audit.status = 'failed'
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

@dag(
    dag_id="corporate_pipeline_dag",
    schedule=None,
    start_date=pendulum.datetime(2025, 4, 23, tz="UTC"),
    catchup=False,
    tags=["corporate", "etl"],
)
def build_corporate_pipeline_dag() -> None:

    @task
    def extract_stage(input_directory: str = str(settings.DATA_DIR)) -> list[str]:
        input_path = Path(input_directory)

        if not input_path.exists():
            logger.warning("input directory not found path=%s", input_directory)
            raise AirflowSkipException(f"Input directory does not exist: {input_directory}")

        xlsm_files = list(input_path.glob("*.xlsm"))

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
        processed_hashes: set[str] = asyncio.run(_get_processed_hashes())
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
                    _register_pending(
                        filename=Path(file_path).name,
                        sha256=sha256,
                        file_path=file_path,
                    )
                )
                logger.info("registered as pending file=%s", Path(file_path).name)
                new_files.append({"file_path": file_path, "sha256": sha256, "upload_id": upload_id})

        if not new_files:
            logger.info("all files already processed, skipping pipeline")
            raise AirflowSkipException("All files already processed")

        logger.info("new files to process count=%s files=%s", len(new_files), new_files)
        return new_files

    @task
    def parse_stage(file_path: dict[str, Any]) -> dict[str, Any]:
        logger.info("parsing master sheet file_path=%s", file_path["file_path"])
        parser = MasterSheetParser(file_path["file_path"])
        parsed = parser.parse()
        logger.info("parsed master sheet parsed=%s", parsed.model_dump())
        return {"parsed_payload": parsed.model_dump(), "upload_id": file_path["upload_id"]}

    @task
    def validate_stage(parsed: dict[str, Any]) -> dict[str, Any]:
        validator = ValidateOperator(parsed=parsed["parsed_payload"])
        results = validator.execute()
        logger.info("validation results results=%s", results)
        # need to work on stoping the pipeline if validation fails
        return {"validated_payload": parsed, "validation_results": results, "upload_id": parsed["upload_id"]}

    @task
    def transform_stage(validated_payload: dict[str, Any]) -> dict[str, Any]:
        
        transformer = TransformOperator(validated_payload["validated_payload"], validated_payload["upload_id"])
        transformed_payload = transformer.execute()
        return {"transformed_payload": transformed_payload}

    @task
    def load_stage(transformed_payload: dict[str, Any]) -> None:
        loader = LoadOperator(transformed_payload)
        result = loader.execute()
        logger.info("load_stage payload keys results=%s", result)

    # wait_for_files = FileArrivalSensor(
    #     task_id="wait_for_master_files",
    #     directory_path=str(settings.DATA_DIR),
    #     file_pattern="*.xlsm",
    #     poke_interval=30,
    #     timeout=60 * 10,
    #     mode="reschedule",
    # )

    extracted = extract_stage()
    parsed = parse_stage.expand(file_path=extracted)
    validated = validate_stage.expand(parsed=parsed)
    transformed = transform_stage.expand(validated_payload=validated)
    # wait_for_files >> extracted
    load_stage.expand(transformed_payload=transformed)


corporate_pipeline_dag = build_corporate_pipeline_dag()
