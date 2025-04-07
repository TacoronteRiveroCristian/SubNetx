#!/usr/bin/env python3
"""
SubNetx VPN Ping Extractor and Storage.

Este script monitoriza los clientes VPN configurados usando un pool de workers
para manejar múltiples clientes eficientemente.
"""

import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any

from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
from vpn.metrics.collector.classes.extractor.ping_extractor import PingExtractor
from vpn.metrics.conf import LOG_LEVEL, PING_DB_PATH, WORK_DIR

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Path to the VPN clients configuration file
VPN_CLIENTS_FILE = os.path.join(WORK_DIR, "collector", "config", "vpn_clients.json")

def load_vpn_clients() -> List[Dict[str, str]]:
    """
    Load VPN clients from the configuration file.

    Returns:
        List[Dict[str, str]]: List of client configurations
    """
    try:
        if not os.path.exists(VPN_CLIENTS_FILE):
            logger.warning(f"VPN clients file not found at {VPN_CLIENTS_FILE}")
            return []

        with open(VPN_CLIENTS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('clients', [])
    except Exception as e:
        logger.error(f"Error loading VPN clients: {str(e)}")
        return []

def process_target(target: Dict[str, str]) -> None:
    """
    Process a single target and store its metrics.

    Args:
        target (Dict[str, str]): Target configuration with name and IP
    """
    try:
        # Extract ping data
        logger.info(f"Testing ping for target: {target['name']} ({target['ip']})")
        extractor = PingExtractor(target['ip'])
        ping_results = extractor.collect()

        # Initialize database connection
        db = PingDatabase(PING_DB_PATH)

        # Store in database
        metric_id = db.store_ping_result(ping_results)
        logger.info(f"Successfully stored results for {target['name']} with ID: {metric_id}")

    except Exception as e:
        logger.error(f"Error processing {target['name']}: {str(e)}")

def main() -> None:
    """Execute the main ping extraction and storage process."""
    logger.info("Starting VPN clients monitoring")

    # Load VPN clients
    clients = load_vpn_clients()
    if not clients:
        logger.warning("No VPN clients found to monitor")
        return

    # Create a thread pool
    max_workers = min(len(clients), 10)  # Limitar a 10 workers máximo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks for each client
        future_to_client = {
            executor.submit(process_target, client): client
            for client in clients
        }

        # Process completed tasks
        for future in as_completed(future_to_client):
            client = future_to_client[future]
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error monitoring client {client['name']}: {str(e)}")

    logger.info("VPN clients monitoring completed")

if __name__ == "__main__":
    main()
