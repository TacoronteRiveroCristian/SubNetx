#!/usr/bin/env python3
"""
SubNetx VPN Traffic Monitor

This module provides functionality to monitor network traffic statistics
for VPN connections, focusing on throughput, packet counts, and traffic
patterns on specific interfaces or to/from target hosts.

JSON Response Format:
{
    "timestamp": "ISO-8601 timestamp of the measurement",
    "target": "Target hostname or IP being monitored",
    "traffic": {
        "interface": "Network interface name (e.g., 'tun0', 'eth0')",
        "timestamp": "ISO-8601 timestamp of the traffic measurement",
        "bytes": {
            "received": "Total bytes received",
            "sent": "Total bytes sent",
            "received_rate": "Bytes received per second",
            "sent_rate": "Bytes sent per second",
            "received_human": "Human-readable received bytes (e.g., '1.5 MB')",
            "sent_human": "Human-readable sent bytes (e.g., '2.3 MB')",
            "received_rate_human": "Human-readable receive rate (e.g., '500 KB/s')",
            "sent_rate_human": "Human-readable send rate (e.g., '750 KB/s')"
        },
        "packets": {
            "received": "Total packets received",
            "sent": "Total packets sent",
            "received_rate": "Packets received per second",
            "sent_rate": "Packets sent per second"
        }
    },
    "network_quality": {
        "latency_ms": "Average round-trip time in milliseconds",
        "packet_loss_percent": "Percentage of lost packets (0-100)",
        "jitter_ms": "Jitter (mean deviation) in milliseconds"
    },
    "historical_data": [
        // Array of previous traffic measurements (last 100 entries)
        // Each entry follows the same format as the "traffic" object
    ]
}

Metrics Explained:
- bytes: Network throughput measurements
  * received/sent: Total data transferred
  * rates: Current transfer speeds
  * human-readable: Formatted values for display (B, KB, MB, GB, TB)
- packets: Network packet statistics
  * received/sent: Total packet counts
  * rates: Current packet rates
- network_quality: Connection quality metrics
  * latency: Network delay
  * packet_loss: Reliability indicator
  * jitter: Network stability indicator
- historical_data: Rolling window of previous measurements
  * Used for trend analysis
  * Limited to last 100 entries
  * Useful for graphing historical patterns
"""

import subprocess
import re
import time
import json
import logging
import ssl
import socket
from datetime import datetime
from typing import Dict, List, Any, Optional

from vpn.metrics.collector.base import BaseMonitor
from vpn.metrics.collector.ping import PingMonitor

