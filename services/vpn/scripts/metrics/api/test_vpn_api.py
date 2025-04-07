#!/usr/bin/env python3
"""
Script de prueba para la API de gestión de SubNetx VPN.

Este script proporciona funciones para probar los endpoints de la API
de gestión de VPN, incluyendo configuración, inicio, parada y gestión
de clientes OpenVPN.

El script verifica primero si la API está en ejecución y luego permite
realizar diversas operaciones a través de los endpoints expuestos.

:module: vpn.metrics.api.test_vpn_api
:author: SubNetx Team
:version: 1.0.0
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# URL base de la API
BASE_URL = "http://localhost:8000"

def check_api_running() -> bool:
    """Verifica si la API está en ejecución.

    Returns:
        bool: True si la API está en ejecución, False en caso contrario
    """
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def print_section(title: str) -> None:
    """Imprime un título de sección formateado.

    Args:
        title: Título de la sección
    """
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)

def print_json(data: Dict[str, Any]) -> None:
    """Imprime datos en formato JSON con formato legible.

    Args:
        data: Datos a imprimir
    """
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_server_status() -> None:
    """Prueba el endpoint de estado del servidor OpenVPN."""
    print_section("Prueba de estado del servidor OpenVPN")
    try:
        response = requests.get(f"{BASE_URL}/api/vpn/status")
        if response.status_code == 200:
            print(f"Estado del servidor OpenVPN: {response.status_code} OK")
            print_json(response.json())
        else:
            print(f"Error al obtener estado del servidor: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

def test_server_setup() -> None:
    """Prueba el endpoint de configuración del servidor OpenVPN."""
    print_section("Prueba de configuración del servidor OpenVPN")

    # Obtener información de configuración del usuario
    print("Por favor, proporciona la información para configurar el servidor OpenVPN:")
    vpn_network = input("Dirección de red VPN (ej. 10.8.0.0): ").strip() or "10.8.0.0"
    vpn_netmask = input("Máscara de red VPN (ej. 255.255.255.0): ").strip() or "255.255.255.0"
    openvpn_port = input("Puerto OpenVPN (1-65535): ").strip() or "1194"
    openvpn_proto = input("Protocolo (udp/tcp): ").strip().lower() or "udp"
    tun_device = input("Dispositivo TUN (ej. tun0): ").strip() or "tun0"
    public_ip = input("IP pública o dominio: ").strip() or "localhost"

    # Nota: El token DuckDNS debe configurarse en el archivo .env del servidor
    # y no a través de la API por seguridad

    # Crear payload para la solicitud
    payload = {
        "vpn_network": vpn_network,
        "vpn_netmask": vpn_netmask,
        "openvpn_port": int(openvpn_port),
        "openvpn_proto": openvpn_proto,
        "tun_device": tun_device,
        "public_ip": public_ip
    }

    try:
        print("\nEnviando solicitud de configuración...")
        response = requests.post(
            f"{BASE_URL}/api/vpn/setup",
            json=payload
        )

        if response.status_code == 200:
            print(f"Configuración del servidor completada: {response.status_code} OK")
            print_json(response.json())
        else:
            print(f"Error al configurar el servidor: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

def test_server_start() -> None:
    """Prueba el endpoint de inicio del servidor OpenVPN."""
    print_section("Prueba de inicio del servidor OpenVPN")
    try:
        response = requests.post(f"{BASE_URL}/api/vpn/start")
        if response.status_code == 200:
            print(f"Inicio del servidor completado: {response.status_code} OK")
            print_json(response.json())
        else:
            print(f"Error al iniciar el servidor: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

def test_server_stop() -> None:
    """Prueba el endpoint de parada del servidor OpenVPN."""
    print_section("Prueba de parada del servidor OpenVPN")
    try:
        response = requests.post(f"{BASE_URL}/api/vpn/stop")
        if response.status_code == 200:
            print(f"Parada del servidor completada: {response.status_code} OK")
            print_json(response.json())
        else:
            print(f"Error al detener el servidor: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

def test_client_create() -> None:
    """Prueba el endpoint de creación de cliente OpenVPN."""
    print_section("Prueba de creación de cliente OpenVPN")

    # Obtener información del cliente
    print("Por favor, proporciona la información para crear el cliente OpenVPN:")
    client_name = input("Nombre del cliente: ").strip()
    client_ip = input("IP del cliente (ej. 10.8.0.10): ").strip()

    # Validar entrada
    if not client_name or not client_ip:
        print("Se requiere tanto el nombre como la IP del cliente.")
        return

    # Crear payload para la solicitud
    payload = {
        "name": client_name,
        "ip": client_ip
    }

    try:
        print("\nEnviando solicitud de creación de cliente...")
        response = requests.post(
            f"{BASE_URL}/api/vpn/client/create",
            json=payload
        )

        if response.status_code == 200:
            print(f"Creación de cliente completada: {response.status_code} OK")
            print_json(response.json())
        else:
            print(f"Error al crear el cliente: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

def test_client_delete() -> None:
    """Prueba el endpoint de eliminación de cliente OpenVPN."""
    print_section("Prueba de eliminación de cliente OpenVPN")

    # Obtener información del cliente
    client_name = input("Nombre del cliente a eliminar: ").strip()

    # Validar entrada
    if not client_name:
        print("Se requiere el nombre del cliente.")
        return

    try:
        print("\nEnviando solicitud de eliminación de cliente...")
        response = requests.delete(f"{BASE_URL}/api/vpn/client/{client_name}")

        if response.status_code == 200:
            print(f"Eliminación de cliente completada: {response.status_code} OK")
            print_json(response.json())
        else:
            print(f"Error al eliminar el cliente: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

def test_client_list() -> None:
    """Prueba el endpoint de listado de clientes OpenVPN."""
    print_section("Prueba de listado de clientes OpenVPN")
    try:
        response = requests.get(f"{BASE_URL}/api/vpn/clients")
        if response.status_code == 200:
            print(f"Listado de clientes completado: {response.status_code} OK")
            clients = response.json()
            if clients:
                print("Clientes configurados:")
                for client in clients:
                    print(f" - {client}")
            else:
                print("No hay clientes configurados.")
        else:
            print(f"Error al listar los clientes: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

def test_metrics() -> None:
    """Prueba los endpoints de métricas."""
    print_section("Prueba de endpoints de métricas")
    try:
        # Listar targets de monitoreo
        print("\nListando targets de monitoreo...")
        response = requests.get(f"{BASE_URL}/api/metrics/targets")

        if response.status_code == 200:
            targets = response.json()
            print(f"Se encontraron {len(targets)} targets")

            if targets:
                # Seleccionar un target para ver métricas
                target = targets[0]
                target_id = target["id"]
                print(f"\nMostrando métricas recientes para target '{target['target']}' (ID: {target_id}):")

                # Obtener última métrica
                response = requests.get(f"{BASE_URL}/api/metrics/targets/{target_id}/latest")
                if response.status_code == 200:
                    print("\nÚltima métrica:")
                    print_json(response.json())
                else:
                    print(f"Error al obtener la última métrica: {response.status_code}")
                    print(response.text)

                # Obtener análisis de calidad
                response = requests.get(f"{BASE_URL}/api/metrics/targets/{target_id}/quality")
                if response.status_code == 200:
                    print("\nAnálisis de calidad de conexión:")
                    print_json(response.json())
                else:
                    print(f"Error al obtener análisis de calidad: {response.status_code}")
                    print(response.text)
            else:
                print("No hay targets configurados para monitoreo.")
        else:
            print(f"Error al listar targets: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")

def main() -> None:
    """Función principal que ejecuta las pruebas de la API."""
    print_section("TEST DE API DE SUBNETX VPN")

    # Verificar si la API está en ejecución
    if not check_api_running():
        print("La API no está en ejecución. Asegúrate de iniciar el servidor API primero.")
        print(f"Intentando conectar a: {BASE_URL}")
        print("\nPuedes iniciar la API con el comando:")
        print("  python -m vpn.metrics.api.api_server")
        return

    print("La API está en ejecución correctamente.\n")

    while True:
        print("\nSelecciona una operación para probar:")
        print("1. Verificar estado del servidor VPN")
        print("2. Configurar servidor VPN")
        print("3. Iniciar servidor VPN")
        print("4. Detener servidor VPN")
        print("5. Crear cliente VPN")
        print("6. Eliminar cliente VPN")
        print("7. Listar clientes VPN")
        print("8. Consultar métricas de monitoreo")
        print("0. Salir")

        option = input("\nOpción: ").strip()

        if option == "1":
            test_server_status()
        elif option == "2":
            test_server_setup()
        elif option == "3":
            test_server_start()
        elif option == "4":
            test_server_stop()
        elif option == "5":
            test_client_create()
        elif option == "6":
            test_client_delete()
        elif option == "7":
            test_client_list()
        elif option == "8":
            test_metrics()
        elif option == "0":
            print("\n¡Hasta pronto!")
            break
        else:
            print("\nOpción no válida. Inténtalo de nuevo.")

        if option != "0":
            time.sleep(1)  # Pausa breve entre operaciones

if __name__ == "__main__":
    main()
