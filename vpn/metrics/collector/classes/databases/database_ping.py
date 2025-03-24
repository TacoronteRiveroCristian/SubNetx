#!/usr/bin/env python3
"""
SubNetx VPN Ping Database

This module provides functionality to store ping monitoring data in a SQLite database.
It handles the persistence of ping metrics collected from network targets, including
latency, packet loss, and connection quality measurements.

Database Schema:
1. ping_targets:
   - id: INTEGER PRIMARY KEY
   - target: TEXT UNIQUE
   - description: TEXT
   - added_at: DATETIME

2. ping_metrics:
   - id: INTEGER PRIMARY KEY
   - target_id: INTEGER FOREIGN KEY
   - timestamp: DATETIME
   - status: TEXT ('online', 'offline', 'timeout')
   - connection_quality: TEXT ('excellent', 'good', 'fair', 'poor', 'none')
   - packet_loss_percent: FLOAT
   - min_rtt: FLOAT
   - avg_rtt: FLOAT
   - max_rtt: FLOAT
   - mdev_rtt: FLOAT
   - packets_transmitted: INTEGER
   - packets_received: INTEGER

3. icmp_details:
   - id: INTEGER PRIMARY KEY
   - ping_metric_id: INTEGER FOREIGN KEY
   - sequence: INTEGER
   - response_time_ms: FLOAT

4. tls_info:
   - id: INTEGER PRIMARY KEY
   - ping_metric_id: INTEGER FOREIGN KEY
   - cert_expiry: DATETIME
   - issuer: TEXT
   - subject: TEXT
   - version: TEXT
   - cipher: TEXT

This design allows for efficient storage and retrieval of ping monitoring data
while maintaining relationships between different aspects of the measurements.
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class PingDatabase:
    """Database manager for VPN ping metrics.

    Handles persistent storage of ping metrics in a SQLite database.
    Designed to efficiently store and retrieve ping monitoring data
    from various targets.

    :param db_path: Path to the SQLite database file
    :type db_path: str
    :ivar db_path: Path to the database file
    :type db_path: str
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the ping database manager.

        If db_path is not provided, creates a database in a 'databases' directory
        within the application's root folder.

        :param db_path: Path to the SQLite database file, defaults to None
        :type db_path: str, optional
        """
        # If no path provided, create a database in the databases directory
        if db_path is None:
            # Create databases directory if it doesn't exist
            db_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "databases",
            )
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "ping_metrics.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            # Create ping_targets table for storing target information
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ping_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT UNIQUE NOT NULL,
                    description TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create ping_metrics table for storing ping results
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ping_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    status TEXT NOT NULL,
                    connection_quality TEXT NOT NULL,
                    packet_loss_percent FLOAT,
                    min_rtt FLOAT,
                    avg_rtt FLOAT,
                    max_rtt FLOAT,
                    mdev_rtt FLOAT,
                    packets_transmitted INTEGER,
                    packets_received INTEGER,
                    raw_output TEXT,
                    FOREIGN KEY (target_id) REFERENCES ping_targets (id)
                )
            """
            )

            # Create icmp_details table for storing individual ping responses
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS icmp_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ping_metric_id INTEGER NOT NULL,
                    sequence INTEGER NOT NULL,
                    response_time_ms FLOAT NOT NULL,
                    FOREIGN KEY (ping_metric_id) REFERENCES ping_metrics (id)
                )
            """
            )

            # Create tls_info table for storing TLS information
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tls_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ping_metric_id INTEGER NOT NULL,
                    cert_expiry DATETIME,
                    issuer TEXT,
                    subject TEXT,
                    version TEXT,
                    cipher TEXT,
                    FOREIGN KEY (ping_metric_id) REFERENCES ping_metrics (id)
                )
            """
            )

            # Create indexes for better performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ping_metrics_target_id ON ping_metrics(target_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ping_metrics_timestamp ON ping_metrics(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ping_metrics_status ON ping_metrics(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_icmp_details_ping_metric_id ON icmp_details(ping_metric_id)"
            )

    def add_target(self, target: str, description: Optional[str] = None) -> int:
        """Add a new ping target or get existing target ID.

        :param target: Target hostname or IP
        :type target: str
        :param description: Optional description of the target
        :type description: str, optional
        :return: ID of the target in the database
        :rtype: int
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Check if target already exists
            cursor = conn.execute(
                "SELECT id FROM ping_targets WHERE target = ?", (target,)
            )

            existing = cursor.fetchone()
            if existing:
                return int(existing["id"])

            # Insert new target
            cursor = conn.execute(
                "INSERT INTO ping_targets (target, description) VALUES (?, ?)",
                (target, description),
            )

            lastrowid = cursor.lastrowid
            if lastrowid is None:
                raise ValueError("Failed to insert target")
            return lastrowid

    def store_ping_result(self, ping_data: Dict[str, Any]) -> int:
        """Store ping monitoring results in the database.

        :param ping_data: Ping data from the PingMonitor
        :type ping_data: Dict[str, Any]
        :return: ID of the inserted ping metric record
        :rtype: int
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Extract primary data
            target = ping_data.get("target")
            if not isinstance(target, str):
                raise ValueError("Target must be a string")
            primary_target_data = ping_data.get("primary_target", {})

            # Get or create target
            target_id = self.add_target(target)

            # Extract values from ping data
            timestamp = primary_target_data.get("timestamp", datetime.now().isoformat())
            status = str(primary_target_data.get("status", "unknown"))
            connection_quality = str(
                primary_target_data.get("connection_quality", "none")
            )
            packet_loss = float(primary_target_data.get("packet_loss_percent", 0))

            # Extract RTT stats
            rtt_stats = primary_target_data.get("rtt_stats", {})
            min_rtt = float(rtt_stats.get("min_ms", 0))
            avg_rtt = float(rtt_stats.get("avg_ms", 0))
            max_rtt = float(rtt_stats.get("max_ms", 0))
            mdev_rtt = float(rtt_stats.get("mdev_ms", 0))

            # Extract packet counts
            packets = primary_target_data.get("packets", {})
            packets_transmitted = int(packets.get("transmitted", 0))
            packets_received = int(packets.get("received", 0))

            # Raw output as JSON
            raw_output = str(primary_target_data.get("raw_output", ""))

            # Insert ping metric record
            cursor = conn.execute(
                """
                INSERT INTO ping_metrics (
                    target_id, timestamp, status, connection_quality,
                    packet_loss_percent, min_rtt, avg_rtt, max_rtt, mdev_rtt,
                    packets_transmitted, packets_received, raw_output
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    target_id,
                    timestamp,
                    status,
                    connection_quality,
                    packet_loss,
                    min_rtt,
                    avg_rtt,
                    max_rtt,
                    mdev_rtt,
                    packets_transmitted,
                    packets_received,
                    raw_output,
                ),
            )

            ping_metric_id = cursor.lastrowid
            if ping_metric_id is None:
                raise ValueError("Failed to insert ping metric")

            # Store ICMP details if available
            icmp_details = primary_target_data.get("icmp_details", [])
            if icmp_details:
                self._store_icmp_details(conn, ping_metric_id, icmp_details)

            # Store TLS info if available
            tls_info = primary_target_data.get("tls_info", {})
            if tls_info:
                self._store_tls_info(conn, ping_metric_id, tls_info)

            return ping_metric_id

    def _store_icmp_details(
        self,
        conn: sqlite3.Connection,
        ping_metric_id: int,
        icmp_details: List[Dict[str, Any]],
    ) -> None:
        """Store ICMP packet details.

        :param conn: SQLite connection
        :type conn: sqlite3.Connection
        :param ping_metric_id: ID of the ping metric record
        :type ping_metric_id: int
        :param icmp_details: List of ICMP packet details
        :type icmp_details: List[Dict[str, Any]]
        """
        for detail in icmp_details:
            sequence = detail.get("sequence", 0)
            response_time = detail.get("response_time_ms", 0)

            conn.execute(
                """
                INSERT INTO icmp_details (ping_metric_id, sequence, response_time_ms)
                VALUES (?, ?, ?)
            """,
                (ping_metric_id, sequence, response_time),
            )

    def _store_tls_info(
        self,
        conn: sqlite3.Connection,
        ping_metric_id: int,
        tls_info: Dict[str, Any],
    ) -> None:
        """Store TLS certificate information.

        :param conn: SQLite connection
        :type conn: sqlite3.Connection
        :param ping_metric_id: ID of the ping metric record
        :type ping_metric_id: int
        :param tls_info: TLS certificate information
        :type tls_info: Dict[str, Any]
        """
        # Extract TLS information and ensure all values are strings or None
        cert_expiry = tls_info.get("cert_expiry")
        issuer = tls_info.get("issuer")
        subject = tls_info.get("subject")
        version = tls_info.get("tls_version")
        cipher = json.dumps(tls_info.get("cipher")) if tls_info.get("cipher") else None

        conn.execute(
            """
            INSERT INTO tls_info (ping_metric_id, cert_expiry, issuer, subject, version, cipher)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (ping_metric_id, cert_expiry, issuer, subject, version, cipher),
        )

    def get_latest_ping(self, target: str) -> Dict[str, Any]:
        """Get the latest ping metrics for a target.

        :param target: Target hostname or IP
        :type target: str
        :return: Latest ping metrics or empty dict if not found
        :rtype: Dict[str, Any]
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT m.* FROM ping_metrics m
                JOIN ping_targets t ON m.target_id = t.id
                WHERE t.target = ?
                ORDER BY m.timestamp DESC
                LIMIT 1
            """,
                (target,),
            )

            row = cursor.fetchone()
            if not row:
                return {}

            result = dict(row)

            # Get ICMP details
            cursor = conn.execute(
                """
                SELECT sequence, response_time_ms
                FROM icmp_details
                WHERE ping_metric_id = ?
                ORDER BY sequence
            """,
                (row["id"],),
            )

            result["icmp_details"] = [dict(row) for row in cursor.fetchall()]

            # Get TLS info
            cursor = conn.execute(
                """
                SELECT cert_expiry, issuer, subject, version, cipher
                FROM tls_info
                WHERE ping_metric_id = ?
            """,
                (row["id"],),
            )

            tls_row = cursor.fetchone()
            if tls_row:
                result["tls_info"] = dict(tls_row)

            return result

    def get_ping_history(
        self, target: str, limit: int = 60, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get ping history for a target.

        :param target: Target hostname or IP
        :type target: str
        :param limit: Maximum number of records to return
        :type limit: int, optional
        :param offset: Offset for pagination
        :type offset: int, optional
        :return: List of ping metrics
        :rtype: List[Dict[str, Any]]
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT m.* FROM ping_metrics m
                JOIN ping_targets t ON m.target_id = t.id
                WHERE t.target = ?
                ORDER BY m.timestamp DESC
                LIMIT ? OFFSET ?
            """,
                (target, limit, offset),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_connection_quality_summary(
        self, target: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Get connection quality summary for a target over a time period.

        :param target: Target hostname or IP
        :type target: str
        :param hours: Number of hours to analyze
        :type hours: int, optional
        :return: Connection quality summary
        :rtype: Dict[str, Any]
        """
        time_threshold = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get counts for each quality level
            cursor = conn.execute(
                """
                SELECT connection_quality, COUNT(*) as count
                FROM ping_metrics m
                JOIN ping_targets t ON m.target_id = t.id
                WHERE t.target = ? AND m.timestamp > ?
                GROUP BY connection_quality
            """,
                (target, time_threshold),
            )

            quality_counts = {
                row["connection_quality"]: row["count"] for row in cursor.fetchall()
            }

            # Get average RTT and packet loss
            cursor = conn.execute(
                """
                SELECT
                    AVG(avg_rtt) as avg_rtt,
                    AVG(packet_loss_percent) as avg_packet_loss,
                    COUNT(*) as total_pings,
                    SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online_count,
                    SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline_count,
                    SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout_count
                FROM ping_metrics m
                JOIN ping_targets t ON m.target_id = t.id
                WHERE t.target = ? AND m.timestamp > ?
            """,
                (target, time_threshold),
            )

            stats = dict(cursor.fetchone())

            # Calculate uptime percentage
            total_pings = stats.get("total_pings", 0)
            if total_pings > 0:
                uptime_percent = (stats.get("online_count", 0) / total_pings) * 100
            else:
                uptime_percent = 0

            return {
                "target": target,
                "period_hours": hours,
                "quality_distribution": quality_counts,
                "avg_rtt_ms": stats.get("avg_rtt", 0),
                "avg_packet_loss_percent": stats.get("avg_packet_loss", 0),
                "uptime_percent": uptime_percent,
                "status_counts": {
                    "online": stats.get("online_count", 0),
                    "offline": stats.get("offline_count", 0),
                    "timeout": stats.get("timeout_count", 0),
                },
                "total_pings": total_pings,
            }

    def delete_old_data(self, days_to_keep: int = 30) -> int:
        """Delete ping data older than the specified number of days.

        :param days_to_keep: Number of days of data to keep
        :type days_to_keep: int, optional
        :return: Number of records deleted
        :rtype: int
        """
        time_threshold = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # First get the IDs of ping metrics to delete
            cursor = conn.execute(
                """
                SELECT id FROM ping_metrics
                WHERE timestamp < ?
            """,
                (time_threshold,),
            )

            metric_ids = [row[0] for row in cursor.fetchall()]

            if not metric_ids:
                return 0

            # Delete related records first (foreign key constraints)
            for metric_id in metric_ids:
                conn.execute(
                    "DELETE FROM icmp_details WHERE ping_metric_id = ?",
                    (metric_id,),
                )
                conn.execute(
                    "DELETE FROM tls_info WHERE ping_metric_id = ?",
                    (metric_id,),
                )

            # Then delete the ping metrics
            cursor = conn.execute(
                "DELETE FROM ping_metrics WHERE id IN ({})".format(
                    ",".join("?" for _ in metric_ids)
                ),
                metric_ids,
            )

            return cursor.rowcount

    def get_all_targets(self) -> List[Dict[str, Any]]:
        """Get a list of all ping targets in the database.

        :return: List of target information
        :rtype: List[Dict[str, Any]]
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT id, target, description, added_at
                FROM ping_targets
                ORDER BY target
            """
            )

            return [dict(row) for row in cursor.fetchall()]


