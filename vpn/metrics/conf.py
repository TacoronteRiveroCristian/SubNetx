"""Configuration for the metrics module."""

import logging
import os

# Working directory
pythonpath: str | None = os.getenv("PYTHONPATH")
if pythonpath is None:
    raise ValueError("PYTHONPATH is not set")
else:
    assert pythonpath, "PYTHONPATH cannot be empty"
    WORKING_DIR: str = pythonpath

# Level of logging
LOG_LEVEL: int = logging.INFO

# Path to the database
PING_DB_PATH: str = os.path.join(WORKING_DIR, "databases", "ping.db")

# Create the folder databases if it doesn't exist
os.makedirs(os.path.join(WORKING_DIR, "databases"), exist_ok=True)
