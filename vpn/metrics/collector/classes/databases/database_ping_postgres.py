"""
SubNetx VPN Ping Database for PostgreSQL.

This module provides functionality to store ping monitoring data in a PostgreSQL database.
It handles the persistence of ping metrics collected from network targets, including
latency, packet loss, and connection quality measurements.

Database Schema:
1. ping_targets:
   - id: SERIAL PRIMARY KEY
   - target: TEXT UNIQUE
   - description: TEXT
   - added_at: TIMESTAMP DEFAULT NOW()

2. ping_metrics:
   - id: SERIAL PRIMARY KEY
   - target_id: INTEGER REFERENCES ping_targets(id)
   - timestamp: TIMESTAMP
   - status: TEXT ('online', 'offline', 'timeout')
   - connection_quality: TEXT ('excellent', 'good', 'fair', 'poor', 'none')
   - packet_loss_percent: FLOAT
   - min_rtt: FLOAT
   - avg_rtt: FLOAT
   - max_rtt: FLOAT
   - mdev_rtt: FLOAT
   - packets_transmitted: INTEGER
   - packets_received: INTEGER
   - raw_output: TEXT

3. icmp_details:
   - id: SERIAL PRIMARY KEY
   - ping_metric_id: INTEGER REFERENCES ping_metrics(id)
   - sequence: INTEGER
   - response_time_ms: FLOAT

4. tls_info:
   - id: SERIAL PRIMARY KEY
   - ping_metric_id: INTEGER REFERENCES ping_metrics(id)
   - cert_expiry: TIMESTAMP
   - issuer: TEXT
   - subject: TEXT
   - version: TEXT
   - cipher: TEXT

This design allows for efficient storage and retrieval of ping monitoring data
while maintaining relationships between different aspects of the measurements.
"""

import json
import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, RealDictRow
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

from vpn.metrics.conf import POSTGRES_URI

logger = logging.getLogger(__name__)


