#!/usr/bin/env python3
"""
SubNetx VPN Force Update Metrics.

Este script realiza una actualización forzada de métricas para un objetivo,
ejecutando cada paso del proceso de extracción y almacenamiento.
Útil para verificar que las correcciones funcionan correctamente.
"""

import argparse
import json
import logging
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from vpn.metrics.api.db_adapter import DBAdapter
from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
from vpn.metrics.collector.classes.extractor.ping_extractor import PingExtractor
from vpn.metrics.conf import LOG_LEVEL, PING_DB_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("metrics_update.log")
    ]
)
logger = logging.getLogger(__name__)


def force_update_metrics(targets: List[str], verbose: bool = False, interval: Optional[int] = None) -> None:
    """
    Forzar la actualización de métricas para los objetivos especificados.

    :param targets: Lista de objetivos (hostnames o IPs)
    :type targets: List[str]
    :param verbose: Mostrar información detallada de depuración
    :type verbose: bool
    :param interval: Intervalo en segundos para actualizaciones continuas
    :type interval: Optional[int]
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Inicializar conexión a la base de datos
    logger.info(f"Conectando a la base de datos: {PING_DB_PATH}")
    db = PingDatabase(PING_DB_PATH)

    # Crear adaptador para formatear los datos
    adapter = DBAdapter(db)

    while True:
        # Procesar cada objetivo
        for target in targets:
            logger.info(f"=== Procesando objetivo: {target} ===")

            try:
                # Extraer datos de ping
                logger.info("Ejecutando extracción de ping...")
                extractor = PingExtractor(target)
                results = extractor.collect()

                # 2. Validar resultados
                if verbose:
                    logger.info("Datos extraídos:")
                    primary_target = results.get('primary_target', {})
                    for key, value in primary_target.items():
                        if key == 'icmp_details':
                            logger.info(f"  icmp_details: {len(value)} entradas")
                            for i, detail in enumerate(value):
                                logger.info(f"    {i+1}: seq={detail.get('sequence', '?')}, time={detail.get('response_time_ms', '?')}ms")
                        elif key == 'tls_info':
                            if value:
                                logger.info("  TLS info:")
                                for tls_key, tls_val in value.items():
                                    logger.info(f"    {tls_key}: {tls_val}")
                            else:
                                logger.info("  TLS info: No disponible")
                        else:
                            logger.info(f"  {key}: {value}")

                # Validar integridad de los datos
                validate_results(results)

                # 3. Almacenar en la base de datos
                logger.info("Almacenando datos en la base de datos...")
                metric_id = db.store_ping_result(results)
                logger.info(f"Métrica guardada con ID: {metric_id}")

                # 4. Recuperar de la base de datos para validación
                logger.info("Recuperando últimos datos para validación...")
                # Necesitamos el nombre del target para buscar
                hostname = results.get('target', target)
                latest_metric = db.get_latest_ping(hostname)

                if verbose:
                    logger.info("Métrica recuperada de la base de datos:")
                    for key, value in latest_metric.items():
                        logger.info(f"  {key}: {value}")

                # 5. Formatear para API y validar
                logger.info("Formateando datos para API...")
                # Obtener el ID del objetivo para el formateador
                target_id = latest_metric.get('target_id', 0)
                formatted_metric = adapter._format_metric(latest_metric, target_id)

                if verbose:
                    logger.info("Datos formateados para API:")
                    logger.info(json.dumps(formatted_metric, indent=2, default=str))

                # Verificar que los datos formateados tienen todos los campos esperados
                validate_formatted_data(formatted_metric)

                logger.info("=== Procesamiento completado para: {target} ===\n")

            except Exception as e:
                logger.error(f"Error al procesar {target}: {str(e)}")
                logger.error(traceback.format_exc())

        # Si no hay intervalo, salir después de una iteración
        if not interval:
            break

        # Esperar para la siguiente actualización
        logger.info(f"Esperando {interval} segundos para la siguiente actualización...")
        time.sleep(interval)


def validate_results(results: Dict[str, Any]) -> None:
    """
    Validar la integridad de los resultados extraídos.

    :param results: Resultados a validar
    :type results: Dict[str, Any]
    """
    logger.info("Validando resultados de extracción...")

    if "primary_target" not in results:
        logger.error("Error: No se encontraron datos de objetivo primario")
        return

    primary = results["primary_target"]

    # Verificar datos clave
    required_fields = ['status', 'timestamp']
    for field in required_fields:
        if field not in primary:
            logger.error(f"Campo primario requerido faltante: {field}")

    logger.info(f"  Estado: {primary.get('status', 'desconocido')}")
    logger.info(f"  Calidad: {primary.get('connection_quality', 'desconocida')}")

    # Verificar campos según el estado
    if primary.get('status') == 'online':
        # Verificar RTT
        rtt_stats = primary.get('rtt_stats', {})
        logger.info("  Estadísticas RTT:")
        logger.info(f"    Min: {rtt_stats.get('min_ms', 0)}")
        logger.info(f"    Avg: {rtt_stats.get('avg_ms', 0)}")
        logger.info(f"    Max: {rtt_stats.get('max_ms', 0)}")
        logger.info(f"    Mdev: {rtt_stats.get('mdev_ms', 0)}")

        if all(v == 0 for v in rtt_stats.values()):
            logger.warning("  ⚠️ Todas las estadísticas RTT son cero")

        # Verificar detalles ICMP
        icmp_details = primary.get('icmp_details', [])
        logger.info(f"  Detalles ICMP: {len(icmp_details)} entradas")

        if len(icmp_details) < 5:
            logger.warning(f"  ⚠️ Solo hay {len(icmp_details)} detalles ICMP (se requieren 5)")

    # Verificar TLS si está disponible
    tls_info = primary.get('tls_info', {})
    logger.info("  Información TLS:")

    if tls_info:
        logger.info(f"    Expiración: {tls_info.get('cert_expiry', 'N/A')}")
        logger.info(f"    Emisor: {tls_info.get('issuer', 'N/A')}")
        logger.info(f"    Asunto: {tls_info.get('subject', 'N/A')}")
        logger.info(f"    Versión: {tls_info.get('version', 'N/A')}")
        logger.info(f"    Cifrado: {tls_info.get('cipher', 'N/A')}")

        all_none = all(v is None for v in tls_info.values())
        if all_none:
            logger.warning("  ⚠️ Todos los campos TLS son nulos")
    else:
        logger.warning("  ⚠️ No hay información TLS disponible")


def validate_formatted_data(data: Dict[str, Any]) -> None:
    """
    Validar que los datos formateados para la API tienen todos los campos necesarios.

    :param data: Datos formateados a validar
    :type data: Dict[str, Any]
    """
    logger.info("Validando datos formateados para API...")

    required_fields = [
        'id', 'target_id', 'timestamp', 'status', 'connection_quality',
        'packet_loss_percent', 'min_rtt', 'avg_rtt', 'max_rtt', 'mdev_rtt',
        'packets_transmitted', 'packets_received', 'icmp_details', 'tls_info'
    ]

    for field in required_fields:
        if field not in data:
            logger.error(f"Campo API faltante: {field}")

    # Verificar detalles ICMP
    icmp_details = data.get('icmp_details', [])
    logger.info(f"  Detalles ICMP: {len(icmp_details)} entradas")

    if len(icmp_details) < 5:
        logger.warning(f"  ⚠️ Solo hay {len(icmp_details)} detalles ICMP en API (se requieren 5)")

    # Verificar TLS
    tls_info = data.get('tls_info')
    logger.info("  Información TLS formateada:")

    if tls_info:
        for field, value in tls_info.items():
            logger.info(f"    {field}: {value}")

        if all(v is None for v in tls_info.values()):
            logger.warning("  ⚠️ Todos los campos TLS son nulos en la API")
    else:
        logger.warning("  ⚠️ No hay información TLS en la API")


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(description="Forzar actualización de métricas VPN")
    parser.add_argument(
        "targets", nargs="*", default=["google.com"],
        help="Objetivos a monitorear (hostnames o IPs)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Mostrar información detallada de depuración"
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=0,
        help="Intervalo en segundos para actualización continua (0 = una sola vez)"
    )

    args = parser.parse_args()

    if not args.targets:
        logger.warning("No se proporcionaron objetivos, usando google.com por defecto")

    if args.interval > 0:
        logger.info(f"Modo de actualización continua cada {args.interval} segundos")
        try:
            force_update_metrics(args.targets, args.verbose, args.interval)
        except KeyboardInterrupt:
            logger.info("Actualización continua interrumpida por el usuario")
    else:
        force_update_metrics(args.targets, args.verbose)


if __name__ == "__main__":
    main()