class TrafficMonitor(BaseMonitor):
    """Monitor for network traffic statistics.

    This class specializes in monitoring network traffic data including
    bytes transmitted/received, packet counts, and transfer rates.
    It provides both raw statistical data and human-readable summaries.

    :param target: Target hostname or IP address to monitor
    :type target: str
    :ivar interface: Network interface being monitored
    :type interface: str
    :ivar previous_stats: Previous traffic statistics
    :type previous_stats: Dict[str, int]
    :ivar current_stats: Current traffic statistics
    :type current_stats: Dict[str, int]
    :ivar traffic_history: Historical traffic data
    :type traffic_history: List[Dict[str, Any]]
    :ivar last_collection_time: Timestamp of last collection
    :type last_collection_time: Optional[float]
    """

    def __init__(self, target: str):
        """Initialize the Traffic Monitor.

        :param target: Target hostname or IP address to monitor
        :type target: str
        """
        super().__init__(target)
        self.interface = self._detect_interface()
        self.previous_stats = {}
        self.current_stats = {}
        self.traffic_history = []
        self.last_collection_time = None
        print(f"Initialized Traffic Monitor for {target} on interface {self.interface}")

    def check_tls(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """
        Check TLS certificate information for the target host.

        Args:
            hostname (str): Hostname to check TLS for
            port (int): Port to check TLS on (default: 443)

        Returns:
            Dict[str, Any]: TLS certificate information
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'tls_version': ssock.version(),
                        'cipher': ssock.cipher(),
                        'cert_expiry': datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z').isoformat(),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'subject': dict(x[0] for x in cert['subject'])
                    }
        except Exception as e:
            self.logger.error(f"TLS check failed for {hostname}: {e}")
            return {
                'tls_version': None,
                'cipher': None,
                'cert_expiry': None,
                'issuer': None,
                'subject': None,
                'error': str(e)
            }

    def _detect_interface(self) -> str:
        """Detect the network interface used to reach the target.

        Determines which network interface is used to route traffic to the target.

        :return: Name of the network interface
        :rtype: str
        :raises subprocess.SubprocessError: If ip route command fails
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
            print(f"Could not detect interface for {self.target}, using default")
            return self._get_default_interface()
        except Exception as e:
            print(f"Error detecting interface: {e}")
            return self._get_default_interface()

    def _get_default_interface(self) -> str:
        """Get the default network interface.

        :return: Name of the default network interface
        :rtype: str
        :raises subprocess.SubprocessError: If ip route command fails
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
            print(f"Error getting default interface: {e}")
            return 'eth0'  # Default fallback

    def _list_interfaces(self) -> List[str]:
        """List all network interfaces on the system.

        :return: List of interface names
        :rtype: List[str]
        :raises subprocess.SubprocessError: If ip link command fails
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
            print(f"Error listing interfaces: {e}")
            return []

    def _get_interface_stats(self, interface: str) -> Dict[str, int]:
        """Get current traffic statistics for a network interface.

        :param interface: Network interface name
        :type interface: str
        :return: Dictionary with rx_bytes, tx_bytes, rx_packets, tx_packets
        :rtype: Dict[str, int]
        :raises FileNotFoundError: If /proc/net/dev cannot be read
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
                print(f"No stats found for interface {interface}")
                # Return zeros as fallback
                stats = {
                    'rx_bytes': 0,
                    'rx_packets': 0,
                    'tx_bytes': 0,
                    'tx_packets': 0
                }

            return stats
        except Exception as e:
            print(f"Error getting interface stats: {e}")
            return {
                'rx_bytes': 0,
                'rx_packets': 0,
                'tx_bytes': 0,
                'tx_packets': 0
            }

    def _calculate_rates(self, current: Dict[str, int], previous: Dict[str, int],
                        interval: float) -> Dict[str, float]:
        """Calculate traffic rates based on current and previous stats.

        :param current: Current traffic statistics
        :type current: Dict[str, int]
        :param previous: Previous traffic statistics
        :type previous: Dict[str, int]
        :param interval: Time interval in seconds
        :type interval: float
        :return: Dictionary with calculated rates (bytes/sec, packets/sec)
        :rtype: Dict[str, float]
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
        """Get traffic statistics specific to the target.

        :return: Dictionary with target-specific traffic data
        :rtype: Dict[str, Any]
        :raises Exception: If traffic data collection fails
        """
        try:
            # Get current interface stats
            self.current_stats = self._get_interface_stats(self.interface)

            # Calculate rates if we have previous stats
            current_time = time.time()
            interval = current_time - self.last_collection_time if self.last_collection_time else 1.0
            rates = self._calculate_rates(self.current_stats, self.previous_stats, interval)

            # Store current stats as previous for next calculation
            self.previous_stats = self.current_stats.copy()
            self.last_collection_time = current_time

            # Format the results
            return {
                'interface': self.interface,
                'timestamp': datetime.now().isoformat(),
                'bytes': {
                    'received': self.current_stats['rx_bytes'],
                    'sent': self.current_stats['tx_bytes'],
                    'received_rate': rates['rx_bytes_rate'],
                    'sent_rate': rates['tx_bytes_rate'],
                    'received_human': self._format_bytes(self.current_stats['rx_bytes']),
                    'sent_human': self._format_bytes(self.current_stats['tx_bytes']),
                    'received_rate_human': f"{self._format_bytes(rates['rx_bytes_rate'])}/s",
                    'sent_rate_human': f"{self._format_bytes(rates['tx_bytes_rate'])}/s"
                },
                'packets': {
                    'received': self.current_stats['rx_packets'],
                    'sent': self.current_stats['tx_packets'],
                    'received_rate': rates['rx_packets_rate'],
                    'sent_rate': rates['tx_packets_rate']
                }
            }
        except Exception as e:
            print(f"Error getting target traffic: {e}")
            raise

    def _get_ping_data_if_needed(self) -> Optional[Dict[str, Any]]:
        """Get ping data if needed for traffic analysis.

        :return: Ping data if available, None otherwise
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            # Use PingMonitor to get ICMP metrics
            ping_monitor = PingMonitor(self.target)
            ping_result = ping_monitor.ping_target(count=4)

            if ping_result.get('status') == 'online':
                return {
                    'latency_ms': ping_result.get('rtt_stats', {}).get('avg_ms', 0),
                    'packet_loss_percent': ping_result.get('packet_loss_percent', 0),
                    'jitter_ms': ping_result.get('rtt_stats', {}).get('mdev_ms', 0)
                }
            return None
        except Exception as e:
            print(f"Error getting ping data: {e}")
            return None

    def collect(self) -> Dict[str, Any]:
        """Collect traffic metrics for the target.

        Performs traffic monitoring to measure throughput, packet counts,
        and network quality metrics.

        :return: Dictionary with traffic metrics
        :rtype: Dict[str, Any]
        :raises Exception: If collection fails
        """
        try:
            # Start with the basic result structure
            result = self.get_basic_result()

            # Get interface traffic data
            traffic_data = self._get_target_traffic()
            result['traffic'] = traffic_data

            # Get ping data if needed
            ping_data = self._get_ping_data_if_needed()
            if ping_data:
                result['network_quality'] = ping_data

            # Add historical data
            self.traffic_history.append(traffic_data)
            if len(self.traffic_history) > 100:  # Keep last 100 entries
                self.traffic_history = self.traffic_history[-100:]
            result['historical_data'] = self.traffic_history

            return result
        except Exception as e:
            print(f"Error in traffic collection: {e}")
            raise

# Standalone testing when script is run directly
if __name__ == "__main__":
    # Setup basic logging if running standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)

    # Test the traffic monitor
    targets = ["google.com", "8.8.8.8"]

    for target in targets:
        try:
            logger.info(f"Testing {target}")
            monitor = TrafficMonitor(target)
            results = monitor.collect()
            logger.info(f"\nResults for {target}:")
            logger.info(json.dumps(results, indent=2))
        except Exception as e:
            logger.error(f"Failed to collect metrics for {target}: {str(e)}")
            logger.error(f"Error details: {e.__class__.__name__}")
