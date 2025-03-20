# SubNetx - OpenVPN Container Manager

```ascii
   _____       _     _   _      _
  / ____|     | |   | \ | |    | |
 | (___  _   _| |__ |  \| | ___| |___  __
  \___ \| | | | '_ \| . ` |/ _ \ __\ \/ /
  ____) | |_| | |_) | |\  |  __/ |_ >  <
 |_____/ \__,_|_.__/|_| \_|\___|\__/_/\_\
```

SubNetx proporciona una imagen de Docker optimizada para gestionar servidores **OpenVPN**, permitiendo configurar y administrar VPNs de manera segura y eficiente. Cada contenedor despliega una **subred VPN independiente**, facilitando la segmentación de redes para distintos proyectos o entornos.

## 📌 Características
- Basado en **Ubuntu 22.04**
- Incluye **OpenVPN, Easy-RSA, iptables y herramientas esenciales**
- **Interfaz de terminal interactiva** para gestionar OpenVPN fácilmente
- Configuración automatizada mediante **variables de entorno**
- Soporte para **gestión de clientes VPN**
- Uso de **iptables para NAT** y reenvío de paquetes
- Soporte para despliegue mediante **Docker Compose**

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

## 💻 Interfaz de Terminal Interactiva

SubNetx cuenta con una interfaz interactiva que facilita la gestión del servidor OpenVPN sin necesidad de recordar comandos complejos.

### Iniciar la Interfaz Interactiva
```bash
sudo docker exec -it subnetx-vpn1 subnetx
```

### Opciones disponibles en la interfaz
La interfaz de terminal te permite:

- **Configurar OpenVPN:** Establece la configuración inicial del servidor
- **Iniciar servicio:** Arranca el servidor OpenVPN
- **Detener servicio:** Detiene el servidor OpenVPN
- **Gestionar clientes:** Submenú para crear y eliminar clientes
  - Crear nuevos clientes con nombre e IP personalizados
  - Eliminar clientes existentes
- **Ver ayuda:** Muestra información de ayuda sobre los comandos disponibles

Todas las operaciones se ejecutan en tiempo real y muestran su progreso directamente en la terminal.

### 6. Gestión del Servidor VPN (Línea de Comandos)
Si prefieres usar la línea de comandos directamente en lugar de la interfaz interactiva:
```bash
sudo docker exec -it subnetx-vpn1 subnetx start
sudo docker exec -it subnetx-vpn1 subnetx stop
```

### 7. Administrar Clientes VPN (Línea de Comandos)
Para agregar clientes sin usar la interfaz interactiva:
```bash
sudo docker exec -it subnetx-vpn1 subnetx client new --name cliente1 --ip 10.8.0.10
```

> ⚠️ **IMPORTANTE:** En el caso de que el cliente necesite apuntar a un **puerto distinto de 1194**, es necesario especificarlo en el **archivo .ovpn** del cliente:

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
sudo docker stop subnetx-vpn1
```
Para eliminarlo definitivamente:
```bash
sudo docker rm subnetx-vpn1
```
Si deseas reiniciar la VPN sin afectar los datos almacenados en el volumen:
```bash
sudo docker start subnetx-vpn1
```
Para eliminar el contenedor y los datos de configuración:
```bash
sudo docker rm -v subnetx-vpn1
```
> **Importante:** Si eliminas el contenedor sin la opción `-v`, los certificados y configuraciones seguirán almacenados en `./vpn1-client`.

## 📌 Notas Importantes
- **Cada contenedor gestiona una subred VPN independiente**, ideal para separar proyectos o clientes
- **Los puertos deben abrirse en el router** para permitir conexiones externas
- **Siempre ejecuta el contenedor como `root`** para evitar problemas de permisos
- **Cuidado con eliminar el contenedor ya que los certificados se perderán**. Si no deseas perder los certificados, usa la opción `-v` al eliminarlo
- Si modificas `docker/config/openvpn/`, recuerda reconstruir la imagen antes de reiniciar
- Al usar Docker Compose, asegúrate de configurar correctamente las variables de entorno en el archivo `.env`
- **Para gestionar múltiples VPNs**, es una buena práctica:
  - Crear un directorio separado para cada VPN (ej: `./vpn1/`, `./vpn2/`)
  - Mantener un archivo `.env` específico en cada directorio con su configuración
  - Montar solo el volumen de clientes (`/etc/openvpn/client`) para cada VPN
  - Usar nombres de contenedor descriptivos (ej: `subnetx-vpn1`, `subnetx-vpn2`)
  - Asegurarte de que cada VPN use un puerto diferente y una subred diferente

## 📖 Información Adicional
Para más detalles sobre OpenVPN y configuraciones avanzadas, consulta la documentación oficial:
🔗 [OpenVPN Documentation](https://openvpn.net/community-resources/)

