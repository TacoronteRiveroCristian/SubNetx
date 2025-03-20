#!/usr/bin/env python3
"""
SubNetx VPN Traffic Monitor
This script monitors network traffic to/from specified hosts or interfaces.
Includes TLS verification, ICMP details, and response time metrics.
"""

import subprocess
import re
import time
import json
import logging
import ssl
import socket
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

    def _get_icmp_metrics(self, target: str = None) -> Dict[str, Any]:
        """
        Collect ICMP ping metrics for the target.

        Args:
            target (str, optional): IP address to ping. If None, uses self.target.

        Returns:
            Dict[str, Any]: ICMP metrics including response times
        """
        ping_target = target if target else self.target
        try:
            # Run ping command with 4 packets
            result = subprocess.run(
                ['ping', '-c', '4', ping_target],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Ping failed with return code {result.returncode}"
                }

            # Parse the ping output
            packet_loss_match = re.search(r'(\d+)% packet loss', result.stdout)
            packet_loss = packet_loss_match.group(1) if packet_loss_match else "100"

            rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', result.stdout)
            if rtt_match:
                rtt_stats = {
                    'min': float(rtt_match.group(1)),
                    'avg': float(rtt_match.group(2)),
                    'max': float(rtt_match.group(3)),
                    'mdev': float(rtt_match.group(4))
                }
            else:
                rtt_stats = {'min': 0, 'avg': 0, 'max': 0, 'mdev': 0}

            # Extract ICMP sequence details
            icmp_details = []
            for line in result.stdout.split('\n'):
                if 'icmp_seq=' in line:
                    icmp_match = re.search(r'icmp_seq=(\d+).*time=([\d.]+)', line)
                    if icmp_match:
                        icmp_details.append({
                            'sequence': int(icmp_match.group(1)),
                            'response_time': float(icmp_match.group(2))
                        })

            return {
                'success': True,
                'packet_loss': float(packet_loss),
                'rtt_stats': rtt_stats,
                'icmp_details': icmp_details
            }
        except Exception as e:
            self.logger.error(f"Error collecting ICMP metrics: {e}")
            return {
                'success': False,
                'error': str(e)
            }

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
        Collect traffic metrics for the target.

        Returns:
            Dict[str, Any]: Dictionary with traffic metrics
        """
        try:
            now = time.time()
            timestamp = datetime.now().isoformat()

            # Get current interface stats
            self.current_stats = self._get_interface_stats(self.interface)

            # Calculate rates if we have previous stats
            rates = self._calculate_rates(
                self.current_stats,
                self.previous_stats,
                now - self.last_collection_time if hasattr(self, 'last_collection_time') else 0
            )

            # Get target-specific traffic if available
            target_traffic = self._get_target_traffic()

            # Add TLS information if it's a hostname
            tls_info = {}
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', self.target):
                tls_info = self.check_tls(self.target)

            # Get ICMP metrics
            icmp_metrics = self._get_icmp_metrics()

            # Store stats for next calculation
            self.previous_stats = self.current_stats
            self.last_collection_time = now

            # Create human-readable rates
            human_readable = {
                'rx_rate': self._format_bytes(rates.get('rx_bytes_rate', 0)),
                'tx_rate': self._format_bytes(rates.get('tx_bytes_rate', 0)),
                'total_rx': self._format_bytes(self.current_stats.get('rx_bytes', 0)),
                'total_tx': self._format_bytes(self.current_stats.get('tx_bytes', 0))
            }

            # Create result dictionary
            result = {
                'timestamp': timestamp,
                'interface': self.interface,
                'target': self.target,
                'current_stats': self.current_stats,
                'rates': rates,
                'human_readable': human_readable,
                'target_traffic': target_traffic,
                'tls_info': tls_info,
                'icmp_metrics': icmp_metrics
            }

            # Add to history (keep last 100 entries)
            self.traffic_history.append({
                'timestamp': timestamp,
                'rx_rate': rates.get('rx_bytes_rate', 0),
                'tx_rate': rates.get('tx_bytes_rate', 0)
            })

            if len(self.traffic_history) > 100:
                self.traffic_history = self.traffic_history[-100:]

            return result
        except Exception as e:
            self.logger.error(f"Error collecting traffic metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'interface': self.interface,
                'target': self.target,
                'error': str(e)
            }

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
