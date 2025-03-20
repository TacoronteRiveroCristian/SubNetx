#!/usr/bin/env python3
"""
SubNetx VPN Traffic Monitor
This script monitors network traffic to/from specified hosts or interfaces.
"""

import subprocess
import re
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class TrafficMonitor:
    def __init__(self, target: str):
        """
        Initialize the Traffic Monitor.

        Args:
            target (str): Target hostname or IP address to monitor
        """
        self.target = target
        self.logger = logging.getLogger('subnetx')  # Initialize logger first
        self.interface = self._detect_interface()
        self.previous_stats = {}
        self.current_stats = {}
        self.traffic_history = []
        self.logger.info(f"Initialized Traffic Monitor for {target} on interface {self.interface}")

    def _detect_interface(self) -> str:
        """
        Detect the network interface used to reach the target.

        Returns:
            str: Name of the network interface
        """
        try:
            # Use ip route to determine which interface is used to reach the target
            result = subprocess.run(
                ['ip', 'route', 'get', self.target],
                capture_output=True,
                text=True
            )

            # Parse the output to extract the interface name
            match = re.search(r'dev\s+(\w+)', result.stdout)
            if match:
                return match.group(1)

            # Fallback to default interface
            self.logger.warning(f"Could not detect interface for {self.target}, using default")
            return self._get_default_interface()
        except Exception as e:
            self.logger.error(f"Error detecting interface: {e}")
            return self._get_default_interface()

    def _get_default_interface(self) -> str:
        """
        Get the default network interface.

        Returns:
            str: Name of the default network interface
        """
        try:
            # Try to get the default route interface
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                text=True
            )

            # Parse the output to extract the interface name
            match = re.search(r'dev\s+(\w+)', result.stdout)
            if match:
                return match.group(1)

            # Fallback to tun0 for VPN or eth0 as a last resort
            interfaces = self._list_interfaces()
            if 'tun0' in interfaces:
                return 'tun0'
            elif interfaces:
                return interfaces[0]
            else:
                return 'eth0'
        except Exception as e:
            self.logger.error(f"Error getting default interface: {e}")
            return 'eth0'  # Default fallback

    def _list_interfaces(self) -> List[str]:
        """
        List all network interfaces on the system.

        Returns:
            List[str]: List of interface names
        """
        try:
            # Use ip link to list interfaces
            result = subprocess.run(
                ['ip', '-o', 'link', 'show'],
                capture_output=True,
                text=True
            )

            # Parse the output to extract interface names
            interfaces = []
            for line in result.stdout.splitlines():
                match = re.search(r'^\d+:\s+(\w+):', line)
                if match and match.group(1) != 'lo':  # Skip loopback
                    interfaces.append(match.group(1))

            return interfaces
        except Exception as e:
            self.logger.error(f"Error listing interfaces: {e}")
            return []

    def _get_interface_stats(self, interface: str) -> Dict[str, int]:
        """
        Get current traffic statistics for a network interface.

        Args:
            interface (str): Network interface name

        Returns:
            Dict[str, int]: Dictionary with rx_bytes, tx_bytes, rx_packets, tx_packets
        """
        try:
            stats = {}

            # Read statistics from /proc/net/dev
            with open('/proc/net/dev', 'r') as f:
                for line in f:
                    if interface in line:
                        # Split the line and extract the statistics
                        # Format: Interface: rx_bytes rx_packets ... tx_bytes tx_packets ...
                        fields = line.split(':')[1].strip().split()
                        stats['rx_bytes'] = int(fields[0])
                        stats['rx_packets'] = int(fields[1])
                        stats['tx_bytes'] = int(fields[8])
                        stats['tx_packets'] = int(fields[9])
                        break

            if not stats:
                self.logger.warning(f"No stats found for interface {interface}")
                # Return zeros as fallback
                stats = {
                    'rx_bytes': 0,
                    'rx_packets': 0,
                    'tx_bytes': 0,
                    'tx_packets': 0
                }

            return stats
        except Exception as e:
            self.logger.error(f"Error getting interface stats: {e}")
            return {
                'rx_bytes': 0,
                'rx_packets': 0,
                'tx_bytes': 0,
                'tx_packets': 0
            }

    def _calculate_rates(self, current: Dict[str, int], previous: Dict[str, int],
                        interval: float) -> Dict[str, float]:
        """
        Calculate traffic rates based on current and previous stats.

        Args:
            current (Dict[str, int]): Current traffic statistics
            previous (Dict[str, int]): Previous traffic statistics
            interval (float): Time interval in seconds

        Returns:
            Dict[str, float]: Dictionary with calculated rates
        """
        rates = {}

        if not previous or interval <= 0:
            # No previous stats or invalid interval, can't calculate rates
            return {
                'rx_bytes_rate': 0,
                'tx_bytes_rate': 0,
                'rx_packets_rate': 0,
                'tx_packets_rate': 0
            }

        # Calculate rates (bytes/sec, packets/sec)
        for key in ['rx_bytes', 'tx_bytes', 'rx_packets', 'tx_packets']:
            if key in current and key in previous:
                # Handle counter reset (e.g., after reboot)
                if current[key] < previous[key]:
                    rates[f'{key}_rate'] = current[key] / interval
                else:
                    rates[f'{key}_rate'] = (current[key] - previous[key]) / interval
            else:
                rates[f'{key}_rate'] = 0

        return rates

    def _format_bytes(self, bytes_value: float) -> str:
        """
        Format bytes to human-readable format (KB, MB, GB).

        Args:
            bytes_value (float): Bytes value to format

        Returns:
            str: Formatted string with units
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0

        while bytes_value >= 1024 and unit_index < len(units) - 1:
            bytes_value /= 1024
            unit_index += 1

        return f"{bytes_value:.2f} {units[unit_index]}"

    def _get_target_traffic(self) -> Dict[str, Any]:
        """
        Get traffic statistics specifically for the target IP.
        Uses iptables or tcpdump depending on availability.

        Returns:
            Dict[str, Any]: Traffic statistics for the target
        """
        try:
            # First try with 'ss' command to get current connections
            result = subprocess.run(
                ['ss', '-t', '-n', 'dst', self.target],
                capture_output=True,
                text=True,
                timeout=5
            )

            connections = 0
            for line in result.stdout.splitlines()[1:]:  # Skip header
                connections += 1

            return {
                'active_connections': connections,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting target traffic: {e}")
            return {
                'active_connections': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

    def collect(self) -> Dict[str, Any]:
        """
        Collect traffic metrics for the monitored interface.

        Returns:
            Dict[str, Any]: Dictionary with traffic metrics
        """
        # Store previous stats if we have them
        if self.current_stats:
            self.previous_stats = self.current_stats

        # Get current interface stats
        timestamp = datetime.now()
        self.current_stats = self._get_interface_stats(self.interface)
        self.current_stats['timestamp'] = timestamp.timestamp()

        # Calculate rates if we have previous stats
        rates = {}
        if self.previous_stats:
            interval = self.current_stats['timestamp'] - self.previous_stats['timestamp']
            rates = self._calculate_rates(self.current_stats, self.previous_stats, interval)

        # Get target-specific traffic if possible
        target_traffic = self._get_target_traffic()

        # Build the result
        result = {
            'interface': self.interface,
            'timestamp': timestamp.isoformat(),
            'stats': {
                'rx_bytes': self.current_stats.get('rx_bytes', 0),
                'tx_bytes': self.current_stats.get('tx_bytes', 0),
                'rx_packets': self.current_stats.get('rx_packets', 0),
                'tx_packets': self.current_stats.get('tx_packets', 0),
            },
            'rates': {
                'rx_bytes_rate': rates.get('rx_bytes_rate', 0),
                'tx_bytes_rate': rates.get('tx_bytes_rate', 0),
                'rx_packets_rate': rates.get('rx_packets_rate', 0),
                'tx_packets_rate': rates.get('tx_packets_rate', 0),
            },
            'human_readable': {
                'rx_rate': self._format_bytes(rates.get('rx_bytes_rate', 0)),
                'tx_rate': self._format_bytes(rates.get('tx_bytes_rate', 0)),
                'total_rx': self._format_bytes(self.current_stats.get('rx_bytes', 0)),
                'total_tx': self._format_bytes(self.current_stats.get('tx_bytes', 0)),
            },
            'target_traffic': target_traffic
        }

        # Add to history (keep last 100 entries)
        self.traffic_history.append({
            'timestamp': timestamp.isoformat(),
            'rx_bytes': self.current_stats.get('rx_bytes', 0),
            'tx_bytes': self.current_stats.get('tx_bytes', 0),
            'rx_rate': rates.get('rx_bytes_rate', 0),
            'tx_rate': rates.get('tx_bytes_rate', 0),
        })

        if len(self.traffic_history) > 100:
            self.traffic_history.pop(0)

        result['history'] = self.traffic_history[-10:]  # Return only the last 10 entries

        self.logger.info(f"Traffic stats - RX: {result['human_readable']['rx_rate']}/s, TX: {result['human_readable']['tx_rate']}/s")

        return result

# Standalone testing when script is run directly
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger('subnetx')

    # Test the traffic monitor
    target = "google.com"
    monitor = TrafficMonitor(target)

    print(f"Monitoring traffic for {target}")
    print("Initial reading (no rates yet):")
    results = monitor.collect()
    print(json.dumps(results, indent=2))

    print("\nWaiting 5 seconds for second reading...")
    time.sleep(5)

    results = monitor.collect()
    print("\nSecond reading (with rates):")
    print(json.dumps(results, indent=2))
