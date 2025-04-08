"""Configuration for the metrics module focused on host monitoring."""

import logging
import os
from typing import Optional

# Working directory
work_dir: Optional[str] = os.getenv("WORK_DIR")
if work_dir is None:
    work_dir = "/app/scripts/metrics"

WORK_DIR: str = work_dir

# Level of logging
LOG_LEVEL: int = logging.INFO
# Format of the log messages
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default ping settings
DEFAULT_PING_COUNT: int = 5
DEFAULT_PING_TIMEOUT: int = 2

# TLS Check enabled by default
CHECK_TLS: bool = True
DEFAULT_TLS_PORT: int = 443
