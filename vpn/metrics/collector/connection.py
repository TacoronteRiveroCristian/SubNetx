#!/usr/bin/env python3
"""
SubNetx VPN Connection Monitor
This script tracks connection status, uptime, and disconnection events.
Includes TLS verification, ICMP details, and response time measurements.
"""

import subprocess
import time
import json
import logging
import socket
import os
import ssl
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class ConnectionMonitor:
    def __init__(self, target: str):
        """
        Initialize the Connection Monitor.

        Args:
            target (str): Target hostname or IP address to monitor
        """
        self.target = target
        self.connection_history = []
        self.disconnection_events = []
        self.first_seen = None
        self.last_seen = None
        self.current_session_start = None
        self.is_connected = False
        self.total_uptime = 0
        self.total_downtime = 0
        self.status_history = []
        self.logger = logging.getLogger('subnetx')
        self.logger.info(f"Initialized Connection Monitor for {target}")

        # Attempt initial connection check
        self._check_connection()

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

    def _get_icmp_metrics(self) -> Dict[str, Any]:
        """
        Collect ICMP ping metrics for the target.

        Returns:
            Dict[str, Any]: ICMP metrics including response times
        """
        try:
            # Run ping command with 4 packets
            result = subprocess.run(
                ['ping', '-c', '4', self.target],
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

    def _check_connection(self) -> bool:
        """
        Check if connection to target is active.

        Returns:
            bool: True if connected, False otherwise
        """
        now = datetime.now()
        was_connected = self.is_connected

        # Try to connect to the target with a socket
        try:
            # First try with socket to test TCP connectivity
            # Default to port 80 since it's commonly open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout

            # Try to resolve hostname first
            try:
                ip = socket.gethostbyname(self.target)
            except socket.gaierror:
                # Can't resolve hostname, might be DNS issue
                ip = self.target  # Just use the target as-is

            result = sock.connect_ex((ip, 80))
            sock.close()

            if result == 0:
                # Connection succeeded
                self.is_connected = True
            else:
                # Fall back to ping if TCP connection fails
                ping_result = subprocess.run(
                    ['ping', '-c', '1', '-W', '2', self.target],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.is_connected = ping_result.returncode == 0

        except Exception as e:
            self.logger.warning(f"Connection check error: {e}")
            self.is_connected = False

        # Update connection records
        if self.is_connected:
            # We're connected
            if not was_connected:
                # This is a new connection
                self.logger.info(f"Connection established to {self.target}")
                self.current_session_start = now

            if self.first_seen is None:
                self.first_seen = now

            self.last_seen = now
        else:
            # We're disconnected
            if was_connected:
                # This is a new disconnection
                self.logger.warning(f"Connection lost to {self.target}")

                # Record the disconnection event
                if self.current_session_start:
                    session_duration = (now - self.current_session_start).total_seconds()
                    disconnection_event = {
                        'disconnection_time': now.isoformat(),
                        'session_start': self.current_session_start.isoformat(),
                        'session_duration_seconds': session_duration
                    }
                    self.disconnection_events.append(disconnection_event)
                    self.logger.info(f"Disconnection after {session_duration:.1f} seconds")

                    # Update total uptime
                    self.total_uptime += session_duration

                self.current_session_start = None

        # Update status history (keep last 100 entries)
        status_entry = {
            'timestamp': now.isoformat(),
            'connected': self.is_connected
        }
        self.status_history.append(status_entry)

        if len(self.status_history) > 100:
            self.status_history.pop(0)

        return self.is_connected

    def _calculate_uptime_percentage(self) -> float:
        """
        Calculate the connection uptime percentage.

        Returns:
            float: Uptime percentage (0-100)
        """
        if not self.first_seen:
            return 0.0

        now = datetime.now()

        # Calculate total monitoring time
        total_time = (now - self.first_seen).total_seconds()

        # Add current session to uptime if connected
        current_uptime = self.total_uptime
        if self.is_connected and self.current_session_start:
            current_session_time = (now - self.current_session_start).total_seconds()
            current_uptime += current_session_time

        # Calculate percentage
        if total_time > 0:
            return (current_uptime / total_time) * 100
        else:
            return 0.0

    def _check_openvpn_status(self) -> Dict[str, Any]:
        """
        Check OpenVPN service status if available.

        Returns:
            Dict[str, Any]: OpenVPN status information
        """
        result = {
            'service_available': False,
            'is_running': False,
            'uptime': None,
            'active_clients': 0
        }

        try:
            # Check if openvpn service is running
            service_check = subprocess.run(
                ['systemctl', 'is-active', 'openvpn'],
                capture_output=True,
                text=True
            )

            result['service_available'] = True
            result['is_running'] = service_check.stdout.strip() == 'active'

            if result['is_running']:
                # Get service uptime
                uptime_check = subprocess.run(
                    ['systemctl', 'show', 'openvpn', '--property=ActiveEnterTimestamp'],
                    capture_output=True,
                    text=True
                )

                # Parse the timestamp
                if 'ActiveEnterTimestamp=' in uptime_check.stdout:
                    timestamp_str = uptime_check.stdout.replace('ActiveEnterTimestamp=', '').strip()
                    if timestamp_str:
                        try:
                            start_time = datetime.strptime(timestamp_str, '%a %Y-%m-%d %H:%M:%S %Z')
                            uptime_seconds = (datetime.now() - start_time).total_seconds()
                            result['uptime'] = uptime_seconds
                        except ValueError:
                            pass

                # Check for active clients if status log is available
                try:
                    if os.path.exists('/var/log/openvpn/status.log'):
                        with open('/var/log/openvpn/status.log', 'r') as f:
                            status_data = f.read()

                        # Count client lines
                        client_count = 0
                        for line in status_data.split('\n'):
                            if line.startswith('CLIENT_LIST'):
                                client_count += 1

                        result['active_clients'] = client_count
                except Exception as e:
                    self.logger.error(f"Error reading OpenVPN status: {e}")

        except Exception as e:
            self.logger.error(f"Error checking OpenVPN service: {e}")

        return result

    def _format_uptime(self, seconds: float) -> str:
        """
        Format seconds into human readable uptime string.

        Args:
            seconds (float): Duration in seconds

        Returns:
            str: Formatted uptime string (e.g. "3d 12h 5m 10s")
        """
        if seconds is None:
            return "unknown"

        # Convert to timedelta for easy handling
        td = timedelta(seconds=seconds)

        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format the string
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)

    def _analyze_connection_stability(self) -> Dict[str, Any]:
        """
        Analyze connection stability based on history.

        Returns:
            Dict[str, Any]: Stability analysis
        """
        # We need enough history to make an assessment
        if len(self.status_history) < 5:
            return {
                'stability': 'unknown',
                'reason': 'insufficient data'
            }

        # Count transitions (connected->disconnected or vice versa)
        transitions = 0
        for i in range(1, len(self.status_history)):
            if self.status_history[i]['connected'] != self.status_history[i-1]['connected']:
                transitions += 1

        # Calculate stability metrics
        uptime_pct = self._calculate_uptime_percentage()

        # Assess stability
        if transitions == 0:
            if uptime_pct > 99:
                stability = 'excellent'
            elif uptime_pct > 90:
                stability = 'good'
            elif uptime_pct > 50:
                stability = 'fair'
            else:
                stability = 'poor'
        elif transitions < 3:
            if uptime_pct > 95:
                stability = 'good'
            elif uptime_pct > 80:
                stability = 'fair'
            else:
                stability = 'unstable'
        else:
            if uptime_pct > 90:
                stability = 'fair'
            else:
                stability = 'unstable'

        # Determine reason
        if uptime_pct < 50:
            reason = 'low uptime percentage'
        elif transitions > 5:
            reason = 'frequent disconnections'
        elif transitions > 0:
            reason = 'occasional disconnections'
        else:
            reason = 'stable connection'

        return {
            'stability': stability,
            'reason': reason,
            'transitions': transitions,
            'uptime_percentage': uptime_pct
        }

    def collect(self) -> Dict[str, Any]:
        """
        Collect connection metrics.

        Returns:
            Dict[str, Any]: Dictionary with connection metrics
        """
        try:
            # Check the current connection status
            self._check_connection()

            # Calculate uptime percentage
            uptime_percentage = self._calculate_uptime_percentage()

            # Check OpenVPN status if available
            openvpn_status = self._check_openvpn_status()

            # Analyze connection stability
            stability_analysis = self._analyze_connection_stability()

            # Add TLS information if it's a hostname
            tls_info = {}
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', self.target):
                tls_info = self.check_tls(self.target)

            # Get ICMP metrics
            icmp_metrics = self._get_icmp_metrics()

            # Convert timestamps to strings for JSON serialization
            first_seen_str = self.first_seen.isoformat() if self.first_seen else None
            last_seen_str = self.last_seen.isoformat() if self.last_seen else None
            current_session_start_str = self.current_session_start.isoformat() if self.current_session_start else None

            # Build the result
            result = {
                'timestamp': datetime.now().isoformat(),
                'target': self.target,
                'status': {
                    'connected': self.is_connected,
                    'first_seen': first_seen_str,
                    'last_seen': last_seen_str,
                    'current_session_start': current_session_start_str,
                    'uptime_seconds': self.total_uptime,
                    'uptime_formatted': self._format_uptime(self.total_uptime),
                    'uptime_percentage': uptime_percentage,
                    'total_sessions': len(self.disconnection_events) + (1 if self.is_connected else 0)
                },
                'history': {
                    'status_history': self.status_history[-20:],  # Last 20 status checks
                    'disconnection_events': self.disconnection_events[-10:]  # Last 10 disconnections
                },
                'openvpn_status': openvpn_status,
                'stability_analysis': stability_analysis,
                'tls_info': tls_info,
                'icmp_metrics': icmp_metrics
            }

            return result
        except Exception as e:
            self.logger.error(f"Error collecting connection metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
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

    # Test the connection monitor
    target = "google.com"
    monitor = ConnectionMonitor(target)

    print(f"Initial connection check for {target}")
    results = monitor.collect()
    print(json.dumps(results, indent=2))

    print("\nWaiting 10 seconds for another check...")
    time.sleep(10)

    results = monitor.collect()
    print("\nUpdated connection status:")
    print(json.dumps(results, indent=2))
