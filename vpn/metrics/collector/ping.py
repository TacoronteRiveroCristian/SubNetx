#!/usr/bin/env python3
"""
SubNetx VPN Client Ping Monitor

This module provides functionality to monitor VPN client connectivity
through ICMP ping tests, measuring latency, packet loss, and response times.
It serves as the primary tool for basic connectivity assessment.

JSON Response Format:
{
    "timestamp": "ISO-8601 timestamp of the measurement",
    "target": "Target hostname or IP being monitored",
    "primary_target": {
        "ip": "IP address of the target",
        "status": "Connection status ('online', 'offline', or 'timeout')",
        "timestamp": "ISO-8601 timestamp of the ping test",
        "connection_quality": "Quality assessment ('excellent', 'good', 'fair', 'poor', or 'none')",
        "rtt_stats": {
            "min_ms": "Minimum round-trip time in milliseconds",
            "avg_ms": "Average round-trip time in milliseconds",
            "max_ms": "Maximum round-trip time in milliseconds",
            "mdev_ms": "Mean deviation of round-trip times in milliseconds"
        },
        "icmp_details": [
            {
                "sequence": "ICMP sequence number",
                "response_time_ms": "Response time for this packet in milliseconds"
            }
        ],
        "packet_loss_percent": "Percentage of lost packets (0-100)",
        "packets": {
            "transmitted": "Number of packets sent",
            "received": "Number of packets received"
        },
        "raw_output": "Raw output from the ping command",
        "tls_info": {
            "certificate": "SSL/TLS certificate information (if applicable)",
            "expiry": "Certificate expiration date",
            "issuer": "Certificate issuer details"
        }
    }
}

Metrics Explained:
- status: Overall connection status of the target
- connection_quality: Based on packet loss:
  * excellent: 0% packet loss
  * good: < 5% packet loss
  * fair: < 20% packet loss
  * poor: >= 20% packet loss
- rtt_stats: Round-trip time statistics showing network latency
- packet_loss_percent: Percentage of packets that didn't receive a response
- icmp_details: Detailed information about each ICMP packet sent
- tls_info: SSL/TLS certificate information for HTTPS targets
"""

import subprocess
import json
import re
from datetime import datetime
import logging
from typing import Dict, List, Any

from vpn.metrics.collector.base import BaseMonitor

