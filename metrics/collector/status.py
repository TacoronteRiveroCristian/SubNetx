#!/usr/bin/env python3
"""
SubNetx VPN Status Monitor
This script monitors connection status and events for VPN clients.
"""

import json
import time
from datetime import datetime
import logging
from typing import Dict, List, Optional
import re
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/subnetx/status_monitor.log'),
        logging.StreamHandler()
    ]
)

class VPNStatusMonitor:
    def __init__(self):
        """Initialize the VPN Status Monitor."""
        self.clients: Dict[str, Dict] = {}
        self.events: List[Dict] = []
        self.logger = logging.getLogger(__name__)
        self.last_position = 0

    def parse_timestamp(self, timestamp: str) -> str:
        """
        Parse OpenVPN timestamp to ISO format.

        Args:
            timestamp (str): OpenVPN timestamp

        Returns:
            str: ISO formatted timestamp
        """
        try:
            # OpenVPN timestamp format: "Wed Mar 20 10:30:45 2024"
            dt = datetime.strptime(timestamp, "%a %b %d %H:%M:%S %Y")
            return dt.isoformat()
        except ValueError:
            return datetime.now().isoformat()

    def get_client_status(self) -> Dict[str, Dict]:
        """
        Get connection status for all clients from OpenVPN status file.

        Returns:
            Dict[str, Dict]: Dictionary of client status information
        """
        try:
            with open('/var/log/openvpn/status.log', 'r') as f:
                status_data = f.read()

            # Regular expressions for parsing
            client_pattern = r'CLIENT_LIST,([^,]+),([^,]+),([^,]+),([^,]+)'

            # Find all client entries
            clients = {}
            for match in re.finditer(client_pattern, status_data):
                name, ip, real_ip, last_seen = match.groups()

                clients[ip] = {
                    'name': name,
                    'ip': ip,
                    'real_ip': real_ip,
                    'last_seen': self.parse_timestamp(last_seen),
                    'status': 'connected',
                    'timestamp': datetime.now().isoformat()
                }

            return clients

        except Exception as e:
            self.logger.error(f"Error reading status file: {e}")
            return {}

    def monitor_events(self):
        """
        Monitor OpenVPN log file for connection events.
        """
        try:
            log_file = '/var/log/openvpn/openvpn.log'

            # Check if file exists
            if not os.path.exists(log_file):
                self.logger.warning(f"Log file not found: {log_file}")
                return

            # Get current file size
            current_size = os.path.getsize(log_file)

            # If file size is less than last position, file was rotated
            if current_size < self.last_position:
                self.last_position = 0

            # Read new lines
            with open(log_file, 'r') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()

            # Update last position
            self.last_position = current_size

            # Process new lines
            for line in new_lines:
                if 'CLIENT' in line:
                    event = self.parse_event(line)
                    if event:
                        self.events.append(event)
                        self.logger.info(f"New event: {event}")

            # Keep only last 1000 events
            if len(self.events) > 1000:
                self.events = self.events[-1000:]

        except Exception as e:
            self.logger.error(f"Error monitoring events: {e}")

    def parse_event(self, line: str) -> Optional[Dict]:
        """
        Parse a log line into an event dictionary.

        Args:
            line (str): Log line to parse

        Returns:
            Optional[Dict]: Parsed event or None if not relevant
        """
        try:
            # Extract timestamp and message
            timestamp_match = re.match(r'(\w+ \w+ \d+ \d+:\d+:\d+ \d+)', line)
            if not timestamp_match:
                return None

            timestamp = self.parse_timestamp(timestamp_match.group(1))
            message = line[timestamp_match.end():].strip()

            # Determine event type
            event_type = 'unknown'
            if 'CONNECTED' in message:
                event_type = 'connected'
            elif 'DISCONNECTED' in message:
                event_type = 'disconnected'

            # Extract client name if present
            client_match = re.search(r'CLIENT:([^,]+)', message)
            client_name = client_match.group(1) if client_match else None

            return {
                'timestamp': timestamp,
                'type': event_type,
                'client': client_name,
                'message': message
            }

        except Exception as e:
            self.logger.error(f"Error parsing event: {e}")
            return None

    def update_status(self):
        """Update status and events for all clients."""
        new_status = self.get_client_status()

        # Update existing clients and add new ones
        for ip, status in new_status.items():
            if ip in self.clients:
                # Check for status changes
                old_status = self.clients[ip]
                if old_status['status'] != status['status']:
                    self.events.append({
                        'timestamp': datetime.now().isoformat(),
                        'type': 'status_change',
                        'client': status['name'],
                        'old_status': old_status['status'],
                        'new_status': status['status']
                    })

            self.clients[ip] = status
            self.logger.info(f"Updated status for {ip}: {status}")

    def save_stats(self, filepath: str = '/var/log/subnetx/status_stats.json'):
        """
        Save status and events to JSON file.

        Args:
            filepath (str): Path to save statistics
        """
        try:
            stats = {
                'clients': self.clients,
                'events': self.events,
                'timestamp': datetime.now().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2)
            self.logger.info(f"Saved status stats to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving status stats: {e}")

def main():
    """Main function to run the status monitor."""
    monitor = VPNStatusMonitor()

    while True:
        try:
            monitor.update_status()
            monitor.monitor_events()
            monitor.save_stats()
            time.sleep(60)  # Update every minute
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
