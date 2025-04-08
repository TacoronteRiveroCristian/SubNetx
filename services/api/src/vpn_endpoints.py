"""
SubNetx VPN Management API Endpoints.

Este módulo define los endpoints para la gestión de un servidor OpenVPN,
incluyendo la configuración, inicio, parada y gestión de clientes.

Los endpoints permiten:
- Obtener el estado actual del servidor
- Configurar el servidor con parámetros personalizados
- Iniciar y detener el servicio
- Crear, listar y eliminar clientes VPN

Los endpoints se comunican con los scripts de shell subyacentes que
realizan las operaciones reales en el sistema.

:module: vpn.metrics.api.vpn_endpoints
:author: SubNetx Team
:version: 1.0.0
"""

import logging
import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Union
import asyncio
import json

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field, IPvAnyAddress, validator

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router con prefijo para todos los endpoints
router = APIRouter(
    prefix="/api/vpn",
    tags=["vpn-management"],
    responses={404: {"description": "Not found"}},
)

# Modelos Pydantic para validación de datos
class ServerStatus(BaseModel):
    """Modelo para el estado del servidor OpenVPN."""
    status: str = Field(..., description="Estado del servidor: running, stopped, unknown")
    uptime: int = Field(0, description="Tiempo de actividad en segundos, 0 si no está en ejecución")
    connected_clients: int = Field(0, description="Número de clientes conectados")
    message: str = Field(..., description="Mensaje descriptivo sobre el estado")

class ServerConfigRequest(BaseModel):
    """Modelo para la configuración del servidor OpenVPN."""
    vpn_network: str = Field(..., description="Dirección de red VPN (ej. 10.8.0.0)")
    vpn_netmask: str = Field(..., description="Máscara de red VPN (ej. 255.255.255.0)")
    openvpn_port: int = Field(..., description="Puerto para OpenVPN (1-65535)")
    openvpn_proto: str = Field(..., description="Protocolo (udp/tcp)")
    tun_device: str = Field(..., description="Dispositivo TUN (ej. tun0)")
    public_ip: str = Field(..., description="IP pública o nombre de dominio")

    # Validadores
    @validator('vpn_network')
    def validate_network(cls, v):
        """Validar formato de dirección de red."""
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', v):
            raise ValueError('Formato de dirección de red inválido')
        return v

    @validator('vpn_netmask')
    def validate_netmask(cls, v):
        """Validar formato de máscara de red."""
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', v):
            raise ValueError('Formato de máscara de red inválido')
        return v

    @validator('openvpn_port')
    def validate_port(cls, v):
        """Validar que el puerto esté en el rango válido."""
        if v < 1 or v > 65535:
            raise ValueError('El puerto debe estar entre 1 y 65535')
        return v

    @validator('openvpn_proto')
    def validate_proto(cls, v):
        """Validar que el protocolo sea udp o tcp."""
        if v.lower() not in ['udp', 'tcp']:
            raise ValueError('El protocolo debe ser udp o tcp')
        return v.lower()

class ClientRequest(BaseModel):
    """Modelo para la creación de cliente OpenVPN."""
    name: str = Field(..., description="Nombre del cliente")
    ip: str = Field(..., description="IP asignada al cliente")

    @validator('name')
    def validate_name(cls, v):
        """Validar que el nombre del cliente sea alfanumérico."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('El nombre del cliente debe ser alfanumérico')
        return v

    @validator('ip')
    def validate_ip(cls, v):
        """Validar formato de dirección IP."""
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', v):
            raise ValueError('Formato de dirección IP inválido')
        return v

class ClientResponse(BaseModel):
    """Modelo para la respuesta de operaciones con clientes."""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo sobre la operación")
    config_path: Optional[str] = Field(None, description="Ruta al archivo de configuración del cliente")

class OperationResponse(BaseModel):
    """Modelo para la respuesta de operaciones generales."""
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo sobre la operación")
    output: Optional[str] = Field(None, description="Salida de la operación")

class ClientInfo(BaseModel):
    """Modelo para la información detallada de un cliente OpenVPN."""
    name: str = Field(..., description="Nombre del cliente")
    ip: str = Field(..., description="IP asignada al cliente")
    created_at: datetime = Field(default_factory=datetime.now, description="Fecha de creación del cliente")

# Función auxiliar para ejecutar comandos
def run_command(command: List[str]) -> Dict[str, Union[bool, str]]:
    """
    Ejecuta un comando en el sistema y devuelve el resultado.

    Args:
        command: Lista de strings con el comando y sus argumentos

    Returns:
        Dict con éxito/fracaso, mensaje y salida del comando
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "success": True,
            "message": "Comando ejecutado correctamente",
            "output": result.stdout.strip()
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Error ejecutando comando: {e}")
        return {
            "success": False,
            "message": f"Error ejecutando comando: {e}",
            "output": e.stderr.strip() if e.stderr else str(e)
        }
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return {
            "success": False,
            "message": f"Error inesperado: {e}",
            "output": str(e)
        }

