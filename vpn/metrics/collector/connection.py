#!/usr/bin/env python3
"""
SubNetx VPN Connection Monitor

This module provides functionality to monitor VPN connection status,
uptime, and stability metrics. It tracks connection events, calculates
uptime percentages, and analyzes connection patterns.

JSON Response Format:
{
    "timestamp": "ISO-8601 timestamp of the measurement",
    "target": "Target hostname or IP being monitored",
    "status": {
        "connected": "Boolean indicating current connection status",
        "timestamp": "ISO-8601 timestamp of the status check",
        "last_seen": "ISO-8601 timestamp of last successful connection",
        "uptime_percentage": "Percentage of time connected (0-100)",
        "current_session_duration": "Duration of current session in seconds",
        "total_uptime": "Total time connected in seconds",
        "total_downtime": "Total time disconnected in seconds"
    },
    "openvpn_status": {
        "service_available": "Boolean indicating if OpenVPN service is available",
        "is_running": "Boolean indicating if OpenVPN service is running",
        "uptime": "Service uptime in seconds",
        "active_clients": "Number of active VPN clients",
        "tun_interface": "Boolean indicating if TUN interface is active"
    },
    "stability_metrics": {
        "disconnection_count": "Number of disconnections in last 24 hours",
        "average_session_duration": "Average duration of connection sessions",
        "longest_session": "Duration of longest connection session",
        "shortest_session": "Duration of shortest connection session",
        "reconnection_rate": "Average time between reconnections",
        "stability_score": "Overall stability score (0-100)"
    },
    "connection_history": [
        {
            "timestamp": "ISO-8601 timestamp",
            "connected": "Boolean indicating connection status",
            "duration": "Duration of this status in seconds"
        }
    ],
    "database_stats": {
        "total_sessions": "Total number of connection sessions recorded",
        "total_events": "Total number of connection events recorded",
        "last_24h_sessions": "Number of sessions in last 24 hours",
        "last_24h_events": "Number of events in last 24 hours"
    }
}

Metrics Explained:
- status: Current connection state and timing information
  * connected: Real-time connection status
  * uptime_percentage: Overall connection reliability
  * session_duration: Current connection length
- openvpn_status: OpenVPN service health
  * service_availability: Service presence
  * client_count: Active VPN connections
  * interface_status: Network interface state
- stability_metrics: Connection reliability analysis
  * disconnection_count: Frequency of disconnections
  * session_duration: Connection persistence
  * stability_score: Overall reliability rating
- connection_history: Recent status changes
  * Limited to last 100 entries
  * Used for trend analysis
- database_stats: Historical data summary
  * Total and recent session counts
  * Event tracking statistics
"""

import subprocess
import time
import json
import logging
import socket
import os
from datetime import datetime, timedelta
from typing import Dict, Any

from base import BaseMonitor
from ping import PingMonitor
from database import ConnectionDatabase

