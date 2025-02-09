# SubnetX OpenVPN Container

Este proyecto proporciona una imagen de Docker optimizada para gestionar un servidor **OpenVPN** con herramientas de configuración automatizadas. La imagen contiene los paquetes necesarios para instalar, configurar y administrar OpenVPN de manera segura y eficiente.

## 📌 Características
- Basado en **Ubuntu 22.04**.
- Incluye **OpenVPN, Easy-RSA, iptables y otras utilidades necesarias**.
- Configuración automatizada con el comando `subnetx setup`.
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
docker build -t subnetx-openvpn .
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
Para configurar OpenVPN, generar certificados y aplicar reglas de iptables, usa:
```bash
sudo docker exec -it subnetx-openvpn subnetx setup
```
También puedes acceder al contenedor y ejecutarlo manualmente:
```bash
sudo docker exec -it subnetx-openvpn bash
sudo subnetx setup
```

### 6. Administrar Clientes VPN
Para añadir un cliente:
```bash
sudo docker exec -it subnetx-openvpn subnetx client new --name cliente1 --ip 10.8.0.10
```

### 7. Detener y Eliminar el Contenedor
Para detener el contenedor:
```bash
sudo docker stop subnetx-openvpn
```

## 📌 Notas Importantes
- **Ejecuta siempre el contenedor como `root`** para evitar problemas de permisos.
- **Los comandos dentro del contenedor también deben ejecutarse como `root`**.
- Si modificas `docker/config/openvpn/`, recuerda reconstruir la imagen.

## 📖 Información Adicional
Para más detalles sobre OpenVPN y su configuración avanzada, visita la documentación oficial:
🔗 [OpenVPN Documentation](https://openvpn.net/community-resources/)

---
📌 **Mantenido por:** Tu equipo de administración VPN 🚀

