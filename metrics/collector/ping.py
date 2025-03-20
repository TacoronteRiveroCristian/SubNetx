#!/usr/bin/env python3
"""
SubNetx VPN Client Ping Monitor
This script monitors the status and latency of VPN clients by performing ping tests.
"""

import subprocess
import json
import time
from datetime import datetime
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/subnetx/ping_monitor.log'),
        logging.StreamHandler()
    ]
)

class VPNPingMonitor:
    def __init__(self, vpn_network: str = "10.8.0.0/24"):
        """
        Initialize the VPN Ping Monitor.

        Args:
            vpn_network (str): VPN network CIDR notation
        """
        self.vpn_network = vpn_network
        self.clients: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)

    def get_active_clients(self) -> List[str]:
        """
        Get list of active VPN clients from OpenVPN status file.

        Returns:
            List[str]: List of client IP addresses
        """
        try:
            with open('/var/log/openvpn/status.log', 'r') as f:
                status_data = f.read()

            # Parse status file to get client IPs
            clients = []
            for line in status_data.split('\n'):
                if 'CLIENT_LIST' in line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        clients.append(parts[1])  # IP address is second field

            return clients
        except Exception as e:
            self.logger.error(f"Error reading status file: {e}")
            return []

    def ping_client(self, ip: str) -> Optional[Dict]:
        """
        Perform ping test on a client IP.

        Args:
            ip (str): Client IP address

        Returns:
            Optional[Dict]: Ping results or None if failed
        """
        try:
            # Perform ping test with 4 packets
            result = subprocess.run(
                ['ping', '-c', '4', ip],
                capture_output=True,
                text=True
            )

            # Parse ping output
            if result.returncode == 0:
                # Extract statistics
                stats = {}
                for line in result.stdout.split('\n'):
                    if 'min/avg/max' in line:
                        stats['latency'] = line.split('=')[1].strip()
                    elif 'transmitted' in line:
                        stats['packets'] = line.split(',')[0].strip()

                return {
                    'ip': ip,
                    'status': 'online',
                    'timestamp': datetime.now().isoformat(),
                    'stats': stats
                }
            else:
                return {
                    'ip': ip,
                    'status': 'offline',
                    'timestamp': datetime.now().isoformat(),
                    'stats': None
                }

        except Exception as e:
            self.logger.error(f"Error pinging {ip}: {e}")
            return None

    def update_client_stats(self):
        """Update statistics for all active clients."""
        clients = self.get_active_clients()

        for ip in clients:
            stats = self.ping_client(ip)
            if stats:
                self.clients[ip] = stats
                self.logger.info(f"Updated stats for {ip}: {stats}")

    def save_stats(self, filepath: str = '/var/log/subnetx/client_stats.json'):
        """
        Save client statistics to JSON file.

        Args:
            filepath (str): Path to save statistics
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.clients, f, indent=2)
            self.logger.info(f"Saved stats to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving stats: {e}")

def main():
    """Main function to run the ping monitor."""
    monitor = VPNPingMonitor()

    while True:
        try:
            monitor.update_client_stats()
            monitor.save_stats()
            time.sleep(60)  # Update every minute
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
