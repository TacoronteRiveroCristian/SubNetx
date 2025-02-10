# SubnetX OpenVPN Container

Este proyecto proporciona una imagen de Docker optimizada para gestionar un servidor **OpenVPN** con herramientas de configuración automatizadas. La imagen contiene los paquetes necesarios para instalar, configurar y administrar OpenVPN de manera segura y eficiente.

## 📌 Características
- Basado en **Ubuntu 22.04**.
- Incluye **OpenVPN, Easy-RSA, iptables y otras utilidades necesarias**.
- Configuración automatizada con el comando `subnetx setup`, ahora con soporte para **parámetros de entrada**.
- Soporta **gestión de clientes VPN**.
- Usa **iptables para NAT** y permite reenvío de paquetes.

## 🚀 Instalación y Uso

### 1. Clonar el Repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_PROYECTO>
```

### 2. Configurar los Permisos
Para mejorar la seguridad, asegúrate de que la carpeta `docker/` tenga los permisos adecuados:
```bash
chmod 600 -R docker/
```
Esto evitará que otros usuarios en el sistema puedan leer archivos sensibles de configuración.

### 3. Construir la Imagen Docker
Ejecuta el siguiente comando para construir la imagen:
```bash
sudo docker build -t subnetx-openvpn -f docker/subnetx.Dockerfile .
```

### 4. Ejecutar el Contenedor
Para iniciar el contenedor y configurar OpenVPN:
```bash
sudo docker run --name subnetx-openvpn -d --rm --cap-add=NET_ADMIN \
    -p 1194:1194/udp \
    --device=/dev/net/tun:/dev/net/tun \
    -v ./client:/etc/openvpn/client \
    subnetx-openvpn
```

### 5. Ejecutar la Configuración Inicial
Ahora `subnetx setup` admite **parámetros de entrada** para personalizar la configuración del servidor OpenVPN:
```bash
sudo docker exec -it subnetx-openvpn subnetx setup \
    --network 10.9.0.0 \
    --netmask 255.255.255.0 \
    --port 1994 \
    --proto udp \
    --tun tun1 \
    --ip myvpn.example.com
```

Si prefieres ejecutarlo manualmente dentro del contenedor:
```bash
sudo docker exec -it subnetx-openvpn /bin/bash
subnetx setup --network 10.9.0.0 --netmask 255.255.255.0 --port 1195 --proto udp --tun tun1 --ip myvpn.example.com
```

### 6. Administrar Clientes VPN
Para añadir un cliente:
```bash
sudo docker exec -it subnetx-openvpn subnetx client new --name cliente1 --ip 10.9.0.10
```

### 7. Detener y Eliminar el Contenedor
Para detener el contenedor:
```bash
sudo docker stop subnetx-openvpn
```

## 📌 Notas Importantes
- **Es necesario abrir el o los puertos a usar por la VPN en el router con el protocolo correspondiente.**
- **Ejecuta siempre el contenedor como `root`** para evitar problemas de permisos.
- **Los comandos dentro del contenedor también deben ejecutarse como `root`**.
- Si modificas `docker/config/openvpn/`, recuerda reconstruir la imagen.

## 📖 Información Adicional
Para más detalles sobre OpenVPN y su configuración avanzada, visita la documentación oficial:
🔗 [OpenVPN Documentation](https://openvpn.net/community-resources/)

