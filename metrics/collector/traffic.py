#!/usr/bin/env python3
"""
SubNetx VPN Traffic Monitor
This script monitors traffic statistics for VPN clients using OpenVPN status file.
"""

import json
import time
from datetime import datetime
import logging
from typing import Dict, List, Optional
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/subnetx/traffic_monitor.log'),
        logging.StreamHandler()
    ]
)

class VPNTrafficMonitor:
    def __init__(self):
        """Initialize the VPN Traffic Monitor."""
        self.clients: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)

    def parse_bytes(self, bytes_str: str) -> int:
        """
        Parse bytes string to integer.

        Args:
            bytes_str (str): Bytes string to parse

        Returns:
            int: Parsed bytes value
        """
        try:
            return int(bytes_str)
        except ValueError:
            return 0

    def get_client_traffic(self) -> Dict[str, Dict]:
        """
        Get traffic statistics for all clients from OpenVPN status file.

        Returns:
            Dict[str, Dict]: Dictionary of client traffic statistics
        """
        try:
            with open('/var/log/openvpn/status.log', 'r') as f:
                status_data = f.read()

            # Regular expressions for parsing
            client_pattern = r'CLIENT_LIST,([^,]+),([^,]+),([^,]+),([^,]+),([^,]+)'
            bytes_pattern = r'bytes_received=(\d+),bytes_sent=(\d+)'

            # Find all client entries
            clients = {}
            for match in re.finditer(client_pattern, status_data):
                name, ip, real_ip, last_seen, bytes_received, bytes_sent = match.groups()

                # Parse bytes
                bytes_recv = self.parse_bytes(bytes_received)
                bytes_sent = self.parse_bytes(bytes_sent)

                # Calculate total traffic
                total_traffic = bytes_recv + bytes_sent

                clients[ip] = {
                    'name': name,
                    'ip': ip,
                    'real_ip': real_ip,
                    'last_seen': last_seen,
                    'bytes_received': bytes_recv,
                    'bytes_sent': bytes_sent,
                    'total_traffic': total_traffic,
                    'timestamp': datetime.now().isoformat()
                }

            return clients

        except Exception as e:
            self.logger.error(f"Error reading traffic stats: {e}")
            return {}

    def update_traffic_stats(self):
        """Update traffic statistics for all clients."""
        new_stats = self.get_client_traffic()

        # Update existing clients and add new ones
        for ip, stats in new_stats.items():
            if ip in self.clients:
                # Calculate traffic delta
                old_stats = self.clients[ip]
                stats['bytes_received_delta'] = stats['bytes_received'] - old_stats['bytes_received']
                stats['bytes_sent_delta'] = stats['bytes_sent'] - old_stats['bytes_sent']
                stats['total_traffic_delta'] = stats['total_traffic'] - old_stats['total_traffic']

            self.clients[ip] = stats
            self.logger.info(f"Updated traffic stats for {ip}: {stats}")

    def save_stats(self, filepath: str = '/var/log/subnetx/traffic_stats.json'):
        """
        Save traffic statistics to JSON file.

        Args:
            filepath (str): Path to save statistics
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.clients, f, indent=2)
            self.logger.info(f"Saved traffic stats to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving traffic stats: {e}")

def main():
    """Main function to run the traffic monitor."""
    monitor = VPNTrafficMonitor()

    while True:
        try:
            monitor.update_traffic_stats()
            monitor.save_stats()
            time.sleep(60)  # Update every minute
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