class PingMonitor(BaseMonitor):
    """VPN Ping Monitor for measuring network connectivity and latency.

    This class specializes in ICMP ping-based measurements, providing
    detailed packet loss statistics, response times in milliseconds,
    and connection quality assessment.

    :param target: Target hostname or IP address to monitor
    :type target: str
    :ivar results: Storage for ping test results
    :type results: Dict[str, Any]
    """

    def __init__(self, target: str):
        """Initialize the VPN Ping Monitor.

        :param target: Target hostname or IP address to monitor
        :type target: str
        """
        super().__init__(target)
        self.results = {}

    def get_active_clients(self) -> List[str]:
        """Get list of active VPN clients from OpenVPN status file.

        :return: List of client IP addresses
        :rtype: List[str]
        :raises FileNotFoundError: If status file cannot be found
        """
        try:
            # Read the status file
            # TODO: Here you have to edit the script so that
            # it takes the clients that are in the ccd folder
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
            print(f"Error reading status file: {e}")
            raise

    def _parse_ping_output(self, output: str) -> Dict[str, Any]:
        """Parse the ping command output to extract metrics.

        :param output: Raw output from ping command
        :type output: str
        :return: Dictionary with parsed ping metrics
        :rtype: Dict[str, Any]
        :raises ValueError: If ping output cannot be parsed
        """
        try:
            # Extract packet loss percentage
            packet_loss_match = re.search(r'(\d+)% packet loss', output)
            packet_loss = packet_loss_match.group(1) if packet_loss_match else "100"

            # Extract round-trip time statistics
            rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
            if rtt_match:
                rtt_stats = {
                    'min_ms': float(rtt_match.group(1)),
                    'avg_ms': float(rtt_match.group(2)),
                    'max_ms': float(rtt_match.group(3)),
                    'mdev_ms': float(rtt_match.group(4))
                }
            else:
                rtt_stats = {'min_ms': 0, 'avg_ms': 0, 'max_ms': 0, 'mdev_ms': 0}

            # Extract ICMP sequence details
            icmp_details = []
            for line in output.split('\n'):
                if 'icmp_seq=' in line:
                    icmp_match = re.search(r'icmp_seq=(\d+).*time=([\d.]+)', line)
                    if icmp_match:
                        icmp_details.append({
                            'sequence': int(icmp_match.group(1)),
                            'response_time_ms': float(icmp_match.group(2))
                        })

            # Extract transmitted and received packets
            packets_match = re.search(r'(\d+) packets transmitted, (\d+) received', output)
            if packets_match:
                transmitted = int(packets_match.group(1))
                received = int(packets_match.group(2))
            else:
                transmitted = 0
                received = 0

            return {
                'timestamp': datetime.now().isoformat(),
                'packet_loss_percent': float(packet_loss),
                'rtt_stats': rtt_stats,
                'icmp_details': icmp_details,
                'packets': {
                    'transmitted': transmitted,
                    'received': received
                }
            }
        except Exception as e:
            print(f"Error parsing ping output: {e}")
            raise ValueError(f"Failed to parse ping output: {e}")

    def ping_target(self, ip: str = None, count: int = 4, timeout: int = 10) -> Dict[str, Any]:
        """Perform ping test on a target IP.

        :param ip: IP address to ping. If None, uses self.target
        :type ip: str, optional
        :param count: Number of ICMP packets to send
        :type count: int, optional
        :param timeout: Timeout in seconds
        :type timeout: int, optional
        :return: Ping results including status, latency and packet loss
        :rtype: Dict[str, Any]
        :raises subprocess.TimeoutExpired: If ping command times out
        :raises subprocess.SubprocessError: If ping command fails
        """
        target = ip if ip else self.target
        print(f"Pinging {target}...")

        try:
            # Perform ping test
            result = subprocess.run(
                ['ping', '-c', str(count), target],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Parse ping output
            if result.returncode == 0:
                # Parse the ping output
                parsed_results = self._parse_ping_output(result.stdout)

                # Determine connection quality based on packet loss
                packet_loss = parsed_results['packet_loss_percent']
                connection_quality = 'excellent' if packet_loss == 0 else \
                                     'good' if packet_loss < 5 else \
                                     'fair' if packet_loss < 20 else \
                                     'poor'

                return {
                    'ip': target,
                    'status': 'online',
                    'timestamp': datetime.now().isoformat(),
                    'connection_quality': connection_quality,
                    'rtt_stats': parsed_results['rtt_stats'],
                    'icmp_details': parsed_results['icmp_details'],
                    'packet_loss_percent': parsed_results['packet_loss_percent'],
                    'packets': parsed_results['packets'],
                    'raw_output': result.stdout
                }
            else:
                print(f"Ping to {target} failed with return code {result.returncode}")
                return {
                    'ip': target,
                    'status': 'offline',
                    'timestamp': datetime.now().isoformat(),
                    'connection_quality': 'none',
                    'error': result.stderr
                }

        except subprocess.TimeoutExpired:
            print(f"Ping to {target} timed out")
            return {
                'ip': target,
                'status': 'timeout',
                'timestamp': datetime.now().isoformat(),
                'connection_quality': 'none',
                'error': 'Ping timeout'
            }
        except Exception as e:
            print(f"Error pinging {target}: {e}")
            raise

    def collect(self) -> Dict[str, Any]:
        """Collect ping metrics for the target.

        Performs ping tests to measure basic connectivity metrics including
        latency, packet loss, and jitter.

        :return: Dictionary with ping metrics
        :rtype: Dict[str, Any]
        :raises Exception: If collection fails
        """
        try:
            # Start with the basic result structure
            result = self.get_basic_result()

            # Ping the main target
            ping_result = self.ping_target()

            # Add TLS information for hostnames
            if self.is_hostname(self.target):
                tls_info = self.get_tls_info()
                ping_result['tls_info'] = tls_info

            self.results[self.target] = ping_result
            result['primary_target'] = ping_result

            # If we're monitoring a VPN server, we could also ping clients
            if self.target.startswith('10.') or self.target.startswith('192.168.'):
                # This might be a VPN server, so ping clients too
                clients_results = {}
                try:
                    clients = self.get_active_clients()
                    for client in clients:
                        if client != self.target:  # Don't ping the target twice
                            client_result = self.ping_target(client)
                            if client_result:
                                clients_results[client] = client_result
                                print(f"Client ping result for {client}: {client_result['status']}")

                    if clients_results:
                        result['vpn_clients'] = clients_results
                except Exception as e:
                    print(f"Error pinging VPN clients: {e}")
                    result['vpn_clients_error'] = str(e)

            return result
        except Exception as e:
            print(f"Error in ping collection: {e}")
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

    # Test the ping monitor
    targets = ["google.com", "8.8.8.8", "invalid.example.domain"]

    for target in targets:
        try:
            logger.info(f"Testing {target}")
            monitor = PingMonitor(target)
            results = monitor.collect()
            logger.info(f"\nResults for {target}:")
            logger.info(json.dumps(results, indent=2))
        except Exception as e:
            logger.error(f"Failed to collect metrics for {target}: {str(e)}")
            logger.error(f"Error details: {e.__class__.__name__}")
