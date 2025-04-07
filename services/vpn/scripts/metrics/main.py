"""
Servicio de recolección de métricas para SubNetx VPN.

Este script se encarga de recopilar métricas de rendimiento y disponibilidad
para el servidor VPN y los clientes conectados. Ejecuta comprobaciones
periódicas de ping y guarda los resultados en una base de datos.

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
import json

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore

from vpn.metrics.conf import LOG_FORMAT, LOG_LEVEL, WORK_DIR
from vpn.metrics.collector.classes.databases.database_factory import create_database

# Configurar logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Variable global para control de ejecución
running = True

def init_database():
    """Inicializar la base de datos."""
    try:
        logger.info("Inicializando conexión a la base de datos...")
        db = create_database()
        logger.info("Conexión a la base de datos inicializada correctamente")
        return db
    except Exception as e:
        logger.error(f"Error inicializando la base de datos: {str(e)}")
        return None

def init_vpn_clients_file():
    """Inicializar el archivo de configuración de clientes VPN si no existe."""
    config_path = os.path.join(WORK_DIR, "collector", "config", "vpn_clients.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    if not os.path.exists(config_path):
        logger.info(f"Creating initial VPN clients configuration file at {config_path}")
        # Crear un archivo vacío con la estructura correcta
        data = {"clients": []}
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=4)
    else:
        logger.info(f"VPN clients configuration file already exists at {config_path}")

    # Si hay clientes OpenVPN configurados, añadirlos al archivo
    try:
        # Listar clientes usando el comando
        result = subprocess.run(
            ["/app/scripts/client/openvpn-client-list.sh"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            # Leer el archivo existente
            with open(config_path, 'r') as f:
                data = json.load(f)

            # Obtener los nombres de clientes ya registrados
            existing_clients = [c.get('name') for c in data.get('clients', [])]

            # Procesar la salida para obtener los clientes
            clients_found = 0
            for line in result.stdout.strip().split('\n'):
                client_name = line.strip()
                if client_name and client_name not in existing_clients:
                    # Obtener la IP del archivo CCD
                    ccd_file = f"/etc/openvpn/ccd/{client_name}"
                    if os.path.exists(ccd_file):
                        with open(ccd_file, 'r') as f:
                            ccd_content = f.read()
                            import re
                            ip_match = re.search(r'ifconfig-push\s+(\d+\.\d+\.\d+\.\d+)', ccd_content)
                            if ip_match:
                                ip = ip_match.group(1)
                                # Añadir el cliente a la lista
                                data['clients'].append({
                                    "name": client_name,
                                    "ip": ip,
                                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S.000000", time.gmtime())
                                })
                                clients_found += 1

            # Si se encontraron nuevos clientes, actualizar el archivo
            if clients_found > 0:
                logger.info(f"Found {clients_found} OpenVPN clients to add to monitoring")
                with open(config_path, 'w') as f:
                    json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error initializing VPN clients from OpenVPN configuration: {str(e)}")

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

    # Inicializar la base de datos
    db = init_database()
    if db is None:
        logger.error("No se pudo inicializar la base de datos. Terminando...")
        return

    # Inicializar archivo de configuración de clientes VPN
    init_vpn_clients_file()

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
