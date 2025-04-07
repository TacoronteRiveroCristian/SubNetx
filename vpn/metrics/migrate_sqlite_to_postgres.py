#!/usr/bin/env python3
"""
SubNetx VPN SQLite to PostgreSQL Migration.

Este script migra los datos de la base de datos SQLite existente a PostgreSQL.
Útil para preservar el histórico de métricas al migrar a la nueva infraestructura.
"""

import argparse
import logging
import sys
import time
from typing import Any, Dict, List, Optional

from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
from vpn.metrics.collector.classes.databases.database_ping_postgres import PingDatabasePostgres
from vpn.metrics.conf import LOG_FORMAT, LOG_LEVEL, PING_DB_PATH, POSTGRES_URI

# Configurar logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("migration.log")
    ]
)
logger = logging.getLogger(__name__)


def migrate_data(batch_size: int = 100, dry_run: bool = False) -> None:
    """
    Migrar datos de SQLite a PostgreSQL.

    :param batch_size: Número de registros a migrar por lote
    :type batch_size: int
    :param dry_run: Si es True, no se insertan datos en PostgreSQL
    :type dry_run: bool
    """
    logger.info(f"Iniciando migración de SQLite a PostgreSQL (dry_run={dry_run})")

    # Inicializar bases de datos
    sqlite_db = PingDatabase(PING_DB_PATH)
    postgres_db = PingDatabasePostgres(POSTGRES_URI)

    # Obtener todos los targets de SQLite
    targets = sqlite_db.get_all_targets()
    logger.info(f"Encontrados {len(targets)} targets en SQLite")

    targets_migrated = 0
    records_migrated = 0

    # Para cada target, migrar sus datos
    for target in targets:
        target_name = target['target']
        logger.info(f"Migrando datos para target: {target_name}")

        # Crear el target en PostgreSQL
        if not dry_run:
            postgres_target_id = postgres_db.add_target(
                target_name,
                target.get('description')
            )
            logger.info(f"Target creado en PostgreSQL con ID: {postgres_target_id}")
        else:
            logger.info(f"[DRY RUN] Target {target_name} sería creado en PostgreSQL")

        # Migrar métricas en lotes
        offset = 0
        total_target_metrics = 0

        while True:
            # Obtener lote de métricas
            metrics = sqlite_db.get_ping_history(target_name, limit=batch_size, offset=offset)
            if not metrics:
                break

            logger.info(f"Procesando lote de {len(metrics)} métricas (offset={offset})")

            # Para cada métrica, migrarla a PostgreSQL
            for metric in metrics:
                # Crear el formato esperado por store_ping_result
                ping_data = {
                    "target": target_name,
                    "primary_target": {
                        "timestamp": metric.get('timestamp'),
                        "status": metric.get('status', 'unknown'),
                        "connection_quality": metric.get('connection_quality', 'none'),
                        "packet_loss_percent": metric.get('packet_loss_percent', 0),
                        "rtt_stats": {
                            "min_ms": metric.get('min_rtt', 0),
                            "avg_ms": metric.get('avg_rtt', 0),
                            "max_ms": metric.get('max_rtt', 0),
                            "mdev_ms": metric.get('mdev_rtt', 0)
                        },
                        "packets": {
                            "transmitted": metric.get('packets_transmitted', 0),
                            "received": metric.get('packets_received', 0)
                        },
                        "raw_output": metric.get('raw_output', ''),
                        "icmp_details": metric.get('icmp_details', []),
                        "tls_info": metric.get('tls_info', {})
                    }
                }

                # Almacenar en PostgreSQL
                if not dry_run:
                    try:
                        metric_id = postgres_db.store_ping_result(ping_data)
                        records_migrated += 1
                        total_target_metrics += 1
                    except Exception as e:
                        logger.error(f"Error migrando métrica: {str(e)}")
                else:
                    records_migrated += 1
                    total_target_metrics += 1
                    logger.debug(f"[DRY RUN] Métrica {metric.get('id')} sería migrada")

            # Incrementar offset para el siguiente lote
            offset += batch_size

            # Pequeña pausa para no sobrecargar la BD
            time.sleep(0.1)

        logger.info(f"Migradas {total_target_metrics} métricas para target {target_name}")
        targets_migrated += 1

    logger.info(f"Migración completada: {targets_migrated} targets, {records_migrated} registros")


def main() -> None:
    """Parse command line arguments and run the migration."""
    parser = argparse.ArgumentParser(description="Migrar datos de SQLite a PostgreSQL")
    parser.add_argument(
        "-b", "--batch-size",
        type=int,
        default=100,
        help="Número de registros a migrar por lote"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecutar en modo simulación (no insertar datos)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mostrar información detallada de depuración"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    migrate_data(args.batch_size, args.dry_run)


if __name__ == "__main__":
    main()
