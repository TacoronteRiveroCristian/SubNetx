# Solución al Problema de Gestión VPN con Docker

## Diagnóstico del Problema

El problema principal identificado fue la incorrecta inicialización de la infraestructura PKI de Easy-RSA en el servicio VPN, específicamente:

1. Faltaba el archivo `serial` en el directorio de Easy-RSA, lo que impedía la emisión de certificados para clientes.
2. La CA (Autoridad Certificadora) no se había generado correctamente.
3. La secuencia de inicialización del servidor no se completó adecuadamente.

Esto ocurrió porque el servicio VPN se estaba intentando utilizar sin realizar primero la configuración inicial necesaria (Setup).

## Solución Aplicada

### 1. Limpieza del Entorno

```bash
# Detener procesos dentro del contenedor
docker exec subnetx_vpn pkill -f "python3 -m scripts.api.main"
docker exec subnetx_vpn pkill openvpn

# Limpiar certificados y archivos de configuración
docker exec subnetx_vpn rm -rf /etc/openvpn/certs/clients/*
docker exec subnetx_vpn rm -rf /etc/openvpn/certs/ca.crt /etc/openvpn/certs/server.crt /etc/openvpn/certs/server.key /etc/openvpn/certs/dh.pem /etc/openvpn/certs/ta.key
docker exec subnetx_vpn rm -rf /etc/openvpn/easy-rsa/pki/*

# Reiniciar contenedores
docker restart subnetx_vpn subnetx_api subnetx_postgres subnetx_ui
```

### 2. Configuración Inicial del Servidor VPN

```bash
# Ejecutar setup del servidor VPN con los parámetros adecuados
docker exec subnetx_vpn curl -X POST http://localhost:9020/server/setup -H "Content-Type: application/json" -d '{"red":"10.10.10.0","mask":"255.255.255.0","port":"1194","proto":"udp","tun":"tun0","ip":"localhost"}'
```

Esto generó correctamente:
- Archivos de configuración del servidor OpenVPN
- Infraestructura PKI completa en `/etc/openvpn/easy-rsa/pki/`
- Certificados y claves necesarios en `/etc/openvpn/certs/`

### 3. Inicio del Servidor VPN

```bash
# Iniciar el servicio OpenVPN
docker exec subnetx_vpn curl -X POST http://localhost:9020/server/start
```

Verificación:
```bash
# Verificar estado
docker exec subnetx_vpn curl -s http://localhost:9020/server/status
# Verificar proceso
docker exec subnetx_vpn ps aux | grep openvpn
```

### 4. Creación de Clientes VPN

```bash
# Crear cliente con nombre e IP específicos
docker exec subnetx_vpn curl -X POST http://localhost:9020/clients/ -H "Content-Type: application/json" -d '{"name":"cliente2","ip":"10.10.10.11"}'

# Crear clientes adicionales
docker exec subnetx_vpn curl -X POST http://localhost:9020/clients/ -H "Content-Type: application/json" -d '{"name":"cliente3","ip":"10.10.10.12"}'
docker exec subnetx_vpn curl -X POST http://localhost:9020/clients/ -H "Content-Type: application/json" -d '{"name":"cliente4","ip":"10.10.10.13"}'
```

### 5. Verificación de la Solución

Se realizaron pruebas exhaustivas que confirmaron:
- El servidor VPN inicia correctamente
- Los clientes se crean sin errores
- Los certificados y archivos de configuración se generan correctamente
- La detención y reinicio del servidor mantienen la configuración
- Los endpoints de API funcionan correctamente tanto dentro como fuera del contenedor
- La interfaz web muestra correctamente la información del servidor y clientes

## Explicación Técnica

El problema principal se debió a una secuencia de operaciones incorrecta:

1. **Secuencia correcta:**
   - Setup del servidor (genera PKI, certificados, configuración)
   - Inicio del servidor
   - Creación de clientes

2. **Secuencia incorrecta que causaba el error:**
   - Intento de crear clientes sin haber realizado el setup previo

La configuración de OpenVPN requiere una infraestructura PKI completa para funcionar correctamente, incluyendo:
- Autoridad Certificadora (CA)
- Certificado y clave del servidor
- Parámetros Diffie-Hellman
- Archivo serial para enumerar los certificados emitidos

Al ejecutar el setup, se inicializó correctamente esta infraestructura, permitiendo que las operaciones posteriores funcionaran adecuadamente.

## Recomendaciones para Evitar el Problema

1. **Verificación de Prerrequisitos:**
   - Implementar verificaciones en la API para asegurar que el setup se realizó antes de permitir otras operaciones.
   - Añadir mensajes de error explícitos cuando se intente crear clientes sin un servidor configurado.

2. **Mejoras en la Documentación:**
   - Documentar claramente la secuencia de operaciones necesaria.
   - Incluir ejemplos de uso correcto de la API.

3. **Mejoras en la Interfaz de Usuario:**
   - Inhabilitar opciones de creación de clientes si el servidor no está configurado.
   - Mostrar guía paso a paso para la configuración inicial.

4. **Scripts de Inicialización Mejorados:**
   - Implementar scripts que verifiquen el estado del sistema al inicio.
   - Ejecutar automáticamente la configuración inicial si es necesario.

## Procedimiento para Futuros Despliegues

1. Iniciar los contenedores con Docker Compose
2. Ejecutar el setup del servidor VPN
3. Iniciar el servidor VPN
4. Crear los clientes necesarios
5. Verificar la funcionalidad completa

Este procedimiento asegura que todos los componentes se inicialicen en el orden correcto y que la infraestructura PKI esté completa antes de intentar operaciones que dependan de ella.