class ConnectionMonitor(BaseMonitor):
    """Monitor for VPN connection status and stability.

    This class specializes in monitoring VPN connection status, uptime,
    and connection stability metrics. It provides both real-time status
    and historical connection data.

    :param target: Target hostname or IP address to monitor
    :type target: str
    :param db: Connection database instance, or creates a new one if None
    :type db: Optional[ConnectionDatabase]
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
    :ivar db: Database connection for persistent storage
    :type db: ConnectionDatabase
    """

    def __init__(self, target: str, db=None):
        """Initialize the Connection Monitor.

        :param target: Target hostname or IP address to monitor
        :type target: str
        :param db: Connection database instance, creates a new one if None
        :type db: Optional[ConnectionDatabase]
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

        # Use provided database or create a new one
        self.db = db if db else ConnectionDatabase("vpn_metrics.db")

        print(f"Initialized Connection Monitor for {target}")

        # Attempt initial connection check
        self._check_connection()

    def _check_connection(self) -> bool:
        """Check if connection to target is active.

        Updates connection state and history based on current status.
        Records connection/disconnection events in the database.

        Returns:
            bool: True if connected, False otherwise.
        """
        now = datetime.now()
        was_connected = self.is_connected

        # Try to connect to the target
        try:
            # First try with socket to test TCP connectivity
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            # Try to resolve hostname first
            try:
                # Obtain the IP address of the target
                ip = socket.gethostbyname(self.target)
            except socket.gaierror:
                # Can't resolve hostname, might be DNS issue
                ip = self.target

            # Attempt TCP connection to port 80
            result = sock.connect_ex((ip, 80))
            sock.close()

            if result == 0:
                # Connection succeeded
                self.is_connected = True
            else:
                # Fall back to ping if TCP connection fails
                ping_monitor = PingMonitor(self.target)
                ping_result = ping_monitor.ping_target(count=1, timeout=2, quiet=True)
                self.is_connected = ping_result.get('status') == 'online'

        except Exception as e:
            print(f"Connection check error: {e}")
            self.is_connected = False

        # Update connection records
        if self.is_connected:
            # We're connected now
            if not was_connected:
                # This is a new connection event
                print(f"Connection established to {self.target}")
                # Record the connection in the database
                self.db.record_connection(self.target)

        else:
            # We're disconnected
            if was_connected:
                # This is a new disconnection event
                print(f"Connection lost to {self.target}")
                # Record the disconnection in the database
                self.db.record_disconnection(self.target)

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
        """Check OpenVPN service status in Docker container.

        Returns:
            Dict[str, Any]: OpenVPN status information.
        """
        result = {
            'service_available': False,
            'is_running': False,
            'uptime': None,
            'active_clients': 0,
            'tun_interface': False
        }

        try:
            # Verificar el archivo PID
            pid_file = os.getenv('OPENVPN_PID_FILE', '/var/run/openvpn.pid')
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                # Verificar si el proceso existe
                try:
                    subprocess.run(['kill', '-0', pid], check=True)
                    result['is_running'] = True
                    result['service_available'] = True
                except subprocess.CalledProcessError:
                    result['is_running'] = False

            # Verificar la interfaz TUN
            tun_device = os.getenv('TUN_DEVICE', 'tun0')
            try:
                subprocess.run(['ip', 'link', 'show', tun_device], check=True, capture_output=True)
                result['tun_interface'] = True
            except subprocess.CalledProcessError:
                result['tun_interface'] = False

            # Verificar procesos OpenVPN
            try:
                ps_output = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                openvpn_processes = [line for line in ps_output.stdout.split('\n')
                                   if 'openvpn' in line.lower() and 'server.conf' in line]
                result['active_clients'] = len(openvpn_processes)
            except Exception as e:
                print(f"Error checking OpenVPN processes: {e}")

            # Verificar logs de estado si están disponibles
            logs_dir = os.getenv('LOGS_DIR', '/var/log/openvpn')
            status_log = os.path.join(logs_dir, 'status.log')
            if os.path.exists(status_log):
                try:
                    with open(status_log, 'r') as f:
                        status_data = f.read()
                    # Contar clientes activos
                    client_count = sum(1 for line in status_data.split('\n')
                                     if line.startswith('CLIENT_LIST'))
                    result['active_clients'] = client_count
                except Exception as e:
                    print(f"Error reading status log: {e}")

        except Exception as e:
            print(f"Error checking OpenVPN status: {e}")

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
        """Analyze connection stability based on database history.

        Returns:
            Dict[str, Any]: Stability analysis including rating and reasons.
        """
        # Get stability metrics from the database
        stability_metrics = self.db.get_stability_metrics(self.target)

        # Get current connection stats from database
        stats = self.db.get_connection_stats(self.target)

        # Default stability assessment
        stability = {
            'stability': stability_metrics.get('status', 'unknown'),
            'rating': stability_metrics.get('stability_rating', 0),
            'uptime_percentage': stability_metrics.get('uptime_percentage', 0),
            'recent_disconnections': stability_metrics.get('disconnections_24h', 0),
            'reason': 'Insufficient data',
            'recommendations': []
        }

        # Determine reason based on rating
        rating = stability.get('rating', 0)

        if rating >= 99:
            stability['reason'] = 'Consistent uptime with minimal disconnections'
        elif rating >= 95:
            stability['reason'] = 'Generally stable with occasional disconnections'
        elif rating >= 80:
            stability['reason'] = 'Somewhat stable but with periodic disconnections'
        elif rating >= 50:
            stability['reason'] = 'Frequent disconnections affecting service quality'
        else:
            stability['reason'] = 'Severe connection issues affecting service usability'

        # Generate recommendations
        recommendations = []
        if rating < 80:
            recommendations.append('Check network configuration for issues')
        if stability['recent_disconnections'] > 5:
            recommendations.append('Investigate causes of frequent disconnections')
        if rating < 50:
            recommendations.append('Consider alternative VPN routing or connectivity')

        stability['recommendations'] = recommendations

        return stability

    def collect(self) -> Dict[str, Any]:
        """Collect connection metrics and status information.

        Returns:
            Dict[str, Any]: Dictionary with connection metrics.
        """
        try:
            # Start with the basic result structure
            result = self.get_basic_result()

            # Check the current connection status
            current_status = self._check_connection()

            # Get connection stats from database
            db_stats = self.db.get_connection_stats(self.target)

            # Check OpenVPN status if available
            openvpn_status = self._check_openvpn_status()

            # Analyze connection stability based on database history
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

            # Get current connection session info from database
            current_session = db_stats.get('current_session', {})

            # Calculate connection status metrics
            connection_status = {
                'connected': self.is_connected,
                'first_seen': db_stats.get('monitoring_period', {}).get('first_seen'),
                'last_seen': db_stats.get('monitoring_period', {}).get('last_seen'),
                'current_session_start': current_session.get('start_time'),
                'current_session_duration': current_session.get('duration'),
                'current_session_formatted': self._format_uptime(current_session.get('duration')),
                'uptime_seconds': db_stats.get('total_duration', 0),
                'uptime_formatted': self._format_uptime(db_stats.get('total_duration', 0)),
                'uptime_percentage': db_stats.get('uptime_percentage', 0),
                'total_sessions': db_stats.get('total_sessions', 0),
                'disconnection_count': len(db_stats.get('recent_disconnections', []))
            }

            # Build the result
            result.update({
                'status': connection_status,
                'history': {
                    'status_history': self.status_history[-20:],
                    'disconnection_events': db_stats.get('recent_disconnections', [])
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

    # Test the connection monitor with database storage
    targets = ["google.com", "8.8.8.8"]
    db = ConnectionDatabase("vpn_metrics.db")

    for target in targets:
        try:
            logger.info(f"Testing {target}")
            monitor = ConnectionMonitor(target, db=db)

            # Primera verificación
            results = monitor.collect()
            logger.info(f"\nInitial results for {target}:")
            logger.info(json.dumps(results, indent=2))

            # Esperar unos segundos
            time.sleep(5)

            # Segunda verificación
            results = monitor.collect()
            logger.info(f"\nUpdated results for {target}:")
            logger.info(json.dumps(results, indent=2))

            # Obtener estadísticas de la base de datos
            stats = db.get_connection_stats(target)
            logger.info(f"\nDatabase statistics for {target}:")
            logger.info(json.dumps(stats, indent=2))

            # Obtener métricas de estabilidad
            stability = db.get_stability_metrics(target)
            logger.info(f"\nStability metrics for {target}:")
            logger.info(json.dumps(stability, indent=2))

        except Exception as e:
            logger.error(f"Failed to collect metrics for {target}: {str(e)}")
            logger.error(f"Error details: {e.__class__.__name__}")
