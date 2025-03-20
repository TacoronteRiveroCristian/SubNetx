#!/usr/bin/env python3
"""
SubNetx VPN Connection Monitor

This module provides functionality to monitor VPN connection status,
uptime, and stability metrics. It tracks connection events, calculates
uptime percentages, and analyzes connection patterns.
"""

import subprocess
import time
import json
import logging
import socket
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from .base import BaseMonitor
from .ping import PingMonitor

class ConnectionMonitor(BaseMonitor):
    """Monitor for VPN connection status and stability.

    This class specializes in monitoring VPN connection status, uptime,
    and connection stability metrics. It provides both real-time status
    and historical connection data.

    :param target: Target hostname or IP address to monitor
    :type target: str
    :ivar connection_history: List of connection status changes
    :type connection_history: List[Dict[str, Any]]
    :ivar disconnection_events: List of disconnection events
    :type disconnection_events: List[Dict[str, Any]]
    :ivar first_seen: Timestamp of first connection
    :type first_seen: Optional[float]
    :ivar last_seen: Timestamp of last connection
    :type last_seen: Optional[float]
    :ivar current_session_start: Start time of current session
    :type current_session_start: Optional[float]
    :ivar is_connected: Current connection status
    :type is_connected: bool
    :ivar total_uptime: Total time connected in seconds
    :type total_uptime: float
    :ivar total_downtime: Total time disconnected in seconds
    :type total_downtime: float
    :ivar status_history: List of status check results
    :type status_history: List[Dict[str, Any]]
    """

    def __init__(self, target: str):
        """Initialize the Connection Monitor.

        :param target: Target hostname or IP address to monitor
        :type target: str
        """
        super().__init__(target)
        self.connection_history = []
        self.disconnection_events = []
        self.first_seen = None
        self.last_seen = None
        self.current_session_start = None
        self.is_connected = False
        self.total_uptime = 0
        self.total_downtime = 0
        self.status_history = []
        print(f"Initialized Connection Monitor for {target}")

        # Attempt initial connection check
        self._check_connection()

    def _check_connection(self) -> bool:
        """Check if connection to target is active.

        Updates connection state and history based on current status.

        Returns:
            bool: True if connected, False otherwise.
        """
        now = datetime.now()
        was_connected = self.is_connected

        # Try to connect to the target
        try:
            # First try with socket to test TCP connectivity
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
                ping_monitor = PingMonitor(self.target)
                ping_result = ping_monitor.ping_target(count=1, timeout=2)
                self.is_connected = ping_result.get('status') == 'online'

        except Exception as e:
            print(f"Connection check error: {e}")
            self.is_connected = False

        # Update connection records
        if self.is_connected:
            # We're connected
            if not was_connected:
                # This is a new connection
                print(f"Connection established to {self.target}")
                self.current_session_start = now

            if self.first_seen is None:
                self.first_seen = now

            self.last_seen = now
        else:
            # We're disconnected
            if was_connected:
                # This is a new disconnection
                print(f"Connection lost to {self.target}")

                # Record the disconnection event
                if self.current_session_start:
                    session_duration = (now - self.current_session_start).total_seconds()
                    disconnection_event = {
                        'disconnection_time': now.isoformat(),
                        'session_start': self.current_session_start.isoformat(),
                        'session_duration_seconds': session_duration
                    }
                    self.disconnection_events.append(disconnection_event)
                    print(f"Disconnection after {session_duration:.1f} seconds")

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
        """Calculate the connection uptime percentage.

        Returns:
            float: Uptime percentage (0-100).
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
        """Check OpenVPN service status if available.

        Returns:
            Dict[str, Any]: OpenVPN status information.
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
                    print(f"Error reading OpenVPN status: {e}")

        except Exception as e:
            print(f"Error checking OpenVPN service: {e}")

        return result

    def _format_uptime(self, seconds: float) -> str:
        """Format seconds into human readable uptime string.

        Args:
            seconds (float): Duration in seconds.

        Returns:
            str: Formatted uptime string (e.g. "3d 12h 5m 10s").
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
        """Analyze connection stability based on history.

        Returns:
            Dict[str, Any]: Stability analysis including rating and reasons.
        """
        # Default stability assessment
        stability = {
            'stability': 'unknown',
            'rating': 0,
            'reason': 'Not enough data',
            'recommendations': []
        }

        # Need at least some history to analyze
        if not self.status_history or len(self.status_history) < 5:
            return stability

        # Calculate stability metrics
        total_checks = len(self.status_history)
        connected_checks = sum(1 for entry in self.status_history if entry['connected'])
        recent_disconnections = len(self.disconnection_events[-10:]) if self.disconnection_events else 0
        uptime_percentage = self._calculate_uptime_percentage()

        # Determine stability rating (0-100)
        rating = min(100, max(0, int(uptime_percentage)))

        # Determine stability category
        if rating >= 99:
            stability_category = 'excellent'
            reason = 'Consistent uptime with minimal disconnections'
        elif rating >= 95:
            stability_category = 'good'
            reason = 'Generally stable with occasional disconnections'
        elif rating >= 80:
            stability_category = 'fair'
            reason = 'Somewhat stable but with periodic disconnections'
        elif rating >= 50:
            stability_category = 'poor'
            reason = 'Frequent disconnections affecting service quality'
        else:
            stability_category = 'critical'
            reason = 'Severe connection issues affecting service usability'

        # Generate recommendations
        recommendations = []
        if rating < 80:
            recommendations.append('Check network configuration for issues')
        if recent_disconnections > 5:
            recommendations.append('Investigate causes of frequent disconnections')
        if rating < 50:
            recommendations.append('Consider alternative VPN routing or connectivity')

        # Return analysis
        return {
            'stability': stability_category,
            'rating': rating,
            'reason': reason,
            'uptime_percentage': uptime_percentage,
            'recent_disconnections': recent_disconnections,
            'total_checks': total_checks,
            'connected_checks': connected_checks,
            'recommendations': recommendations
        }

    def collect(self) -> Dict[str, Any]:
        """Collect connection metrics and status information.

        Returns:
            Dict[str, Any]: Dictionary with connection metrics.
        """
        try:
            # Start with the basic result structure
            result = self.get_basic_result()

            # Check the current connection status
            self._check_connection()

            # Calculate uptime percentage
            uptime_percentage = self._calculate_uptime_percentage()

            # Check OpenVPN status if available
            openvpn_status = self._check_openvpn_status()

            # Analyze connection stability
            stability_analysis = self._analyze_connection_stability()

            # Get TLS information if it's a hostname
            tls_info = self.get_tls_info() if self.is_hostname(self.target) else {}

            # Use PingMonitor for connectivity metrics when needed
            connectivity_metrics = {}
            if self.is_connected:
                try:
                    ping_monitor = PingMonitor(self.target)
                    ping_result = ping_monitor.ping_target(count=4)
                    if ping_result.get('status') == 'online':
                        connectivity_metrics = {
                            'rtt_stats': ping_result.get('rtt_stats', {}),
                            'packet_loss_percent': ping_result.get('packet_loss_percent', 0),
                            'icmp_details': ping_result.get('icmp_details', [])
                        }
                except Exception as e:
                    print(f"Error getting ping metrics: {e}")

            # Convert timestamps to strings for JSON serialization
            first_seen_str = self.first_seen.isoformat() if self.first_seen else None
            last_seen_str = self.last_seen.isoformat() if self.last_seen else None
            current_session_start_str = self.current_session_start.isoformat() if self.current_session_start else None

            # Calculate current session duration
            current_session_duration = None
            if self.is_connected and self.current_session_start:
                current_session_duration = (datetime.now() - self.current_session_start).total_seconds()

            # Build the result
            result.update({
                'status': {
                    'connected': self.is_connected,
                    'first_seen': first_seen_str,
                    'last_seen': last_seen_str,
                    'current_session_start': current_session_start_str,
                    'current_session_duration': current_session_duration,
                    'current_session_formatted': self._format_uptime(current_session_duration) if current_session_duration else None,
                    'uptime_seconds': self.total_uptime + (current_session_duration or 0),
                    'uptime_formatted': self._format_uptime(self.total_uptime + (current_session_duration or 0)),
                    'uptime_percentage': uptime_percentage,
                    'total_sessions': len(self.disconnection_events) + (1 if self.is_connected else 0)
                },
                'history': {
                    'status_history': self.status_history[-20:],  # Last 20 status checks
                    'disconnection_events': self.disconnection_events[-10:]  # Last 10 disconnections
                },
                'openvpn_status': openvpn_status,
                'stability_analysis': stability_analysis
            })

            # Add optional components if available
            if tls_info:
                result['tls_info'] = tls_info

            if connectivity_metrics:
                result['connectivity'] = connectivity_metrics

            return result
        except Exception as e:
            print(f"Error collecting connection metrics: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'target': self.target,
                'error': str(e)
            }

# Standalone testing when script is run directly
if __name__ == "__main__":
    # Setup basic logging if running standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)

    # Test the connection monitor
    targets = ["google.com", "8.8.8.8"]

    for target in targets:
        try:
            logger.info(f"Testing {target}")
            monitor = ConnectionMonitor(target)
            results = monitor.collect()
            logger.info(f"\nResults for {target}:")
            logger.info(json.dumps(results, indent=2))
        except Exception as e:
            logger.error(f"Failed to collect metrics for {target}: {str(e)}")
            logger.error(f"Error details: {e.__class__.__name__}")
