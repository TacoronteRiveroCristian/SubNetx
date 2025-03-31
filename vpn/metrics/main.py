"""
Servicio de recolección de métricas para SubNetx VPN.

Este script se encarga de recopilar métricas de rendimiento y disponibilidad
para el servidor VPN y los clientes conectados. Ejecuta comprobaciones
periódicas de ping y guarda los resultados en una base de datos SQLite.

:module: vpn.metrics.main
:author: SubNetx Team
:version: 1.0.1
"""

import logging
import os
import signal
import subprocess
import sys
import time

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore

from vpn.metrics.conf import LOG_FORMAT, LOG_LEVEL

# Configurar logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Variable global para control de ejecución
running = True

def signal_handler(sig, frame):
    """Manejador de señales para terminar limpiamente."""
    global running
    logger.info(f"Recibida señal {sig}, terminando...")
    running = False

def run_ping_check() -> None:
    """Ejecutar la comprobación de ping.

    Esta función llama al script de extracción de datos de ping
    que se encarga de realizar los pings a los objetivos configurados
    y guardar los resultados en la base de datos.
    """
    try:
        script_path = os.path.join("vpn/metrics/collector/src/extract_and_save_ping.py")

        # Asegurar que el script tiene permisos de ejecución
        if os.path.exists(script_path) and not os.access(script_path, os.X_OK):
            os.chmod(script_path, 0o755)

        result = subprocess.run(
            [script_path], capture_output=True, text=True, check=True
        )

        if result.returncode == 0:
            logger.info("Comprobación de ping completada correctamente")
            if result.stdout.strip():  # Solo registrar si hay salida
                logger.debug(result.stdout)
        else:
            logger.error(f"Error en comprobación de ping: {result.stderr}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando comprobación de ping: {e.stderr}")
    except Exception as e:
        logger.error(f"Error inesperado en comprobación de ping: {str(e)}")


def main() -> None:
    """Configurar y ejecutar el servicio de recolección de métricas."""
    logger.info("Iniciando servicio de recolección de métricas de SubNetx")

    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Crear el planificador
    scheduler = BackgroundScheduler()

    # Añadir trabajo de comprobación de ping - ejecutar cada minuto
    scheduler.add_job(
        run_ping_check,
        trigger=IntervalTrigger(minutes=1),
        id="ping_check",
        name="Ejecutar comprobación de ping cada minuto",
        replace_existing=True,
    )

    # Iniciar el planificador
    scheduler.start()
    logger.info("Planificador iniciado correctamente")

    try:
        # Ejecutar una primera comprobación inmediatamente
        logger.info("Ejecutando comprobación inicial...")
        run_ping_check()

        # Mantener el hilo principal vivo
        while running:
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error en el bucle principal: {str(e)}")
    finally:
        # Asegurar que el planificador se detiene limpiamente
        scheduler.shutdown()
        logger.info("Planificador detenido, servicio finalizado")


if __name__ == "__main__":
    main()
