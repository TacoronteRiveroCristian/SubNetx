# SubnetX VPN Container

Este proyecto proporciona una imagen de Docker optimizada para gestionar un servidor **OpenVPN**, permitiendo configurar y administrar VPNs de manera segura y eficiente. Cada contenedor despliega una **subred VPN independiente**, lo que significa que si deseas gestionar múltiples subredes, puedes ejecutar un contenedor por cada una, facilitando la segmentación de redes para distintos proyectos.

## 📌 Características
- Basado en **Ubuntu 22.04**.
- Incluye **OpenVPN, Easy-RSA, iptables y herramientas esenciales**.
- Configuración automatizada con `subnetx setup`, que ahora admite **parámetros de entrada**.
- Soporte para **gestión de clientes VPN**.
- Uso de **iptables para NAT** y reenvío de paquetes.

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

### 3. Construir la Imagen Docker
Ejecuta el siguiente comando para construir la imagen:
```bash
sudo docker build -t subnetx-vpn -f docker/subnetx.Dockerfile .
```

### 4. Ejecutar el Contenedor
Cada contenedor se encarga de gestionar una **subred VPN independiente**. Si deseas configurar una VPN específica para un proyecto, lanza un contenedor con un nombre distintivo:
```bash
sudo docker run --name subnetx-vpn1 -d \
    --restart unless-stopped \
    --cap-add=NET_ADMIN \
    --device=/dev/net/tun:/dev/net/tun \
    -p 1194:1194/udp \
    -v ./vpn1-client:/etc/openvpn/client \
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
    subnetx-vpn
```

> ⚠️ **IMPORTANTE:** Si el servidor está detrás de un router, **debes abrir y redirigir el puerto correspondiente en el router** para permitir conexiones externas. En este ejemplo:
> - Para `subnetx-vpn1`, debes abrir y redirigir el puerto **1194/UDP** en el router hacia la IP del servidor.
> - Para `subnetx-vpn2`, debes abrir y redirigir el puerto **1195/UDP** en el router hacia la IP del servidor.

### 5. Ejecutar la Configuración Inicial
Cada contenedor VPN debe configurarse individualmente. Ejecuta el siguiente comando para configurar `subnetx-vpn1`:
```bash
sudo docker exec -it subnetx-vpn1 subnetx setup \
    --network 10.9.0.0 \
    --netmask 255.255.255.0 \
    --port 1194 \
    --proto udp \
    --tun tun1 \
    --ip myvpn1.example.com
```
Para otro proyecto con una subred diferente:
```bash
sudo docker exec -it subnetx-vpn2 subnetx setup \
    --network 10.10.0.0 \
    --netmask 255.255.255.0 \
    --port 1195 \
    --proto udp \
    --tun tun2 \
    --ip myvpn2.example.com
```

#### 🔍 **Configuración de `tunX` y `tapX`**
El parámetro `--tun tunX` o `--tap tapX` especifica el tipo de interfaz de red:
- `tunX`: Crea una interfaz de **capa 3 (IP Routing)**, permitiendo el acceso a la VPN sin integrar los clientes en la misma red local.
- `tapX`: Crea una interfaz de **capa 2 (Ethernet Bridging)**, lo que significa que los clientes de la VPN estarán en la misma red que el servidor, como si estuvieran conectados por cable.

Para la mayoría de los casos, **`tunX` es la mejor opción** porque es más eficiente y evita colisiones de direcciones IP en redes LAN existentes. Usa `tapX` solo si necesitas que los clientes compartan la misma red LAN que el servidor.

### 6. Gestión del Servidor VPN
Una vez configurado, puedes gestionar el servidor con los siguientes comandos:
```bash
sudo docker exec -it subnetx-vpn1 subnetx start
sudo docker exec -it subnetx-vpn1 subnetx stop
```
Al ejecutar los comandos `subnetx start` y `subnetx stop`, la VPN se inicia o para respectivamente y manteniendo los certificados y configuración que se estableció con el comando `subnetx setup`.

### 6. Administrar Clientes VPN
Para agregar clientes sin perder la configuración ni los certificados:
```bash
sudo docker exec -it subnetx-vpn1 subnetx client new --name cliente1 --ip 10.9.0.10
```
Para otro proyecto:
```bash
sudo docker exec -it subnetx-vpn2 subnetx client new --name cliente2 --ip 10.10.0.10
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


### 7. Detener y Eliminar el Contenedor
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
> **Importante:** Si eliminas el contenedor sin la opción `-v`, los certificados y configuraciones seguirán almacenados en `./vpn1-data`.

## 📌 Notas Importantes
- **Cada contenedor gestiona una subred VPN independiente**, ideal para separar proyectos o clientes.
- **Los puertos deben abrirse en el router** para permitir conexiones externas.
- **Siempre ejecuta el contenedor como `root`** para evitar problemas de permisos.
- **Cuidado con eliminar el contenedor ya que los certificados se perderán**. Si deseas eliminar el contenedor sin perder los certificados, utiliza la opción `-v` al eliminarlo: `sudo docker rm -v subnetx-vpn1`.
- Si modificas `docker/config/openvpn/`, recuerda reconstruir la imagen antes de reiniciar.

## 📖 Información Adicional
Para más detalles sobre OpenVPN y configuraciones avanzadas, consulta la documentación oficial:
🔗 [OpenVPN Documentation](https://openvpn.net/community-resources/)

