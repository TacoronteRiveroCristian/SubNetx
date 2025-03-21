#!/usr/bin/env python3
"""
VPN Connection Database Manager

This module provides functionality to store and manage VPN connection metrics
in a SQLite database, including connection events, uptime statistics, and
stability metrics.

Database Schema:
1. connection_events:
   - id: INTEGER PRIMARY KEY
   - timestamp: DATETIME
   - target: TEXT
   - event_type: TEXT ('connected' or 'disconnected')
   - session_duration: FLOAT
   - uptime_percentage: FLOAT

2. connection_sessions:
   - id: INTEGER PRIMARY KEY
   - target: TEXT
   - start_time: DATETIME
   - end_time: DATETIME
   - duration: FLOAT
   - status: TEXT ('active' or 'ended')

3. stability_metrics:
   - id: INTEGER PRIMARY KEY
   - timestamp: DATETIME
   - target: TEXT
   - uptime_percentage: FLOAT
   - stability_rating: INTEGER
   - disconnection_count: INTEGER
   - avg_session_duration: FLOAT
   - monitoring_period: INTEGER

4. target_status:
   - id: INTEGER PRIMARY KEY
   - target: TEXT UNIQUE
   - is_connected: BOOLEAN
   - last_check: DATETIME
   - last_status_change: DATETIME
   - consecutive_status_duration: INTEGER
   - total_uptime: INTEGER
   - total_downtime: INTEGER

JSON Response Formats:

1. get_target_status():
{
    "is_connected": "Boolean indicating current connection status",
    "last_check": "ISO-8601 timestamp of last status check",
    "last_status_change": "ISO-8601 timestamp of last status change",
    "consecutive_status_duration": "Duration of current status in seconds",
    "total_uptime": "Total time connected in seconds",
    "total_downtime": "Total time disconnected in seconds"
}

2. get_connection_stats():
{
    "total_sessions": "Total number of connection sessions",
    "total_events": "Total number of connection events",
    "average_session_duration": "Average duration of sessions in seconds",
    "longest_session": "Duration of longest session in seconds",
    "shortest_session": "Duration of shortest session in seconds",
    "disconnection_count": "Number of disconnections",
    "uptime_percentage": "Percentage of time connected (0-100)",
    "sessions": [
        {
            "start_time": "ISO-8601 timestamp",
            "end_time": "ISO-8601 timestamp",
            "duration": "Duration in seconds",
            "status": "Session status ('active' or 'ended')"
        }
    ]
}

3. get_stability_metrics():
{
    "uptime_percentage": "Percentage of time connected (0-100)",
    "stability_rating": "Overall stability score (0-100)",
    "disconnection_count": "Number of disconnections in monitoring period",
    "avg_session_duration": "Average duration of sessions in seconds",
    "monitoring_period": "Period of monitoring in seconds",
    "reconnection_rate": "Average time between reconnections in seconds",
    "stability_trend": "Trend indicator ('improving', 'stable', 'degrading')"
}

Metrics Explained:
- connection_events: Individual connection/disconnection events
  * Used for detailed event tracking
  * Includes session duration and uptime percentage
- connection_sessions: Complete connection sessions
  * Tracks start and end times
  * Calculates session durations
  * Maintains active/ended status
- stability_metrics: Aggregated stability data
  * Calculates uptime and stability ratings
  * Tracks disconnection patterns
  * Monitors session duration trends
- target_status: Current connection state
  * Real-time connection status
  * Tracks consecutive status duration
  * Maintains total uptime/downtime
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class ConnectionDatabase:
    """Database manager for VPN connection metrics.

    Handles persistent storage of connection events, statistics and metrics
    in a SQLite database.

    :param db_path: Path to the SQLite database file
    :type db_path: str
    :ivar db_path: Path to the database file
    :type db_path: str
    """

    def __init__(self, db_path: str = "vpn_metrics.db"):
        """Initialize the database manager.

        :param db_path: Path to the SQLite database file
        :type db_path: str
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            # Create connection_events table for storing individual events
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connection_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    target TEXT NOT NULL,
                    event_type TEXT NOT NULL,  -- 'connected' or 'disconnected'
                    session_duration FLOAT,     -- duration in seconds
                    uptime_percentage FLOAT
                )
            """)

            # Create connection_sessions table for tracking session durations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connection_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    duration FLOAT,
                    status TEXT DEFAULT 'active'  -- 'active' or 'ended'
                )
            """)

            # Create stability_metrics table for tracking stability over time
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stability_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    target TEXT NOT NULL,
                    uptime_percentage FLOAT,
                    stability_rating INTEGER,
                    disconnection_count INTEGER,
                    avg_session_duration FLOAT,
                    monitoring_period INTEGER  -- period in seconds
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_target ON connection_events(target)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON connection_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_target ON connection_sessions(target)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON connection_sessions(status)")

            # Create target_status table for storing current connection status
            conn.execute("""
                CREATE TABLE IF NOT EXISTS target_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT UNIQUE NOT NULL,
                    is_connected BOOLEAN NOT NULL DEFAULT 0,
                    last_check DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_status_change DATETIME,
                    consecutive_status_duration INTEGER DEFAULT 0,
                    total_uptime INTEGER DEFAULT 0,
                    total_downtime INTEGER DEFAULT 0
                )
            """)

            # Create index for target_status
            conn.execute("CREATE INDEX IF NOT EXISTS idx_target_status ON target_status(target)")

    def record_connection(self, target: str):
        """Record a connection event.

        Creates a new connection session and updates the target status.

        :param target: Target hostname or IP
        :type target: str
        """
        now = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Check if there's already an active session for this target
            cursor = conn.execute("""
                SELECT id FROM connection_sessions
                WHERE target = ? AND status = 'active'
            """, (target,))

            active_session = cursor.fetchone()

            if not active_session:
                # No active session, create a new one
                conn.execute("""
                    INSERT INTO connection_events (target, event_type)
                    VALUES (?, 'connected')
                """, (target,))

                # Create new session
                conn.execute("""
                    INSERT INTO connection_sessions (target, start_time)
                    VALUES (?, ?)
                """, (target, now.isoformat()))

            # Check if target exists in target_status
            cursor = conn.execute("""
                SELECT id, is_connected, last_status_change, consecutive_status_duration
                FROM target_status WHERE target = ?
            """, (target,))

            status_row = cursor.fetchone()

            if status_row:
                # Target exists, update status
                status_id = status_row['id']
                was_connected = bool(status_row['is_connected'])

                if not was_connected:
                    # Status changed from disconnected to connected
                    conn.execute("""
                        UPDATE target_status
                        SET is_connected = 1,
                            last_check = ?,
                            last_status_change = ?,
                            consecutive_status_duration = 0
                        WHERE id = ?
                    """, (now.isoformat(), now.isoformat(), status_id))
                else:
                    # Status still connected, update duration
                    last_change = datetime.fromisoformat(status_row['last_status_change'])
                    duration = (now - last_change).total_seconds() + status_row['consecutive_status_duration']

                    conn.execute("""
                        UPDATE target_status
                        SET last_check = ?,
                            consecutive_status_duration = ?
                        WHERE id = ?
                    """, (now.isoformat(), duration, status_id))
            else:
                # Target doesn't exist, create it
                conn.execute("""
                    INSERT INTO target_status
                    (target, is_connected, last_check, last_status_change)
                    VALUES (?, 1, ?, ?)
                """, (target, now.isoformat(), now.isoformat()))

    def record_disconnection(self, target: str):
        """Record a disconnection event.

        Ends the active connection session and updates the target status.

        :param target: Target hostname or IP
        :type target: str
        """
        now = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Find the active session
            cursor = conn.execute("""
                SELECT id, start_time
                FROM connection_sessions
                WHERE target = ? AND status = 'active'
                ORDER BY start_time DESC LIMIT 1
            """, (target,))

            session = cursor.fetchone()

            if session:
                session_id, start_time = session['id'], session['start_time']
                # Calculate duration
                start = datetime.fromisoformat(start_time)
                duration = (now - start).total_seconds()

                # Update the session
                conn.execute("""
                    UPDATE connection_sessions
                    SET end_time = ?,
                        duration = ?,
                        status = 'ended'
                    WHERE id = ?
                """, (now.isoformat(), duration, session_id))

                # Record the disconnection event
                conn.execute("""
                    INSERT INTO connection_events (target, event_type, session_duration)
                    VALUES (?, 'disconnected', ?)
                """, (target, duration))

            # Update target status
            cursor = conn.execute("""
                SELECT id, is_connected, last_status_change, consecutive_status_duration, total_uptime
                FROM target_status WHERE target = ?
            """, (target,))

            status_row = cursor.fetchone()

            if status_row:
                # Target exists, update status
                status_id = status_row['id']
                was_connected = bool(status_row['is_connected'])

                if was_connected:
                    # Status changed from connected to disconnected
                    last_change = datetime.fromisoformat(status_row['last_status_change'])
                    uptime_duration = (now - last_change).total_seconds() + status_row['consecutive_status_duration']
                    total_uptime = status_row['total_uptime'] + uptime_duration

                    conn.execute("""
                        UPDATE target_status
                        SET is_connected = 0,
                            last_check = ?,
                            last_status_change = ?,
                            consecutive_status_duration = 0,
                            total_uptime = ?
                        WHERE id = ?
                    """, (now.isoformat(), now.isoformat(), total_uptime, status_id))
                else:
                    # Status still disconnected, update duration
                    last_change = datetime.fromisoformat(status_row['last_status_change'])
                    duration = (now - last_change).total_seconds() + status_row['consecutive_status_duration']

                    conn.execute("""
                        UPDATE target_status
                        SET last_check = ?,
                            consecutive_status_duration = ?
                        WHERE id = ?
                    """, (now.isoformat(), duration, status_id))
            else:
                # Target doesn't exist, create it
                conn.execute("""
                    INSERT INTO target_status
                    (target, is_connected, last_check, last_status_change)
                    VALUES (?, 0, ?, ?)
                """, (target, now.isoformat(), now.isoformat()))

    def get_target_status(self, target: str) -> Dict[str, Any]:
        """Get current status and statistics for a target.

        Returns comprehensive status information including connection state,
        durations, and timing information.

        :param target: Target hostname or IP
        :type target: str
        :return: Status information dictionary
        :rtype: Dict[str, Any]
        """
        now = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get target status
            cursor = conn.execute("""
                SELECT * FROM target_status
                WHERE target = ?
            """, (target,))

            status = cursor.fetchone()

            if not status:
                # No status found, return default
                return {
                    'target': target,
                    'is_connected': False,
                    'last_check': now.isoformat(),
                    'consecutive_status_duration': 0,
                    'consecutive_status_formatted': '0s',
                    'total_uptime': 0,
                    'total_uptime_formatted': '0s',
                    'total_downtime': 0,
                    'total_downtime_formatted': '0s',
                    'first_seen': None,
                    'monitoring_period': 0
                }

            # Convert to dictionary and calculate formatted values
            result = dict(status)

            # Calculate current duration based on last status change
            last_change = datetime.fromisoformat(status['last_status_change']) if status['last_status_change'] else now
            current_duration = (now - last_change).total_seconds() + status['consecutive_status_duration']

            # Format durations
            result['consecutive_status_formatted'] = self._format_duration(current_duration)
            result['total_uptime_formatted'] = self._format_duration(status['total_uptime'])
            result['total_downtime_formatted'] = self._format_duration(status['total_downtime'])

            # Get first seen time (first event)
            cursor = conn.execute("""
                SELECT MIN(timestamp) as first_seen
                FROM connection_events
                WHERE target = ?
            """, (target,))

            first_seen = cursor.fetchone()['first_seen']
            result['first_seen'] = first_seen

            # Calculate monitoring period if first seen exists
            if first_seen:
                first_time = datetime.fromisoformat(first_seen)
                monitoring_period = (now - first_time).total_seconds()
                result['monitoring_period'] = monitoring_period
                result['monitoring_period_formatted'] = self._format_duration(monitoring_period)
            else:
                result['monitoring_period'] = 0
                result['monitoring_period_formatted'] = '0s'

            return result

    def get_disconnection_count(self, target: str, period_hours: int = 24) -> int:
        """Get the count of disconnections within a specific period.

        :param target: Target hostname or IP
        :type target: str
        :param period_hours: Period in hours to count disconnections
        :type period_hours: int
        :return: Number of disconnections
        :rtype: int
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM connection_events
                WHERE target = ? AND event_type = 'disconnected'
                AND timestamp >= datetime('now', ?)
            """, (target, f'-{period_hours} hours'))

            return cursor.fetchone()[0]

    def get_connection_stats(self, target: str, days: int = 30) -> Dict[str, Any]:
        """Get connection statistics.

        :param target: Target hostname or IP
        :type target: str
        :param days: Number of days to analyze
        :type days: int
        :return: Dictionary with statistics
        :rtype: Dict[str, Any]
        """
        with sqlite3.connect(self.db_path) as conn:
            # Configure to receive rows as dictionaries
            conn.row_factory = sqlite3.Row

            # Get session statistics
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_sessions,
                    AVG(CASE WHEN duration IS NOT NULL THEN duration ELSE 0 END) as avg_duration,
                    MAX(duration) as max_duration,
                    MIN(CASE WHEN duration IS NOT NULL THEN duration ELSE 0 END) as min_duration,
                    SUM(CASE WHEN duration IS NOT NULL THEN duration ELSE 0 END) as total_duration
                FROM connection_sessions
                WHERE target = ?
                AND start_time >= datetime('now', ?)
            """, (target, f'-{days} days'))

            stats = dict(cursor.fetchone())

            # Get current active session
            cursor = conn.execute("""
                SELECT
                    start_time,
                    CASE
                        WHEN end_time IS NULL THEN
                            ROUND((JULIANDAY('now') - JULIANDAY(start_time)) * 86400)
                        ELSE duration
                    END as current_duration
                FROM connection_sessions
                WHERE target = ? AND status = 'active'
                ORDER BY start_time DESC LIMIT 1
            """, (target,))

            current_session = cursor.fetchone()
            if current_session:
                stats['current_session'] = {
                    'start_time': current_session['start_time'],
                    'duration': current_session['current_duration']
                }

            # Get recent disconnections
            cursor = conn.execute("""
                SELECT
                    ce.timestamp as disconnect_time,
                    ce.session_duration,
                    cs.start_time as session_start
                FROM connection_events ce
                LEFT JOIN connection_sessions cs ON
                    cs.target = ce.target AND
                    cs.end_time = ce.timestamp
                WHERE ce.target = ?
                AND ce.event_type = 'disconnected'
                ORDER BY ce.timestamp DESC
                LIMIT 10
            """, (target,))

            stats['recent_disconnections'] = [dict(row) for row in cursor.fetchall()]

            # Calculate total monitoring time
            cursor = conn.execute("""
                SELECT
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM connection_events
                WHERE target = ?
            """, (target,))

            timespan = cursor.fetchone()
            if timespan and timespan['first_seen'] and timespan['last_seen']:
                first_seen = datetime.fromisoformat(timespan['first_seen'])
                last_seen = datetime.fromisoformat(timespan['last_seen'])
                total_monitored_time = (last_seen - first_seen).total_seconds()
                stats['monitoring_period'] = {
                    'first_seen': timespan['first_seen'],
                    'last_seen': timespan['last_seen'],
                    'total_seconds': total_monitored_time
                }

                # Calculate real uptime
                if total_monitored_time > 0:
                    stats['uptime_percentage'] = (stats['total_duration'] / total_monitored_time) * 100
                else:
                    stats['uptime_percentage'] = 0

            return stats

    def calculate_uptime(self, target: str, days: int = 30) -> float:
        """Calculate uptime percentage.

        :param target: Target hostname or IP
        :type target: str
        :param days: Number of days to analyze
        :type days: int
        :return: Uptime percentage
        :rtype: float
        """
        with sqlite3.connect(self.db_path) as conn:
            # Calculate total time of completed sessions
            cursor = conn.execute("""
                SELECT SUM(duration) as total_uptime
                FROM connection_sessions
                WHERE target = ?
                AND status = 'ended'
                AND start_time >= datetime('now', ?)
            """, (target, f'-{days} days'))

            completed_uptime = cursor.fetchone()[0] or 0

            # Calculate time of active sessions
            cursor = conn.execute("""
                SELECT
                    ROUND(SUM(
                        (JULIANDAY('now') - JULIANDAY(start_time)) * 86400
                    )) as active_time
                FROM connection_sessions
                WHERE target = ?
                AND status = 'active'
                AND start_time >= datetime('now', ?)
            """, (target, f'-{days} days'))

            active_time = cursor.fetchone()[0] or 0

            # Total time of the period
            total_time = days * 24 * 60 * 60  # days to seconds
            total_uptime = completed_uptime + active_time

            return (total_uptime / total_time) * 100 if total_time > 0 else 0

    def get_stability_metrics(self, target: str) -> Dict[str, Any]:
        """Get stability metrics.

        :param target: Target hostname or IP
        :type target: str
        :return: Dictionary with stability metrics
        :rtype: Dict[str, Any]
        """
        uptime = self.calculate_uptime(target)

        # Get target status for detailed metrics
        target_status = self.get_target_status(target)

        # Get disconnection count in the last 24 hours
        disconnections_24h = self.get_disconnection_count(target, 24)

        with sqlite3.connect(self.db_path) as conn:
            # Calculate stability rating
            stability_rating = 100
            if disconnections_24h > 0:
                stability_rating -= min(disconnections_24h * 10, 50)
            if uptime < 99:
                stability_rating -= min((100 - uptime) * 2, 50)

            # Calculate average session duration
            cursor = conn.execute("""
                SELECT AVG(duration) as avg_duration
                FROM connection_sessions
                WHERE target = ? AND status = 'ended'
                AND end_time >= datetime('now', '-24 hours')
            """, (target,))

            avg_duration = cursor.fetchone()[0] or 0

            # Get monitoring period in seconds
            monitoring_period = target_status.get('monitoring_period', 0)

            # Save metrics
            conn.execute("""
                INSERT INTO stability_metrics
                (target, uptime_percentage, stability_rating, disconnection_count,
                avg_session_duration, monitoring_period)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (target, uptime, stability_rating, disconnections_24h, avg_duration, monitoring_period))

            # Return stability metrics
            return {
                'uptime_percentage': uptime,
                'stability_rating': stability_rating,
                'disconnections_24h': disconnections_24h,
                'avg_session_duration': avg_duration,
                'monitoring_period': monitoring_period,
                'monitoring_period_formatted': self._format_duration(monitoring_period),
                'status': 'stable' if stability_rating >= 80 else 'unstable'
            }

    def _format_duration(self, seconds: float) -> str:
        """Format seconds into human readable duration string.

        :param seconds: Duration in seconds
        :type seconds: float
        :return: Formatted duration (e.g. "3d 12h 5m 10s")
        :rtype: str
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