# Standalone testing when script is run directly
if __name__ == "__main__":
    # Setup test database
    db = PingDatabase("test_ping_database.db")

    # Add test data
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "target": "google.com",
        "primary_target": {
            "ip": "8.8.8.8",
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "connection_quality": "excellent",
            "rtt_stats": {
                "min_ms": 20.5,
                "avg_ms": 25.3,
                "max_ms": 30.1,
                "mdev_ms": 2.7,
            },
            "icmp_details": [
                {"sequence": 1, "response_time_ms": 22.5},
                {"sequence": 2, "response_time_ms": 24.8},
                {"sequence": 3, "response_time_ms": 26.3},
                {"sequence": 4, "response_time_ms": 27.6},
            ],
            "packet_loss_percent": 0.0,
            "packets": {"transmitted": 4, "received": 4},
            "raw_output": "PING google.com (8.8.8.8) 56(84) bytes of data...",
            "tls_info": {
                "expiry": "2023-12-31T00:00:00",
                "issuer": "Google Internet Authority",
                "subject": "*.google.com",
            },
        },
    }

    # Store the test data
    metric_id = db.store_ping_result(test_data)
    print(f"Stored test data with ID: {metric_id}")

    # Get the latest ping
    latest = db.get_latest_ping("google.com")
    print(f"Latest ping for google.com: {latest}")

    # Get a summary
    summary = db.get_connection_quality_summary("google.com")
    print(f"Connection quality summary: {json.dumps(summary, indent=2)}")
