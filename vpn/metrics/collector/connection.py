#!/usr/bin/env python3
"""
SubNetx VPN Connection Monitor
This script tracks connection status, uptime, and disconnection events.
"""

import subprocess
import time
import json
import logging
import socket
import os
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
        # Check current connection
        is_connected = self._check_connection()

        # Get OpenVPN status if relevant
        openvpn_status = self._check_openvpn_status()

        # Calculate uptime stats
        uptime_pct = self._calculate_uptime_percentage()

        # Current session duration
        current_session_duration = None
        if self.is_connected and self.current_session_start:
            current_session_duration = (datetime.now() - self.current_session_start).total_seconds()

        # Analyze connection stability
        stability_analysis = self._analyze_connection_stability()

        # Build the result
        result = {
            'timestamp': datetime.now().isoformat(),
            'target': self.target,
            'current_status': {
                'connected': is_connected,
                'current_session_start': self.current_session_start.isoformat() if self.current_session_start else None,
                'current_session_duration': current_session_duration,
                'current_session_duration_formatted': self._format_uptime(current_session_duration) if current_session_duration else None
            },
            'connection_stats': {
                'first_seen': self.first_seen.isoformat() if self.first_seen else None,
                'last_seen': self.last_seen.isoformat() if self.last_seen else None,
                'uptime_percentage': uptime_pct,
                'total_uptime_seconds': self.total_uptime + (current_session_duration or 0),
                'total_uptime_formatted': self._format_uptime(self.total_uptime + (current_session_duration or 0)),
                'disconnection_count': len(self.disconnection_events)
            },
            'vpn_service': openvpn_status,
            'stability_analysis': stability_analysis,
            'recent_disconnections': self.disconnection_events[-5:] if self.disconnection_events else []
        }

        # Log current status
        if is_connected:
            self.logger.info(f"Connection to {self.target} is UP (uptime: {result['current_status']['current_session_duration_formatted']})")
        else:
            self.logger.warning(f"Connection to {self.target} is DOWN")

        # Log stability assessment
        self.logger.info(f"Connection stability: {stability_analysis['stability']} ({stability_analysis['reason']})")

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
