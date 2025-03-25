#!/usr/bin/env python3
"""
SubNetx VPN Ping Extractor and Storage Test.

This script tests the ping extraction and database storage functionality
by pinging both a valid domain (google.com) and an invalid domain,
then storing the results in the SQLite database.
"""

import json
import logging
from typing import List

from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
from vpn.metrics.collector.classes.extractor.ping_extractor import PingExtractor
from vpn.metrics.conf import LOG_LEVEL, PING_DB_PATH

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_ping_and_store(targets: List[str]) -> None:
    """
    Test ping extraction and database storage for a list of targets.

    :param targets: List of target hostnames or IPs to test
    :type targets: List[str]
    """
    # Initialize database connection
    db = PingDatabase(PING_DB_PATH)

    for target in targets:
        try:
            # Extract ping data
            logger.info(f"Testing ping for target: {target}")
            extractor = PingExtractor(target)
            ping_results = extractor.collect()

            # Log the results
            logger.info(f"Ping results for {target}:")
            logger.info(json.dumps(ping_results, indent=2))

            # Store in database
            logger.info(f"Storing results for {target} in database")
            metric_id = db.store_ping_result(ping_results)
            logger.info(f"Successfully stored results with ID: {metric_id}")

            # Verify storage by retrieving latest ping
            latest = db.get_latest_ping(target)
            logger.info(f"Retrieved latest ping for {target}:")
            logger.info(json.dumps(latest, indent=2))

        except Exception as e:
            logger.error(f"Error processing {target}: {str(e)}")
            logger.error(f"Error type: {e.__class__.__name__}")


def main() -> None:
    """Execute the main ping extraction and storage test."""
    # Test targets
    targets = ["google.com", "invalid.example.domain"]

    logger.info("Starting ping extraction and storage test")
    test_ping_and_store(targets)
    logger.info("Test completed")


if __name__ == "__main__":
    main()
