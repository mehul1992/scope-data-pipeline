from __future__ import annotations
from pathlib import Path
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.context import Context
import logging

logger = logging.getLogger(__name__)

class FileArrivalSensor(BaseSensorOperator):
    """Sensor stub to check whether .xlsm files have arrived in data/."""

    def __init__(self, directory_path: str, file_pattern: str = "*.xlsm", **kwargs: object) -> None:
        """Initialize sensor configuration for file arrival checks."""
        super().__init__(**kwargs)
        self.directory_path = directory_path
        self.file_pattern = file_pattern

    def poke(self, context: Context) -> bool:
        """Poke stub for file availability detection."""
        logger.info("checking for files in directory_path=%s file_pattern=%s", self.directory_path, self.file_pattern)
        path  = Path(self.directory_path)


        if not path.exists():
            return False
        
        files = list(path.glob(self.file_pattern))

        if files:
            logger.info(
                "files detected count=%s files=%s",
                count=len(files),
                files=[f.name for f in files]
            )
            return True

        logger.info("no files found, waiting pattern=%s", self.file_pattern)
        return False