class PingDatabasePostgres:
    """Database manager for VPN ping metrics using PostgreSQL.

    Handles persistent storage of ping metrics in a PostgreSQL database.
    Designed to efficiently store and retrieve ping monitoring data
    from various targets.

    :param conn_string: Connection string to PostgreSQL database
    :type conn_string: str
    :ivar conn_string: Connection string to the database
    :type conn_string: str
    """

    def __init__(self, conn_string: Optional[str] = None) -> None:
        """Initialize the ping database manager.

        If conn_string is not provided, uses the default from conf.py

        :param conn_string: Connection string to PostgreSQL database, defaults to None
        :type conn_string: str, optional
        """
        self.conn_string = conn_string or POSTGRES_URI
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database tables if they don't exist."""
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor() as cursor:
                # Create ping_targets table for storing target information
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ping_targets (
                        id SERIAL PRIMARY KEY,
                        target TEXT UNIQUE NOT NULL,
                        description TEXT,
                        added_at TIMESTAMP DEFAULT NOW()
                    )
                """)

                # Create ping_metrics table for storing ping results
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ping_metrics (
                        id SERIAL PRIMARY KEY,
                        target_id INTEGER NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
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
                """)

                # Create icmp_details table for storing individual ping responses
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS icmp_details (
                        id SERIAL PRIMARY KEY,
                        ping_metric_id INTEGER NOT NULL,
                        sequence INTEGER NOT NULL,
                        response_time_ms FLOAT NOT NULL,
                        FOREIGN KEY (ping_metric_id) REFERENCES ping_metrics (id)
                    )
                """)

                # Create tls_info table for storing TLS information
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tls_info (
                        id SERIAL PRIMARY KEY,
                        ping_metric_id INTEGER NOT NULL,
                        cert_expiry TIMESTAMP,
                        issuer TEXT,
                        subject TEXT,
                        version TEXT,
                        cipher TEXT,
                        FOREIGN KEY (ping_metric_id) REFERENCES ping_metrics (id)
                    )
                """)

                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ping_metrics_target_id
                    ON ping_metrics(target_id)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ping_metrics_timestamp
                    ON ping_metrics(timestamp)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ping_metrics_status
                    ON ping_metrics(status)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_icmp_details_ping_metric_id
                    ON icmp_details(ping_metric_id)
                """)

            conn.commit()

    def add_target(self, target: str, description: Optional[str] = None) -> int:
        """Add a new ping target or get existing target ID.

        :param target: Target hostname or IP
        :type target: str
        :param description: Optional description of the target
        :type description: str, optional
        :return: ID of the target in the database
        :rtype: int
        """
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if target already exists
                cursor.execute(
                    "SELECT id FROM ping_targets WHERE target = %s", (target,)
                )
                existing = cursor.fetchone()

                if existing:
                    return int(existing["id"])

                # Insert new target
                cursor.execute(
                    "INSERT INTO ping_targets (target, description) VALUES (%s, %s) RETURNING id",
                    (target, description)
                )
                result = cursor.fetchone()

                if result is None or "id" not in result:
                    raise ValueError("Failed to insert target")

                return int(result["id"])

    def store_ping_result(self, ping_data: Dict[str, Any]) -> int:
        """Store ping monitoring results in the database.

        :param ping_data: Ping data from the PingMonitor
        :type ping_data: Dict[str, Any]
        :return: ID of the inserted ping metric record
        :rtype: int
        """
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Extract primary data
                target = ping_data.get("target")
                if not isinstance(target, str):
                    raise ValueError("Target must be a string")
                primary_target_data = ping_data.get("primary_target", {})

                # Get or create target
                target_id = self.add_target(target)

                # Extract values from ping data
                timestamp = primary_target_data.get(
                    "timestamp", datetime.now().isoformat()
                )
                status = str(primary_target_data.get("status", "unknown"))
                connection_quality = str(
                    primary_target_data.get("connection_quality", "none")
                )
                packet_loss = float(
                    primary_target_data.get("packet_loss_percent", 0)
                )

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
                cursor.execute("""
                    INSERT INTO ping_metrics (
                        target_id, timestamp, status, connection_quality,
                        packet_loss_percent, min_rtt, avg_rtt, max_rtt, mdev_rtt,
                        packets_transmitted, packets_received, raw_output
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
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
                ))

                result = cursor.fetchone()
                if result is None or "id" not in result:
                    raise ValueError("Failed to insert ping metric")

                ping_metric_id = int(result["id"])

                # Store ICMP details if available
                icmp_details = primary_target_data.get("icmp_details", [])
                if icmp_details:
                    self._store_icmp_details(conn, ping_metric_id, icmp_details)

                # Store TLS info if available
                tls_info = primary_target_data.get("tls_info", {})
                if tls_info:
                    self._store_tls_info(conn, ping_metric_id, tls_info)

                conn.commit()
                return ping_metric_id

    def _store_icmp_details(
        self,
        conn: psycopg2.extensions.connection,
        ping_metric_id: int,
        icmp_details: List[Dict[str, Any]],
    ) -> None:
        """Store ICMP packet details.

        :param conn: PostgreSQL connection
        :type conn: psycopg2.extensions.connection
        :param ping_metric_id: ID of the ping metric record
        :type ping_metric_id: int
        :param icmp_details: List of ICMP packet details
        :type icmp_details: List[Dict[str, Any]]
        """
        with conn.cursor() as cursor:
            for detail in icmp_details:
                sequence = detail.get("sequence", 0)
                response_time = detail.get("response_time_ms", 0)

                cursor.execute("""
                    INSERT INTO icmp_details (ping_metric_id, sequence, response_time_ms)
                    VALUES (%s, %s, %s)
                """, (ping_metric_id, sequence, response_time))

    def _store_tls_info(
        self,
        conn: psycopg2.extensions.connection,
        ping_metric_id: int,
        tls_info: Dict[str, Any],
    ) -> None:
        """Store TLS certificate information.

        :param conn: PostgreSQL connection
        :type conn: psycopg2.extensions.connection
        :param ping_metric_id: ID of the ping metric record
        :type ping_metric_id: int
        :param tls_info: TLS certificate information
        :type tls_info: Dict[str, Any]
        """
        # Extract TLS information and ensure all values are strings or None
        cert_expiry = tls_info.get("expiry")
        issuer = tls_info.get("issuer")
        subject = tls_info.get("subject")
        version = tls_info.get("version")
        cipher = tls_info.get("cipher")

        with conn.cursor() as cursor:
            # Store TLS information in database
            cursor.execute("""
                INSERT INTO tls_info (ping_metric_id, cert_expiry, issuer, subject, version, cipher)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (ping_metric_id, cert_expiry, issuer, subject, version, cipher))

    def get_latest_ping(self, target: str) -> Dict[str, Any]:
        """Get the latest ping metrics for a target.

        :param target: Target hostname or IP
        :type target: str
        :return: Latest ping metrics or empty dict if not found
        :rtype: Dict[str, Any]
        """
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT m.* FROM ping_metrics m
                    JOIN ping_targets t ON m.target_id = t.id
                    WHERE t.target = %s
                    ORDER BY m.timestamp DESC
                    LIMIT 1
                """, (target,))

                row = cursor.fetchone()
                if not row:
                    return {}

                result = dict(row)

                # Get ICMP details
                cursor.execute("""
                    SELECT sequence, response_time_ms
                    FROM icmp_details
                    WHERE ping_metric_id = %s
                    ORDER BY sequence
                """, (row["id"],))

                result["icmp_details"] = [dict(row) for row in cursor.fetchall()]

                # Get TLS info
                cursor.execute("""
                    SELECT cert_expiry, issuer, subject, version, cipher
                    FROM tls_info
                    WHERE ping_metric_id = %s
                """, (row["id"],))

                tls_row = cursor.fetchone()
                result["tls_info"] = dict(tls_row) if tls_row else {}

                # Convert decimal to float for JSON serialization
                self._convert_decimal_to_float(result)

                return result

    def _convert_decimal_to_float(self, data: Dict[str, Any]) -> None:
        """Convert Decimal objects to float for JSON serialization.

        :param data: Dictionary containing possibly Decimal values
        :type data: Dict[str, Any]
        """
        import decimal
        for key, value in data.items():
            if isinstance(value, decimal.Decimal):
                data[key] = float(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._convert_decimal_to_float(item)
            elif isinstance(value, dict):
                self._convert_decimal_to_float(value)

    def get_ping_history(
        self, target: str, limit: int = 60, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get ping metrics history for a target.

        :param target: Target hostname or IP
        :type target: str
        :param limit: Maximum number of records to return
        :type limit: int
        :param offset: Offset for pagination
        :type offset: int
        :return: List of ping metrics
        :rtype: List[Dict[str, Any]]
        """
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT m.* FROM ping_metrics m
                    JOIN ping_targets t ON m.target_id = t.id
                    WHERE t.target = %s
                    ORDER BY m.timestamp DESC
                    LIMIT %s OFFSET %s
                """, (target, limit, offset))

                rows = cursor.fetchall()
                results = []

                for row in rows:
                    metric = dict(row)

                    # Get ICMP details
                    cursor.execute("""
                        SELECT sequence, response_time_ms
                        FROM icmp_details
                        WHERE ping_metric_id = %s
                        ORDER BY sequence
                    """, (row["id"],))

                    metric["icmp_details"] = [dict(r) for r in cursor.fetchall()]

                    # Get TLS info
                    cursor.execute("""
                        SELECT cert_expiry, issuer, subject, version, cipher
                        FROM tls_info
                        WHERE ping_metric_id = %s
                    """, (row["id"],))

                    tls_row = cursor.fetchone()
                    metric["tls_info"] = dict(tls_row) if tls_row else {}

                    # Convert decimal to float for JSON serialization
                    self._convert_decimal_to_float(metric)
                    results.append(metric)

                return results

    def get_connection_quality_summary(
        self, target: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Get connection quality summary for a target.

        :param target: Target hostname or IP
        :type target: str
        :param hours: Number of hours to analyze
        :type hours: int
        :return: Connection quality summary
        :rtype: Dict[str, Any]
        """
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Calculate cutoff time
                cutoff = datetime.now() - timedelta(hours=hours)

                # Get target ID
                cursor.execute(
                    "SELECT id FROM ping_targets WHERE target = %s", (target,)
                )
                target_row = cursor.fetchone()
                if not target_row:
                    return {}

                target_id = target_row["id"]

                # Count by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM ping_metrics
                    WHERE target_id = %s AND timestamp > %s
                    GROUP BY status
                """, (target_id, cutoff))

                status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
                total_records = sum(status_counts.values())

                # Count by connection quality
                cursor.execute("""
                    SELECT connection_quality, COUNT(*) as count
                    FROM ping_metrics
                    WHERE target_id = %s AND timestamp > %s
                    GROUP BY connection_quality
                """, (target_id, cutoff))

                quality_counts = {row["connection_quality"]: row["count"] for row in cursor.fetchall()}

                # Calculate average RTT stats
                cursor.execute("""
                    SELECT
                        AVG(min_rtt) as avg_min_rtt,
                        AVG(avg_rtt) as avg_avg_rtt,
                        AVG(max_rtt) as avg_max_rtt,
                        MIN(min_rtt) as lowest_min_rtt,
                        MAX(max_rtt) as highest_max_rtt
                    FROM ping_metrics
                    WHERE target_id = %s AND timestamp > %s AND status = 'online'
                """, (target_id, cutoff))

                rtt_row = cursor.fetchone()
                rtt_stats = dict(rtt_row) if rtt_row else {}

                # Calculate average packet loss
                cursor.execute("""
                    SELECT AVG(packet_loss_percent) as avg_packet_loss
                    FROM ping_metrics
                    WHERE target_id = %s AND timestamp > %s
                """, (target_id, cutoff))

                loss_row = cursor.fetchone()
                avg_packet_loss = loss_row["avg_packet_loss"] if loss_row and loss_row["avg_packet_loss"] is not None else 0

                # Build the summary
                summary = {
                    "target": target,
                    "period_hours": hours,
                    "total_records": total_records,
                    "status_counts": status_counts,
                    "quality_counts": quality_counts,
                    "rtt_stats": rtt_stats,
                    "avg_packet_loss": avg_packet_loss,
                    "uptime_percent": (status_counts.get("online", 0) / total_records * 100) if total_records > 0 else 0
                }

                # Convert decimal to float for JSON serialization
                self._convert_decimal_to_float(summary)

                return summary

    def delete_old_data(self, days_to_keep: int = 30) -> int:
        """Delete old ping metrics data.

        :param days_to_keep: Number of days to keep data
        :type days_to_keep: int
        :return: Number of deleted records
        :rtype: int
        """
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor() as cursor:
                # Calculate cutoff date
                cutoff = datetime.now() - timedelta(days=days_to_keep)

                # Get IDs of metrics to delete
                cursor.execute("""
                    SELECT id FROM ping_metrics
                    WHERE timestamp < %s
                """, (cutoff,))

                metric_ids = [row[0] for row in cursor.fetchall()]
                deleted_count = len(metric_ids)

                if deleted_count > 0:
                    # Delete related ICMP details
                    placeholders = ','.join(['%s'] * len(metric_ids))
                    cursor.execute(f"""
                        DELETE FROM icmp_details
                        WHERE ping_metric_id IN ({placeholders})
                    """, metric_ids)

                    # Delete related TLS information
                    cursor.execute(f"""
                        DELETE FROM tls_info
                        WHERE ping_metric_id IN ({placeholders})
                    """, metric_ids)

                    # Delete ping metrics
                    cursor.execute(f"""
                        DELETE FROM ping_metrics
                        WHERE id IN ({placeholders})
                    """, metric_ids)

                    conn.commit()

                return deleted_count

    def get_all_targets(self) -> List[Dict[str, Any]]:
        """Get all monitored targets.

        :return: List of all targets
        :rtype: List[Dict[str, Any]]
        """
        with psycopg2.connect(self.conn_string) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, target, description, added_at
                    FROM ping_targets
                    ORDER BY added_at DESC
                """)

                return [dict(row) for row in cursor.fetchall()]
