from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pendulum
from airflow.sdk import dag, task

logger = logging.getLogger(__name__)

@dag(
    dag_id="corporate_pipeline_dag",
    schedule="* * * * *", # every 1 minute schedule
    start_date=pendulum.datetime(2025, 4, 23, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["corporate", "etl"],
)
def build_corporate_pipeline_dag() -> None:

    @task
    def extract_stage() -> list[str]:
        from app.core.config import settings
        from app.airflow.operators.extract_operator import ExtractOperator
        input_directory = str(settings.DATA_DIR)
        extractor = ExtractOperator(input_directory=input_directory)
        new_files = extractor.execute()
        return new_files

    @task
    def parse_stage(file_path: dict[str, Any]) -> dict[str, Any]:
        from app.etl.parsers.master_sheet_parser import MasterSheetParser
        logger.info("parsing master sheet file_path=%s", file_path["file_path"])
        parser = MasterSheetParser(file_path["file_path"])
        parsed = parser.parse()
        logger.info("parsed master sheet parsed=%s", parsed.model_dump())
        return {"parsed_payload": parsed.model_dump(), "upload_id": file_path["upload_id"]}

    @task
    def validate_stage(parsed: dict[str, Any]) -> dict[str, Any]:
        from app.airflow.operators.validate_operator import ValidateOperator
        validator = ValidateOperator(parsed=parsed["parsed_payload"])
        results = validator.execute()
        logger.info("validation results results=%s", results)
        # need to work on stoping the pipeline if validation fails
        return {"validated_payload": parsed, "validation_results": results, "upload_id": parsed["upload_id"]}

    @task
    def transform_stage(validated_payload: dict[str, Any]) -> dict[str, Any]:
        from app.airflow.operators.transform_operator import TransformOperator
        transformer = TransformOperator(validated_payload["validated_payload"], validated_payload["upload_id"])
        transformed_payload = transformer.execute()
        return {"transformed_payload": transformed_payload}

    @task
    def load_stage(transformed_payload: dict[str, Any]) -> None:
        from app.airflow.operators.load_operator import LoadOperator
        loader = LoadOperator(transformed_payload)
        result = loader.execute()
        logger.info("load_stage payload keys results=%s", result)

    extracted = extract_stage()
    parsed = parse_stage.expand(file_path=extracted)
    validated = validate_stage.expand(parsed=parsed)
    transformed = transform_stage.expand(validated_payload=validated)
    load_stage.expand(transformed_payload=transformed)


corporate_pipeline_dag = build_corporate_pipeline_dag()
