# SubnetX VPN Container

Este proyecto proporciona una imagen de Docker optimizada para gestionar un servidor **OpenVPN**, permitiendo configurar y administrar VPNs de manera segura y eficiente. Cada contenedor despliega una **subred VPN independiente**, lo que significa que si deseas gestionar múltiples subredes, puedes ejecutar un contenedor por cada una, facilitando la segmentación de redes para distintos proyectos.

## 📌 Características
- Basado en **Ubuntu 22.04**.
- Incluye **OpenVPN, Easy-RSA, iptables y herramientas esenciales**.
- Configuración automatizada mediante **variables de entorno**.
- Soporte para **gestión de clientes VPN**.
- Uso de **iptables para NAT** y reenvío de paquetes.
- Soporte para despliegue mediante **Docker Compose**.

## 🚀 Instalación y Uso

### 1. Clonar el Repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_PROYECTO>
```

### 2. Configurar los Permisos
Para mejorar la seguridad, establece permisos adecuados en la carpeta `docker/`:
```bash
chmod 600 -R docker/
```
Esto evita accesos no autorizados a archivos sensibles de configuración.

### 3. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```bash
# Configuración de OpenVPN
VPN_NETWORK=10.8.0.0
VPN_NETMASK=255.255.255.0
OPENVPN_PORT=1194
OPENVPN_PROTO=udp
TUN_DEVICE=tun0
PUBLIC_IP=tu-dominio.duckdns.org

# Configuración de DuckDNS (opcional)
DUCKDNS_TOKEN=tu-token-duckdns
```

### 4. Opción A: Despliegue con Docker Compose (Recomendado)

#### 4.1. Iniciar los Servicios
```bash
docker compose up -d
```

### 5. Opción B: Despliegue Individual de Contenedores

#### 5.1. Construir la Imagen Docker
```bash
sudo docker build -t subnetx-vpn -f docker/subnetx.Dockerfile .
```

#### 5.2. Ejecutar el Contenedor
Cada contenedor se encarga de gestionar una **subred VPN independiente**. Si deseas configurar una VPN específica para un proyecto, lanza un contenedor con un nombre distintivo:
```bash
sudo docker run --name subnetx-vpn1 -d \
    --restart unless-stopped \
    --cap-add=NET_ADMIN \
    --device=/dev/net/tun:/dev/net/tun \
    -p 1194:1194/udp \
    -v ./vpn1-client:/etc/openvpn/client \
    --env-file .env \
    subnetx-vpn
```

Si deseas otra subred para un segundo proyecto:
```bash
sudo docker run --name subnetx-vpn2 -d \
    --restart unless-stopped \
    --cap-add=NET_ADMIN \
    --device=/dev/net/tun:/dev/net/tun \
    -p 1195:1194/udp \
    -v ./vpn2-client:/etc/openvpn/client \
    --env-file ./vpn2/.env \
    subnetx-vpn
```

> ⚠️ **IMPORTANTE:** Si el servidor está detrás de un router, **debes abrir y redirigir el puerto correspondiente en el router** para permitir conexiones externas. En este ejemplo:
> - Para `subnetx-vpn1`, debes abrir y redirigir el puerto **1194/UDP** en el router hacia la IP del servidor.
> - Para `subnetx-vpn2`, debes abrir y redirigir el puerto **1195/UDP** en el router hacia la IP del servidor.

### 6. Gestión del Servidor VPN
Una vez configurado, puedes gestionar el servidor con los siguientes comandos:
```bash
sudo docker exec -it subnetx_vpn subnetx start
sudo docker exec -it subnetx_vpn subnetx stop
```

### 7. Administrar Clientes VPN
Para agregar clientes sin perder la configuración ni los certificados:
```bash
sudo docker exec -it subnetx_vpn subnetx client new --name cliente1 --ip 10.8.0.10
```

> ⚠️ **IMPORTANTE:** En el caso de que el cliente necesite apuntar a un **puerto distinto de 1194**, es necesario especificarlo en el **archivo .ovpn** del cliente ya que esa funcionalidad aún no está implementada en la herramienta `subnetx`.

```bash
client
dev tun
proto udp
remote myvpn1.example.com 119X #1994
resolv-retry infinite
...
```

### 8. Detener y Eliminar el Contenedor
Para **detener** el contenedor sin perder la configuración:
```bash
sudo docker stop subnetx_vpn
```
Para eliminarlo definitivamente:
```bash
sudo docker rm subnetx_vpn
```
Si deseas reiniciar la VPN sin afectar los datos almacenados en el volumen:
```bash
sudo docker start subnetx_vpn
```
Para eliminar el contenedor y los datos de configuración:
```bash
sudo docker rm -v subnetx_vpn
```
> **Importante:** Si eliminas el contenedor sin la opción `-v`, los certificados y configuraciones seguirán almacenados en `./vpn1-data`.

## 📌 Notas Importantes
- **Cada contenedor gestiona una subred VPN independiente**, ideal para separar proyectos o clientes.
- **Los puertos deben abrirse en el router** para permitir conexiones externas.
- **Siempre ejecuta el contenedor como `root`** para evitar problemas de permisos.
- **Cuidado con eliminar el contenedor ya que los certificados se perderán**. Si deseas eliminar el contenedor sin perder los certificados, utiliza la opción `-v` al eliminarlo: `sudo docker rm -v subnetx_vpn`.
- Si modificas `docker/config/openvpn/`, recuerda reconstruir la imagen antes de reiniciar.
- Al usar Docker Compose, asegúrate de configurar correctamente las variables de entorno en el archivo `.env`.
- **Para gestionar múltiples VPNs**, es una buena práctica:
  - Crear un directorio separado para cada VPN (ej: `./vpn1/`, `./vpn2/`)
  - Mantener un archivo `.env` específico en cada directorio con su configuración
  - Montar solo el volumen de clientes (`/etc/openvpn/client`) para cada VPN
  - Usar nombres de contenedor descriptivos (ej: `subnetx-vpn1`, `subnetx-vpn2`)
  - Asegurarte de que cada VPN use un puerto diferente y una subred diferente

## 📖 Información Adicional
Para más detalles sobre OpenVPN y configuraciones avanzadas, consulta la documentación oficial:
🔗 [OpenVPN Documentation](https://openvpn.net/community-resources/)

