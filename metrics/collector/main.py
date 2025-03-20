#!/usr/bin/env python3
"""
SubNetx VPN Monitoring System
Main script that orchestrates all monitoring components:
- Ping monitoring
- Traffic monitoring
- Status monitoring
"""

import os
import sys
import time
import logging
import signal
from typing import List, Dict
from ping import VPNPingMonitor
from traffic import VPNTrafficMonitor
from status import VPNStatusMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/subnetx/monitor.log'),
        logging.StreamHandler()
    ]
)

class VPNMonitorSystem:
    def __init__(self):
        """Initialize the VPN monitoring system."""
        self.logger = logging.getLogger(__name__)
        self.monitors: List[object] = []
        self.running = True

        # Initialize monitors
        self.ping_monitor = VPNPingMonitor()
        self.traffic_monitor = VPNTrafficMonitor()
        self.status_monitor = VPNStatusMonitor()

        self.monitors.extend([
            self.ping_monitor,
            self.traffic_monitor,
            self.status_monitor
        ])

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def ensure_log_directories(self):
        """Ensure all required log directories exist."""
        log_dirs = [
            '/var/log/subnetx',
            '/var/log/openvpn'
        ]

        for directory in log_dirs:
            try:
                os.makedirs(directory, exist_ok=True)
                self.logger.info(f"Ensured log directory exists: {directory}")
            except Exception as e:
                self.logger.error(f"Error creating log directory {directory}: {e}")
                sys.exit(1)

    def run(self):
        """Run the monitoring system."""
        self.logger.info("Starting SubNetx VPN monitoring system...")
        self.ensure_log_directories()

        while self.running:
            try:
                # Update all monitors
                for monitor in self.monitors:
                    if hasattr(monitor, 'update_status'):
                        monitor.update_status()
                    elif hasattr(monitor, 'update_traffic_stats'):
                        monitor.update_traffic_stats()
                    elif hasattr(monitor, 'update_client_stats'):
                        monitor.update_client_stats()

                # Save all stats
                for monitor in self.monitors:
                    if hasattr(monitor, 'save_stats'):
                        monitor.save_stats()

                # Sleep for a minute before next update
                time.sleep(60)

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying

        self.logger.info("Shutting down SubNetx VPN monitoring system...")

def main():
    """Main function to run the monitoring system."""
    monitor_system = VPNMonitorSystem()
    monitor_system.run()

if __name__ == "__main__":
    main()
