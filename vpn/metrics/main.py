"""This script is used to collect metrics from the SubNetx VPN server."""

import logging
import os
import subprocess
import sys

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore

from vpn.metrics.conf import LOG_FORMAT, LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    stream=sys.stdout,
)
logger = logging.getLogger(__file__)


def run_ping_check() -> None:
    """Run the ping check script."""
    try:
        script_path = os.path.join("vpn/metrics/collector/src/extract_and_save_ping.py")
        result = subprocess.run(
            [script_path], capture_output=True, text=True, check=True
        )

        if result.returncode == 0:
            logger.info("Ping check completed successfully")
            logger.info(result.stdout)
        else:
            logger.error(f"Ping check failed with error: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running ping check: {str(e)}")


def main() -> None:
    """Set up the scheduler for metrics collection."""
    logger.info("Starting SubNetx metrics collection service")

    # Create scheduler
    scheduler = BackgroundScheduler()

    # Add ping check job - run every minute
    scheduler.add_job(
        run_ping_check,
        trigger=IntervalTrigger(minutes=1),
        id="ping_check",
        name="Run ping check every minute",
        replace_existing=True,
    )

    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started")

    try:
        # Keep the main thread alive
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
