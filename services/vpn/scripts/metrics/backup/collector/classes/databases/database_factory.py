"""
SubNetx VPN Database Factory.

This module provides a factory function to create the appropriate database
based on available configuration, with preference for PostgreSQL.
"""

import logging
import os
from typing import Any, Dict, Optional, Union

from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
from vpn.metrics.collector.classes.databases.database_ping_postgres import PingDatabasePostgres
from vpn.metrics.conf import PING_DB_PATH, POSTGRES_URI

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """Factory for creating database instances."""

    @staticmethod
    def create_database(use_postgres: Optional[bool] = None) -> Union[PingDatabase, PingDatabasePostgres]:
        """
        Create a database instance based on configuration.

        This factory method will create either a PostgreSQL or SQLite database
        instance, depending on configuration. By default, it will try PostgreSQL
        first and fall back to SQLite if PostgreSQL is not available.

        :param use_postgres: Force using PostgreSQL if True, SQLite if False, or auto-detect if None
        :type use_postgres: Optional[bool]
        :return: A database instance
        :rtype: Union[PingDatabase, PingDatabasePostgres]
        """
        # Check if PostgreSQL should be used
        if use_postgres is None:
            # Auto-detect: try PostgreSQL first, fall back to SQLite
            try:
                # Check if PostgreSQL is available by importing the module
                import psycopg2
                db = PingDatabasePostgres()
                logger.info("Using PostgreSQL database")
                return db
            except ImportError:
                logger.warning("psycopg2 not available, falling back to SQLite")
                return PingDatabase(PING_DB_PATH)
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {str(e)}, falling back to SQLite")
                return PingDatabase(PING_DB_PATH)
        elif use_postgres:
            # Force PostgreSQL
            db = PingDatabasePostgres()
            logger.info("Using PostgreSQL database")
            return db
        else:
            # Force SQLite
            logger.info("Using SQLite database")
            return PingDatabase(PING_DB_PATH)


# Default factory function
create_database = DatabaseFactory.create_database
