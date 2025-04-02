#!/usr/bin/env python3
"""
SubNetx VPN Ping Extractor and Storage Test.

Este script prueba la funcionalidad de extracción de ping y almacenamiento en la base de datos
haciendo ping tanto a un dominio válido (google.com) como a un dominio no válido,
y luego almacenando los resultados en la base de datos SQLite.
"""

import json
import logging
import sys
from typing import Dict, List, Any

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

            # Validate RTT data
            primary_target = ping_results.get("primary_target", {})
            rtt_stats = primary_target.get("rtt_stats", {})
            logger.info("Validating RTT statistics:")
            logger.info(f"  min_rtt: {rtt_stats.get('min_ms', 'N/A')}")
            logger.info(f"  avg_rtt: {rtt_stats.get('avg_ms', 'N/A')}")
            logger.info(f"  max_rtt: {rtt_stats.get('max_ms', 'N/A')}")
            logger.info(f"  mdev_rtt: {rtt_stats.get('mdev_ms', 'N/A')}")

            # Validate packet data
            packets = primary_target.get("packets", {})
            logger.info("Validating packet statistics:")
            logger.info(f"  transmitted: {packets.get('transmitted', 'N/A')}")
            logger.info(f"  received: {packets.get('received', 'N/A')}")
            logger.info(f"  packet_loss: {primary_target.get('packet_loss_percent', 'N/A')}%")

            # Validate TLS info
            tls_info = primary_target.get("tls_info", {})
            logger.info("Validating TLS information:")
            logger.info(f"  expiry: {tls_info.get('expiry', 'N/A')}")
            logger.info(f"  issuer: {tls_info.get('issuer', 'N/A')}")
            logger.info(f"  subject: {tls_info.get('subject', 'N/A')}")
            logger.info(f"  version: {tls_info.get('version', 'N/A')}")
            logger.info(f"  cipher: {tls_info.get('cipher', 'N/A')}")

            # Log the complete results as JSON
            logger.info(f"Complete ping results for {target}:")
            logger.info(json.dumps(ping_results, indent=2))

            # Store in database
            logger.info(f"Storing results for {target} in database")
            metric_id = db.store_ping_result(ping_results)
            logger.info(f"Successfully stored results with ID: {metric_id}")

            # Verify storage by retrieving latest ping
            latest = db.get_latest_ping(target)
            logger.info(f"Retrieved latest ping for {target}:")
            logger.info(json.dumps(latest, indent=2))

            # Validate database retrieval
            validate_database_data(latest)

        except Exception as e:
            logger.error(f"Error processing {target}: {str(e)}")
            logger.error(f"Error type: {e.__class__.__name__}")


def validate_database_data(data: Dict[str, Any]) -> None:
    """
    Validate that all required fields are present in the database result.

    :param data: Database data to validate
    :type data: Dict[str, Any]
    """
    logger.info("Validating database retrieval:")

    # Check RTT data
    logger.info("  RTT data present: %s", all(
        k in data for k in ['min_rtt', 'avg_rtt', 'max_rtt', 'mdev_rtt']
    ))

    # Check packet data
    logger.info("  Packet data present: %s", all(
        k in data for k in ['packets_transmitted', 'packets_received', 'packet_loss_percent']
    ))

    # Check TLS data if present
    if 'tls_info' in data and data['tls_info']:
        logger.info("  TLS data present: %s", all(
            k in data['tls_info'] for k in ['cert_expiry', 'issuer', 'subject', 'version', 'cipher']
        ))
    else:
        logger.info("  TLS data not available in database result")


def main() -> None:
    """Execute the main ping extraction and storage test."""
    # Test targets - use command line arguments if provided, otherwise default to google.com
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["google.com", "invalid.example.domain"]

    logger.info("Starting ping extraction and storage test")
    test_ping_and_store(targets)
    logger.info("Test completed")


if __name__ == "__main__":
    main()
