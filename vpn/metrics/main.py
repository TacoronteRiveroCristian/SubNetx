#!/usr/bin/env python3
"""
SubNetx VPN Network Monitoring System
Centralizes monitoring of various network metrics including ping, traffic,
bandwidth, connection time, and disconnection events.
"""

import logging
import time
import argparse
import sys
from typing import List, Dict, Any

# Import collectors (will add more as we create them)
from collector.ping import VPNPingMonitor
from collector.traffic import TrafficMonitor
from collector.bandwidth import BandwidthMonitor
from collector.connection import ConnectionMonitor

def setup_logger() -> logging.Logger:
    """
    Configure and return a centralized logger for the application.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('subnetx')
    logger.setLevel(logging.INFO)

    # Remove existing handlers if logger was already configured
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # Create console handler with formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger

class NetworkMonitor:
    """
    Main class that coordinates all network monitoring activities.
    """
    def __init__(self, target: str, interval: int = 60):
        """
        Initialize the network monitoring system.

        Args:
            target (str): Target IP/hostname to monitor
            interval (int): Monitoring interval in seconds
        """
        self.target = target
        self.interval = interval
        self.logger = logging.getLogger('subnetx')
        self.metrics: Dict[str, Any] = {}
        self.monitors = []

        # Initialize all monitors
        self.logger.info(f"Initializing network monitoring for {target}")
        self.init_monitors()

    def init_monitors(self):
        """Initialize all monitoring modules."""
        self.ping_monitor = VPNPingMonitor(self.target)
        self.monitors.append(self.ping_monitor)

        self.traffic_monitor = TrafficMonitor(self.target)
        self.monitors.append(self.traffic_monitor)

        self.bandwidth_monitor = BandwidthMonitor(self.target)
        self.monitors.append(self.bandwidth_monitor)

        self.connection_monitor = ConnectionMonitor(self.target)
        self.monitors.append(self.connection_monitor)

        self.logger.info(f"Initialized {len(self.monitors)} monitoring modules")

    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from all monitoring modules.

        Returns:
            Dict[str, Any]: Combined metrics from all monitors
        """
        metrics = {
            'timestamp': time.time(),
            'target': self.target
        }

        # Collect metrics from each monitor
        for monitor in self.monitors:
            monitor_name = monitor.__class__.__name__
            self.logger.info(f"Collecting metrics from {monitor_name}")
            monitor_metrics = monitor.collect()
            metrics[monitor_name] = monitor_metrics

        return metrics

    def run(self, duration: int = None):
        """
        Run the monitoring system for a specified duration.

        Args:
            duration (int, optional): Duration in seconds to run monitoring.
                                     If None, runs indefinitely.
        """
        self.logger.info(f"Starting network monitoring for {self.target}")
        start_time = time.time()

        try:
            while True:
                # Check if we've reached the duration limit
                if duration and (time.time() - start_time) > duration:
                    self.logger.info(f"Reached monitoring duration of {duration}s")
                    break

                # Collect and process metrics
                self.metrics = self.collect_metrics()
                self.logger.info(f"Collected metrics: {self.metrics}")

                # Save metrics to persistent storage
                self.save_metrics(self.metrics)

                # Wait for next collection interval
                time.sleep(self.interval)

        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Error in monitoring: {e}")

    def save_metrics(self, metrics: Dict[str, Any]):
        """
        Save metrics to persistent storage.

        Args:
            metrics (Dict[str, Any]): Metrics to save
        """
        # For now, we'll just print them, but in a real implementation
        # you might write to a database, file, etc.
        self.logger.info(f"METRICS: {metrics}")

def main():
    """Main entry point for the network monitoring system."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='SubNetx Network Monitoring System')
    parser.add_argument('--target', '-t', default='google.com',
                        help='Target host/IP to monitor (default: google.com)')
    parser.add_argument('--interval', '-i', type=int, default=60,
                        help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('--duration', '-d', type=int,
                        help='Duration to run monitoring in seconds (default: indefinitely)')

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger()

    # Log startup information
    logger.info(f"Starting SubNetx Network Monitoring")
    logger.info(f"Target: {args.target}")
    logger.info(f"Interval: {args.interval}s")
    if args.duration:
        logger.info(f"Duration: {args.duration}s")
    else:
        logger.info("Duration: indefinite (press Ctrl+C to stop)")

    # Initialize and run the network monitor
    monitor = NetworkMonitor(args.target, args.interval)
    monitor.run(args.duration)

    logger.info("Network monitoring completed")

if __name__ == "__main__":
    main()
