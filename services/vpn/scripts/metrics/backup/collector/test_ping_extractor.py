#!/usr/bin/env python3
"""
SubNetx VPN Ping Extractor Test.

Este script realiza pruebas exhaustivas del extractor de ping para verificar
que todos los campos (RTT, paquetes y TLS) se extraen correctamente.
"""

import json
import logging
import sys
from typing import Any, Dict, List, Optional

from vpn.metrics.collector.classes.extractor.ping_extractor import PingExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_ping_extractor(target: str) -> None:
    """
    Prueba exhaustiva del extractor de ping para un objetivo.

    :param target: Nombre de host o IP a probar
    :type target: str
    """
    logger.info(f"=== Iniciando prueba para {target} ===")

    try:
        # Crear extractor y obtener datos
        extractor = PingExtractor(target)
        logger.info(f"Extrayendo datos de ping para {target}...")
        results = extractor.collect()

        # Verificar la estructura del resultado
        if "primary_target" not in results:
            logger.error("ERROR: No se encontró 'primary_target' en los resultados")
            return

        primary_target = results["primary_target"]

        # Verificar estado de conexión
        logger.info(f"Estado de conexión: {primary_target.get('status', 'desconocido')}")
        logger.info(f"Calidad de conexión: {primary_target.get('connection_quality', 'desconocida')}")

        # Verificar RTT (tiempos de respuesta)
        verify_rtt_data(primary_target)

        # Verificar datos de paquetes
        verify_packet_data(primary_target)

        # Verificar detalles ICMP (pings individuales)
        verify_icmp_details(primary_target)

        # Verificar información TLS
        verify_tls_info(primary_target)

        # Mostrar resultado completo en JSON
        logger.info("Resultado completo de la prueba:")
        logger.info(json.dumps(results, indent=2))

    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def verify_rtt_data(data: Dict[str, Any]) -> None:
    """
    Verifica los datos RTT y muestra los resultados.

    :param data: Datos del objetivo primario
    :type data: Dict[str, Any]
    """
    logger.info("--- Verificando datos RTT ---")

    rtt_stats = data.get("rtt_stats", {})
    min_rtt = rtt_stats.get("min_ms")
    avg_rtt = rtt_stats.get("avg_ms")
    max_rtt = rtt_stats.get("max_ms")
    mdev_rtt = rtt_stats.get("mdev_ms")

    logger.info(f"min_rtt: {min_rtt}")
    logger.info(f"avg_rtt: {avg_rtt}")
    logger.info(f"max_rtt: {max_rtt}")
    logger.info(f"mdev_rtt: {mdev_rtt}")

    if min_rtt == 0 and avg_rtt == 0 and max_rtt == 0 and mdev_rtt == 0:
        logger.warning("ADVERTENCIA: Todos los valores RTT son cero")

    if data["status"] == "online" and (min_rtt is None or avg_rtt is None):
        logger.error("ERROR: Estado online pero faltan datos RTT")


def verify_packet_data(data: Dict[str, Any]) -> None:
    """
    Verifica los datos de paquetes y muestra los resultados.

    :param data: Datos del objetivo primario
    :type data: Dict[str, Any]
    """
    logger.info("--- Verificando datos de paquetes ---")

    packets = data.get("packets", {})
    transmitted = packets.get("transmitted", 0)
    received = packets.get("received", 0)
    packet_loss = data.get("packet_loss_percent", 100)

    logger.info(f"Paquetes transmitidos: {transmitted}")
    logger.info(f"Paquetes recibidos: {received}")
    logger.info(f"Pérdida de paquetes: {packet_loss}%")

    if data["status"] == "online" and received == 0:
        logger.error("ERROR: Estado online pero sin paquetes recibidos")

    # Verificación adicional de coherencia
    if received > transmitted:
        logger.error("ERROR: Paquetes recibidos mayor que transmitidos (incoherente)")


def verify_icmp_details(data: Dict[str, Any]) -> None:
    """
    Verifica los detalles ICMP y muestra los resultados.

    :param data: Datos del objetivo primario
    :type data: Dict[str, Any]
    """
    logger.info("--- Verificando detalles ICMP ---")

    icmp_details = data.get("icmp_details", [])
    logger.info(f"Número de respuestas ICMP: {len(icmp_details)}")

    if data["status"] == "online" and not icmp_details:
        logger.warning("ADVERTENCIA: Estado online pero sin detalles ICMP")

    # Mostrar algunos detalles si existen
    if icmp_details:
        logger.info("Primeras respuestas:")
        for i, detail in enumerate(icmp_details[:3]):
            logger.info(f"  Seq {detail.get('sequence')}: {detail.get('response_time_ms')} ms")


def verify_tls_info(data: Dict[str, Any]) -> None:
    """
    Verifica la información TLS y muestra los resultados.

    :param data: Datos del objetivo primario
    :type data: Dict[str, Any]
    """
    logger.info("--- Verificando información TLS ---")

    tls_info = data.get("tls_info")

    if tls_info is None:
        logger.info("No hay información TLS disponible")
        return

    # Verificar campos individuales
    expiry = tls_info.get("expiry")
    issuer = tls_info.get("issuer")
    subject = tls_info.get("subject")
    version = tls_info.get("version")
    cipher = tls_info.get("cipher")

    logger.info(f"Expiración: {expiry or 'N/A'}")
    logger.info(f"Emisor: {issuer or 'N/A'}")
    logger.info(f"Asunto: {subject or 'N/A'}")
    logger.info(f"Versión: {version or 'N/A'}")
    logger.info(f"Cifrado: {cipher or 'N/A'}")

    # Verificación de problema común
    all_none = all(x is None for x in [expiry, issuer, subject, version, cipher])
    if all_none:
        logger.error("ERROR: Todos los campos TLS son None")


def main() -> None:
    """Ejecuta la prueba principal del extractor de ping."""
    logger.info("=== Test de Extractor de Ping SubNetx ===")

    # Usar argumentos de línea de comandos o dominio predeterminado
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["google.com"]

    for target in targets:
        test_ping_extractor(target)
        logger.info("")

    logger.info("Prueba completada")


if __name__ == "__main__":
    main()
