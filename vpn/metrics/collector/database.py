#!/usr/bin/env python3
"""
VPN Connection Database Manager

This module provides functionality to store and manage VPN connection metrics
in a SQLite database, including connection events, uptime statistics, and
stability metrics.
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any

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
            # Crear tabla para eventos de conexión
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connection_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    target TEXT NOT NULL,
                    event_type TEXT NOT NULL,  -- 'connected' o 'disconnected'
                    session_duration FLOAT,     -- duración en segundos
                    uptime_percentage FLOAT
                )
            """)

            # Crear tabla para sesiones de conexión
            conn.execute("""
                CREATE TABLE IF NOT EXISTS connection_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    duration FLOAT,
                    status TEXT DEFAULT 'active'  -- 'active' o 'ended'
                )
            """)

            # Crear tabla para métricas de estabilidad
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stability_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    target TEXT NOT NULL,
                    uptime_percentage FLOAT,
                    stability_rating INTEGER,
                    disconnection_count INTEGER,
                    avg_session_duration FLOAT
                )
            """)

            # Crear índices para mejor rendimiento
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_target ON connection_events(target)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON connection_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_target ON connection_sessions(target)")

    def record_connection(self, target: str):
        """Registrar un evento de conexión.

        :param target: Target hostname o IP
        :type target: str
        """
        with sqlite3.connect(self.db_path) as conn:
            # Registrar el evento
            conn.execute("""
                INSERT INTO connection_events (target, event_type)
                VALUES (?, 'connected')
            """, (target,))

            # Crear nueva sesión
            conn.execute("""
                INSERT INTO connection_sessions (target, start_time)
                VALUES (?, CURRENT_TIMESTAMP)
            """, (target,))

    def record_disconnection(self, target: str):
        """Registrar un evento de desconexión.

        :param target: Target hostname o IP
        :type target: str
        """
        with sqlite3.connect(self.db_path) as conn:
            # Encontrar la sesión activa
            cursor = conn.execute("""
                SELECT id, start_time
                FROM connection_sessions
                WHERE target = ? AND status = 'active'
                ORDER BY start_time DESC LIMIT 1
            """, (target,))
            session = cursor.fetchone()

            if session:
                session_id, start_time = session
                # Calcular duración
                start = datetime.fromisoformat(start_time)
                duration = (datetime.now() - start).total_seconds()

                # Actualizar la sesión
                conn.execute("""
                    UPDATE connection_sessions
                    SET end_time = CURRENT_TIMESTAMP,
                        duration = ?,
                        status = 'ended'
                    WHERE id = ?
                """, (duration, session_id))

                # Registrar el evento de desconexión
                conn.execute("""
                    INSERT INTO connection_events (target, event_type, session_duration)
                    VALUES (?, 'disconnected', ?)
                """, (target, duration))

    def get_connection_stats(self, target: str, days: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas de conexión.

        :param target: Target hostname o IP
        :type target: str
        :param days: Número de días a analizar
        :type days: int
        :return: Diccionario con estadísticas
        :rtype: Dict[str, Any]
        """
        with sqlite3.connect(self.db_path) as conn:
            # Configurar para recibir filas como diccionarios
            conn.row_factory = sqlite3.Row

            # Obtener estadísticas de sesiones
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

            # Obtener última sesión activa
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

            # Obtener últimas desconexiones
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

            # Calcular tiempo total de monitoreo
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

                # Calcular uptime real
                if total_monitored_time > 0:
                    stats['uptime_percentage'] = (stats['total_duration'] / total_monitored_time) * 100
                else:
                    stats['uptime_percentage'] = 0

            return stats

    def calculate_uptime(self, target: str, days: int = 30) -> float:
        """Calcular porcentaje de uptime.

        :param target: Target hostname o IP
        :type target: str
        :param days: Número de días a analizar
        :type days: int
        :return: Porcentaje de uptime
        :rtype: float
        """
        with sqlite3.connect(self.db_path) as conn:
            # Calcular tiempo total de sesiones completadas
            cursor = conn.execute("""
                SELECT SUM(duration) as total_uptime
                FROM connection_sessions
                WHERE target = ?
                AND status = 'ended'
                AND start_time >= datetime('now', ?)
            """, (target, f'-{days} days'))

            completed_uptime = cursor.fetchone()[0] or 0

            # Calcular tiempo de sesiones activas
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

            # Tiempo total del período
            total_time = days * 24 * 60 * 60  # días a segundos
            total_uptime = completed_uptime + active_time

            return (total_uptime / total_time) * 100 if total_time > 0 else 0

    def get_stability_metrics(self, target: str) -> Dict[str, Any]:
        """Obtener métricas de estabilidad.

        :param target: Target hostname o IP
        :type target: str
        :return: Diccionario con métricas de estabilidad
        :rtype: Dict[str, Any]
        """
        uptime = self.calculate_uptime(target)

        with sqlite3.connect(self.db_path) as conn:
            # Contar desconexiones recientes
            cursor = conn.execute("""
                SELECT COUNT(*)
                FROM connection_events
                WHERE target = ?
                AND event_type = 'disconnected'
                AND timestamp >= datetime('now', '-24 hours')
            """, (target,))

            disconnections_24h = cursor.fetchone()[0]

            # Calcular rating de estabilidad
            stability_rating = 100
            if disconnections_24h > 0:
                stability_rating -= min(disconnections_24h * 10, 50)
            if uptime < 99:
                stability_rating -= min((100 - uptime) * 2, 50)

            # Guardar métricas
            conn.execute("""
                INSERT INTO stability_metrics
                (target, uptime_percentage, stability_rating, disconnection_count)
                VALUES (?, ?, ?, ?)
            """, (target, uptime, stability_rating, disconnections_24h))

            return {
                'uptime_percentage': uptime,
                'stability_rating': stability_rating,
                'disconnections_24h': disconnections_24h,
                'status': 'stable' if stability_rating >= 80 else 'unstable'
            }