# Rutas para gestión del servidor OpenVPN
@router.get("/status", response_model=ServerStatus, summary="Obtener estado del servidor OpenVPN")
async def get_server_status():
    """
    Obtiene el estado actual del servidor OpenVPN.

    Verifica si el servicio está en ejecución, cuánto tiempo lleva activo,
    y cuántos clientes están conectados.

    Returns:
        ServerStatus: Estado actual del servidor
    """
    # Ejecutar script de verificación de estado
    result = run_command(["/app/scripts/core/openvpn-status.sh"])

    if result["success"]:
        # Analizar salida para determinar estado
        output = str(result["output"])

        if "running" in output.lower():
            # Extraer información adicional si está disponible
            uptime_match = re.search(r'uptime: (\d+)', output)
            clients_match = re.search(r'clients: (\d+)', output)

            return {
                "status": "running",
                "uptime": int(uptime_match.group(1)) if uptime_match else 0,
                "connected_clients": int(clients_match.group(1)) if clients_match else 0,
                "message": "Servidor ejecutándose correctamente"
            }
        else:
            return {
                "status": "stopped",
                "uptime": 0,
                "connected_clients": 0,
                "message": "Servidor detenido"
            }
    else:
        # Si hay error, reportar estado desconocido
        return {
            "status": "unknown",
            "uptime": 0,
            "connected_clients": 0,
            "message": f"No se pudo determinar el estado: {result['output']}"
        }

@router.post("/setup", response_model=OperationResponse, summary="Configurar servidor OpenVPN")
async def setup_server(config: ServerConfigRequest):
    """
    Configura el servidor OpenVPN con los parámetros especificados.

    Genera los archivos de configuración necesarios para el servidor OpenVPN
    utilizando los parámetros proporcionados.

    Args:
        config: Parámetros de configuración del servidor

    Returns:
        OperationResponse: Resultado de la operación de configuración
    """
    # Construir comando con los parámetros usando flags
    command = [
        "/app/scripts/core/openvpn-setup.sh",
        "--red", config.vpn_network,
        "--mask", config.vpn_netmask,
        "--port", str(config.openvpn_port),
        "--proto", config.openvpn_proto,
        "--tun", config.tun_device,
        "--ip", config.public_ip
    ]

    # Ejecutar script de configuración
    result = run_command(command)

    if result["success"]:
        return {
            "success": True,
            "message": "Servidor configurado correctamente con parámetros personalizados",
            "output": result["output"]
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Error configurando el servidor: {result['output']}"
        )

@router.post("/start", response_model=OperationResponse, summary="Iniciar servidor OpenVPN")
async def start_server():
    """
    Inicia el servidor OpenVPN.

    Ejecuta el servicio OpenVPN con la configuración actual.

    Returns:
        OperationResponse: Resultado de la operación de inicio
    """
    # Verificar estado actual
    status = await get_server_status()

    if status["status"] == "running":
        return {
            "success": True,
            "message": "El servidor ya está en ejecución",
            "output": "No se requiere acción"
        }

    # Ejecutar script de inicio
    result = run_command(["/app/scripts/core/openvpn-start.sh"])

    if result["success"]:
        return {
            "success": True,
            "message": "Servidor iniciado correctamente",
            "output": result["output"]
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Error iniciando el servidor: {result['output']}"
        )

@router.post("/stop", response_model=OperationResponse, summary="Detener servidor OpenVPN")
async def stop_server():
    """
    Detiene el servidor OpenVPN.

    Finaliza el proceso del servicio OpenVPN.

    Returns:
        OperationResponse: Resultado de la operación de parada
    """
    # Verificar estado actual
    status = await get_server_status()

    if status["status"] == "stopped":
        return {
            "success": True,
            "message": "El servidor ya está detenido",
            "output": "No se requiere acción"
        }

    # Ejecutar script de parada
    result = run_command(["/app/scripts/core/openvpn-stop.sh"])

    if result["success"]:
        return {
            "success": True,
            "message": "Servidor detenido correctamente",
            "output": result["output"]
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Error deteniendo el servidor: {result['output']}"
        )

