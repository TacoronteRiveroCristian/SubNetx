# SubNetx VPN Management API

Esta API proporciona una interfaz REST para administrar el servidor OpenVPN y sus clientes, permitiendo configurar, controlar y monitorear todos los aspectos del servicio VPN.

## Funcionalidades

- **Gestión del servidor OpenVPN**:
  - Configuración inicial del servidor con parámetros personalizables
  - Inicio del servicio
  - Parada del servicio
  - Consulta de estado en tiempo real

- **Gestión de clientes**:
  - Creación de nuevos clientes con IP fija
  - Eliminación de clientes
  - Listado de clientes configurados

## Arquitectura

La API está desarrollada utilizando FastAPI y se integra con los scripts de shell que configuran y administran el servidor OpenVPN. Esto permite:

1. Acceso a todas las funcionalidades desde una interfaz web
2. Integración con la interfaz de usuario de SubNetx
3. Control programático de la VPN
4. Validación de parámetros y manejo de errores robusto

## Endpoints disponibles

### Gestión del servidor

- `GET /api/vpn/status` - Obtiene el estado actual del servidor
- `POST /api/vpn/setup` - Configura el servidor OpenVPN con parámetros personalizables
- `POST /api/vpn/start` - Inicia el servicio OpenVPN
- `POST /api/vpn/stop` - Detiene el servicio OpenVPN

### Gestión de clientes

- `GET /api/vpn/clients` - Lista todos los clientes configurados
- `POST /api/vpn/client/create` - Crea un nuevo cliente con IP fija
- `DELETE /api/vpn/client/{client_name}` - Elimina un cliente existente

## Ejemplos de uso

### Obtener el estado del servidor

```bash
curl -X GET http://localhost:8000/api/vpn/status | jq
```

Respuesta:
```json
{
  "status": "running",
  "uptime": 3600,
  "connected_clients": 2,
  "message": "Servidor ejecutándose correctamente"
}
```

### Configurar el servidor

Para configurar el servidor con parámetros personalizados:

```bash
curl -X POST http://localhost:8000/api/vpn/setup \
  -H "Content-Type: application/json" \
  -d '{
    "vpn_network": "10.8.0.0",
    "vpn_netmask": "255.255.255.0",
    "openvpn_port": 1194,
    "openvpn_proto": "udp",
    "tun_device": "tun0",
    "public_ip": "labcrist.duckdns.org"
  }' | jq
```

Respuesta:
```json
{
  "success": true,
  "message": "Servidor configurado correctamente con parámetros personalizados",
  "output": "✅ Configuración de OpenVPN completada correctamente."
}
```

> **Nota importante**: Las credenciales sensibles como el token de DuckDNS deben configurarse en el archivo `.env` del servidor y no a través de la API.

### Iniciar el servidor

```bash
curl -X POST http://localhost:8000/api/vpn/start | jq
```

Respuesta:
```json
{
  "success": true,
  "message": "Servidor iniciado correctamente",
  "output": "✅ OpenVPN iniciado correctamente en segundo plano (PID: 1234)."
}
```

### Detener el servidor

```bash
curl -X POST http://localhost:8000/api/vpn/stop | jq
```

Respuesta:
```json
{
  "success": true,
  "message": "Servidor detenido correctamente",
  "output": "✅ OpenVPN detenido correctamente."
}
```

### Crear un nuevo cliente

```bash
curl -X POST http://localhost:8000/api/vpn/client/create \
  -H "Content-Type: application/json" \
  -d '{"name": "cliente1", "ip": "10.8.0.10"}' | jq
```

Respuesta:
```json
{
  "success": true,
  "message": "Cliente cliente1 creado correctamente",
  "config_path": "/etc/openvpn/clients/cliente1.ovpn"
}
```

### Listar clientes

```bash
curl -X GET http://localhost:8000/api/vpn/clients | jq
```

Respuesta:
```json
[
  "cliente1",
  "cliente2",
  "cliente3"
]
```

### Eliminar un cliente

```bash
curl -X DELETE http://localhost:8000/api/vpn/client/cliente1 | jq
```

Respuesta:
```json
{
  "success": true,
  "message": "Cliente cliente1 eliminado correctamente",
  "output": "✅ Cliente cliente1 eliminado correctamente."
}
```

## Parámetros de configuración

La configuración del servidor OpenVPN acepta los siguientes parámetros:

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| vpn_network | string | Dirección de red para la VPN | "10.8.0.0" |
| vpn_netmask | string | Máscara de red para la VPN | "255.255.255.0" |
| openvpn_port | integer | Puerto para el servicio | 1194 |
| openvpn_proto | string | Protocolo (udp/tcp) | "udp" |
| tun_device | string | Interfaz TUN a utilizar | "tun0" |
| public_ip | string | IP pública o nombre de dominio | "ejemplo.duckdns.org" |

## Archivo .env

El archivo `.env` debe contener los siguientes parámetros sensibles que no se deberían exponer a través de la API:

```bash
# Configuración de DuckDNS (opcional)
DUCKDNS_TOKEN=your-duckdns-token

# Otros parámetros sensibles
```

## Pruebas automatizadas

Para probar todos los endpoints de forma interactiva, utiliza el script de prueba incluido:

```bash
python3 test_vpn_api.py
```

Este script te guiará a través de todas las funcionalidades disponibles en la API, permitiéndote personalizar la configuración del servidor y realizar operaciones con clientes.

## Integración con la UI de SubNetx

Para integrar esta API con la interfaz de usuario de SubNetx, actualiza las funciones en el archivo `server.tsx` para que realicen llamadas a estos endpoints en lugar de usar simulaciones.

Ejemplo de función para iniciar el servidor desde la UI:

```typescript
const handleServerOperation = async (operation: 'setup' | 'start' | 'stop' | 'edit') => {
  setLoading(true);

  try {
    // Determinar la URL del endpoint según la operación
    let endpoint = '';
    let body = null;
    let method = 'POST';

    switch(operation) {
      case 'setup':
        endpoint = '/api/vpn/setup';
        // Obtener los valores del formulario o usar valores predeterminados
        body = {
          vpn_network: "10.8.0.0",
          vpn_netmask: "255.255.255.0",
          openvpn_port: 1194,
          openvpn_proto: "udp",
          tun_device: "tun0",
          public_ip: "labcrist.duckdns.org"
        };
        break;
      case 'start': endpoint = '/api/vpn/start'; break;
      case 'stop': endpoint = '/api/vpn/stop'; break;
      case 'edit': endpoint = '/api/vpn/config/edit'; break;
    }

    // Realizar la llamada a la API
    const response = await fetch(endpoint, {
      method: method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: body ? JSON.stringify(body) : null
    });

    const data = await response.json();

    if (data.success) {
      // Actualizar el estado según la operación
      if (operation === 'start') {
        setServerStatus('running');
      } else if (operation === 'stop') {
        setServerStatus('stopped');
      }
    } else {
      // Manejar error
      console.error('Error:', data.error || data.message);
    }
  } catch (error) {
    console.error('Failed to perform operation:', error);
  } finally {
    setLoading(false);
  }
};
```

## Consideraciones de seguridad

Esta API debería:

1. Implementar autenticación antes de usarse en producción
2. Usar HTTPS para cifrar las comunicaciones
3. Restringir el acceso solo a administradores
4. Nunca transmitir tokens o credenciales sensibles a través de la API

Antes de desplegar en producción, asegúrate de implementar estas medidas de seguridad.
