#!/usr/bin/env python3
"""
SubNetx VPN Client Ping Monitor
This script monitors the status and latency of VPN clients by performing ping tests.
Includes TLS verification, ICMP metrics, and response time measurements.
"""

import subprocess
import json
import time
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any
import re
import ssl
import socket

class VPNPingMonitor:
    def __init__(self, target: str):
        """
        Initialize the VPN Ping Monitor.

        Args:
            target (str): Target hostname or IP address to monitor
        """
        self.target = target
        self.results = {}
        self.logger = logging.getLogger('subnetx')
        self.logger.info(f"Initialized Ping Monitor for {target}")

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

    def _parse_ping_output(self, output: str) -> Dict[str, Any]:
        """
        Parse the ping command output to extract metrics.

        Args:
            output (str): Raw output from ping command

        Returns:
            Dict[str, Any]: Dictionary with parsed metrics
        """
        try:
            # Extract packet loss percentage using regex - capture both number and %
            packet_loss_match = re.search(r'(\d+%)', output)
            packet_loss = packet_loss_match.group(1) if packet_loss_match else "100%"

            # Extract round-trip time statistics
            rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
            if rtt_match:
                rtt_stats = {
                    'min': float(rtt_match.group(1)),
                    'avg': float(rtt_match.group(2)),
                    'max': float(rtt_match.group(3)),
                    'mdev': float(rtt_match.group(4))
                }
            else:
                rtt_stats = {'min': 0, 'avg': 0, 'max': 0, 'mdev': 0}

            # Extract ICMP type and code information
            icmp_info = []
            for line in output.split('\n'):
                if 'icmp_seq=' in line:
                    icmp_match = re.search(r'icmp_seq=(\d+).*time=([\d.]+)', line)
                    if icmp_match:
                        icmp_info.append({
                            'sequence': int(icmp_match.group(1)),
                            'response_time': float(icmp_match.group(2))
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
                'packet_loss': packet_loss,
                'rtt_stats': rtt_stats,
                'icmp_details': icmp_info,
                'packets': {
                    'transmitted': transmitted,
                    'received': received
                }
            }
        except Exception as e:
            self.logger.error(f"Error parsing ping output: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'packet_loss': "100%",
                'rtt_stats': {'min': 0, 'avg': 0, 'max': 0, 'mdev': 0},
                'icmp_details': [],
                'packets': {'transmitted': 0, 'received': 0},
                'error': str(e)
            }

    def ping_target(self, ip: str = None) -> Optional[Dict]:
        """
        Perform ping test on a target IP.

        Args:
            ip (str, optional): IP address to ping. If None, uses self.target.

        Returns:
            Optional[Dict]: Ping results or None if failed
        """
        target = ip if ip else self.target
        self.logger.info(f"Pinging {target}...")

        try:
            # Perform ping test with 4 packets
            result = subprocess.run(
                ['ping', '-c', '4', target],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Parse ping output
            if result.returncode == 0:
                # Extract statistics
                stats = {}
                packet_loss = "100%"  # Default to 100% loss
                min_rtt = max_rtt = avg_rtt = std_rtt = "N/A"

                for line in result.stdout.split('\n'):
                    if 'min/avg/max' in line:
                        # Parse the RTT values (min/avg/max/mdev)
                        rtt_parts = line.split('=')[1].strip().split('/')
                        if len(rtt_parts) >= 4:
                            min_rtt = float(rtt_parts[0])
                            avg_rtt = float(rtt_parts[1])
                            max_rtt = float(rtt_parts[2])
                            std_rtt = float(rtt_parts[3].split()[0])  # Remove 'ms'
                    elif 'packet loss' in line:
                        # Parse packet loss percentage
                        for part in line.split(','):
                            if 'packet loss' in part:
                                packet_loss = re.search(r'(\d+)%', part).group(1)
                                break

                # Create detailed stats dictionary
                stats = {
                    'min_rtt': min_rtt,
                    'avg_rtt': avg_rtt,
                    'max_rtt': max_rtt,
                    'std_rtt': std_rtt,
                    'packet_loss': packet_loss
                }

                # Determine if connection is stable based on packet loss
                if packet_loss not in ['N/A', 'unknown', None]:
                    loss_pct = float(packet_loss)
                    connection_quality = 'excellent' if loss_pct == 0 else \
                                         'good' if loss_pct < 5 else \
                                         'fair' if loss_pct < 20 else \
                                         'poor'
                else:
                    connection_quality = 'unknown'

                # Get TLS information if it's a hostname
                tls_info = {}
                if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', target):
                    tls_info = self.check_tls(target)

                # Parse ICMP details
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
                    'ip': target,
                    'status': 'online',
                    'timestamp': datetime.now().isoformat(),
                    'connection_quality': connection_quality,
                    'stats': stats,
                    'tls_info': tls_info,
                    'icmp_details': icmp_details,
                    'raw_output': result.stdout
                }
            else:
                self.logger.warning(f"Ping to {target} failed with return code {result.returncode}")
                return {
                    'ip': target,
                    'status': 'offline',
                    'timestamp': datetime.now().isoformat(),
                    'connection_quality': 'none',
                    'stats': None,
                    'tls_info': {},
                    'icmp_details': [],
                    'error': result.stderr
                }

        except subprocess.TimeoutExpired:
            self.logger.warning(f"Ping to {target} timed out")
            return {
                'ip': target,
                'status': 'timeout',
                'timestamp': datetime.now().isoformat(),
                'connection_quality': 'none',
                'stats': None,
                'tls_info': {},
                'icmp_details': [],
                'error': 'Ping timeout'
            }
        except Exception as e:
            self.logger.error(f"Error pinging {target}: {e}")
            return {
                'ip': target,
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'connection_quality': 'none',
                'stats': None,
                'tls_info': {},
                'icmp_details': [],
                'error': str(e)
            }

    def collect(self) -> Dict[str, Any]:
        """
        Collect ping metrics for the target.

        Returns:
            Dict[str, Any]: Dictionary with ping metrics
        """
        # Ping the main target
        result = self.ping_target()
        self.results[self.target] = result

        # If we're monitoring a VPN server, we could also ping clients
        if self.target.startswith('10.') or self.target.startswith('192.168.'):
            # This might be a VPN server, so ping clients too
            try:
                clients = self.get_active_clients()
                for client in clients:
                    if client != self.target:  # Don't ping the target twice
                        client_result = self.ping_target(client)
                        if client_result:
                            self.results[client] = client_result
                            self.logger.info(f"Client ping result for {client}: {client_result['status']}")
            except Exception as e:
                self.logger.error(f"Error pinging VPN clients: {e}")

        return self.results

# Standalone testing when script is run directly
if __name__ == "__main__":
    # Setup basic logging if running standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger('subnetx')

    # Test the ping monitor
    targets = ["google.com", "8.8.8.8", "invalid.example.domain"]

    for target in targets:
        monitor = VPNPingMonitor(target)
        results = monitor.collect()
        print(f"\nResults for {target}:")
        print(json.dumps(results, indent=2))
