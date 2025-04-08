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

# PostgreSQL database configuration
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "subnetx")
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "subnetx_user")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "subnetx_password")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_URI: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Path to the SQLite database (legacy support)
PING_DB_PATH: str = os.path.join(WORK_DIR, "databases", "ping.db")

# Create the folder databases if it doesn't exist
os.makedirs(os.path.join(WORK_DIR, "databases"), exist_ok=True)
