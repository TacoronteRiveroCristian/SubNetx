"""Configuration for the metrics module."""

import logging
import os
from typing import Optional

# Working directory
work_dir: Optional[str] = os.getenv("WORK_DIR")
if work_dir is None:
    raise ValueError("WORK_DIR is not set")

WORK_DIR: str = work_dir

# Level of logging
LOG_LEVEL: int = logging.INFO
# Format of the log messages
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Path to the database
PING_DB_PATH: str = os.path.join(WORK_DIR, "databases", "ping.db")

# Create the folder databases if it doesn't exist
os.makedirs(os.path.join(WORK_DIR, "databases"), exist_ok=True)