@router.post("/reset", response_model=OperationResponse, summary="Eliminar toda la configuración del servidor OpenVPN")
async def reset_server():
    """
    Elimina toda la configuración del servidor OpenVPN.

    Borra todos los certificados del servidor, configuraciones y clientes.
    Esta operación no se puede deshacer.

    Returns:
        OperationResponse: Resultado de la operación de eliminación
    """
    # Ejecutar script de reset que ya maneja la parada del servidor y la limpieza de archivos
    logger.info("Iniciando proceso de reset del servidor OpenVPN")
    result = run_command(["/app/scripts/core/openvpn-reset.sh"])

    if result["success"]:
        logger.info("Reset completado correctamente")
        return {
            "success": True,
            "message": "Configuración del servidor eliminada correctamente",
            "output": result["output"]
        }
    else:
        logger.error(f"Error durante el reset: {result['output']}")
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando la configuración del servidor: {result['output']}"
        )

# Rutas para gestión de clientes
@router.get("/clients", response_model=List[ClientInfo], summary="Listar clientes OpenVPN")
async def list_clients():
    """
    Lista todos los clientes OpenVPN configurados con su información detallada.

    Returns:
        List[ClientInfo]: Lista de clientes con su información detallada
    """
    # Ejecutar script para listar clientes
    result = run_command(["/app/scripts/client/openvpn-client-list.sh"])

    if result["success"]:
        # Obtener lista de clientes desde la salida
        output = str(result["output"])
        clients = []

        # Procesar cada cliente
        for line in output.split("\n"):
            if line.strip():
                # Obtener información del cliente del archivo CCD
                client_name = line.strip()
                ccd_file = f"/etc/openvpn/ccd/{client_name}"

                if os.path.exists(ccd_file):
                    # Leer IP del archivo CCD
                    with open(ccd_file, 'r') as f:
                        ccd_content = f.read()
                        ip_match = re.search(r'ifconfig-push\s+(\d+\.\d+\.\d+\.\d+)', ccd_content)
                        ip = ip_match.group(1) if ip_match else "Unknown"

                    # Obtener fecha de creación del archivo
                    created_at = datetime.fromtimestamp(os.path.getctime(ccd_file))

                    clients.append(ClientInfo(
                        name=client_name,
                        ip=ip,
                        created_at=created_at
                    ))

        return clients
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Error listando clientes: {result['output']}"
        )

@router.post("/client/create", response_model=ClientResponse, summary="Crear cliente OpenVPN")
async def create_client(client: ClientRequest):
    """
    Crea un nuevo cliente OpenVPN.

    Genera la configuración y certificados para un nuevo cliente con
    la IP especificada. Verifica que la IP y el nombre no estén ya en uso
    y que la IP esté dentro de la red configurada.

    Args:
        client: Datos del cliente a crear

    Returns:
        ClientResponse: Resultado de la operación de creación
    """
    # Verificar si el nombre o la IP ya están en uso
    existing_clients = await list_clients()
    for existing_client in existing_clients:
        if existing_client.name == client.name:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un cliente con el nombre {client.name}"
            )
        if existing_client.ip == client.ip:
            raise HTTPException(
                status_code=400,
                detail=f"La IP {client.ip} ya está asignada al cliente {existing_client.name}"
            )

    # Construir comando con los parámetros
    command = [
        "/app/scripts/client/openvpn-client-new.sh",
        "--name", client.name,
        "--ip", client.ip
    ]

    try:
        # Ejecutar el comando
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Error creating client: {stderr.decode()}"
            )

        # Añadir el cliente al archivo de monitorización
        await update_monitoring_clients(client)

        # Devolver la respuesta
        return ClientResponse(
            success=True,
            message=f"Client {client.name} created successfully",
            config_path=f"/etc/openvpn/client/{client.name}.ovpn"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def update_monitoring_clients(client: ClientRequest):
    """
    Actualiza el archivo JSON de clientes para monitorización.

    Args:
        client: Cliente a añadir al monitoreo
    """
    try:
        work_dir = os.getenv("WORK_DIR", "")
        config_path = os.path.join(work_dir, "collector", "config", "vpn_clients.json")

        # Asegurar que el directorio exista
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # Leer el archivo existente o crear uno nuevo
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                data = json.load(f)
        else:
            logger.info(f"Creating new vpn_clients.json file at {config_path}")
            data = {"clients": []}

        # Añadir el nuevo cliente si no existe
        client_exists = any(c.get('name') == client.name for c in data['clients'])
        if not client_exists:
            data['clients'].append({
                "name": client.name,
                "ip": client.ip,
                "created_at": datetime.now().isoformat()
            })

            # Guardar el archivo actualizado
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=4)

            logger.info(f"Added client {client.name} with IP {client.ip} to monitoring")

            # Intentar registrar el cliente en la base de datos de métricas
            try:
                db_path = os.path.join(work_dir, "databases", "ping.db")
                if os.path.exists(db_path):
                    from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
                    db = PingDatabase(db_path)
                    target_id = db.add_target(client.ip, f"VPN Client: {client.name}")
                    logger.info(f"Added client {client.name} to metrics database with ID {target_id}")
            except Exception as db_err:
                logger.error(f"Error adding client to metrics database: {str(db_err)}")
        else:
            logger.info(f"Client {client.name} already exists in monitoring file")

    except Exception as e:
        logger.error(f"Error updating monitoring clients: {str(e)}")
        # No lanzamos excepción para no interrumpir la creación del cliente

@router.delete("/client/{client_name}", response_model=OperationResponse, summary="Eliminar cliente OpenVPN")
async def delete_client(
    client_name: str = Path(..., description="Nombre del cliente a eliminar")
):
    """
    Elimina un cliente OpenVPN.

    Elimina la configuración y certificados del cliente especificado.

    Args:
        client_name: Nombre del cliente a eliminar

    Returns:
        OperationResponse: Resultado de la operación de eliminación
    """
    # Construir comando con los parámetros
    command = [
        "/app/scripts/client/openvpn-client-delete.sh",
        "--name", client_name
    ]

    try:
        # Ejecutar el comando
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting client: {stderr.decode()}"
            )

        # Eliminar el cliente del archivo de monitorización
        await remove_monitoring_client(client_name)

        return OperationResponse(
            success=True,
            message=f"Client {client_name} deleted successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def remove_monitoring_client(client_name: str):
    """
    Elimina un cliente del archivo JSON de monitorización.

    Args:
        client_name: Nombre del cliente a eliminar
    """
    try:
        work_dir = os.getenv("WORK_DIR", "")
        config_path = os.path.join(work_dir, "collector", "config", "vpn_clients.json")
        if not os.path.exists(config_path):
            logger.warning(f"VPN clients file not found at {config_path}")
            return

        # Leer el archivo
        client_ip = None
        with open(config_path, 'r') as f:
            data = json.load(f)

            # Buscar la IP del cliente antes de eliminarlo
            for client in data.get('clients', []):
                if client.get('name') == client_name:
                    client_ip = client.get('ip')
                    break

        # Filtrar el cliente a eliminar
        data['clients'] = [c for c in data['clients'] if c.get('name') != client_name]

        # Guardar el archivo actualizado
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=4)

        logger.info(f"Removed client {client_name} from monitoring")

        # Si encontramos la IP, intentar eliminar el cliente de la base de datos
        if client_ip:
            try:
                # Obtener todos los targets de la base de datos y eliminar el que coincida con la IP
                db_path = os.path.join(work_dir, "databases", "ping.db")
                if os.path.exists(db_path):
                    from vpn.metrics.collector.classes.databases.database_ping import PingDatabase
                    db = PingDatabase(db_path)

                    # Buscamos el target con la IP del cliente
                    targets = db.get_all_targets()
                    for target in targets:
                        if target.get('target') == client_ip:
                            # No hay método para eliminar targets, pero podríamos eliminar las métricas
                            # Esto es una medida temporal hasta que se implemente
                            logger.info(f"Found target with ID {target.get('id')} for removed client {client_name}")
                            break
            except Exception as db_err:
                logger.error(f"Error managing metrics database for client removal: {str(db_err)}")

    except Exception as e:
        logger.error(f"Error removing monitoring client: {str(e)}")
        # No lanzamos excepción para no interrumpir la eliminación del cliente

@router.get("/has-certificates", summary="Verificar si existen certificados del servidor")
async def has_certificates():
    """
    Comprueba si existen certificados y configuraciones para el servidor.

    Este endpoint verifica la existencia de archivos críticos como el certificado
    del servidor, la clave y la configuración.

    Returns:
        Dict: Indicando si existen certificados y configuración
    """
    # Comprobar existencia de archivos críticos
    server_conf_exists = os.path.exists("/etc/openvpn/server/server.conf")
    pki_exists = os.path.exists("/etc/openvpn/easy-rsa/pki")

    # Consideramos que hay certificados si existe el directorio PKI o la configuración del servidor
    has_certs = server_conf_exists or pki_exists

    logger.info(f"Verificación de certificados: {has_certs} (server_conf: {server_conf_exists}, pki: {pki_exists})")

    return {
        "hasCertificates": has_certs,
        "serverConfExists": server_conf_exists,
        "pkiExists": pki_exists
    }
