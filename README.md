# VPN Sencilla con Docker

Este documento describe los pasos para configurar y ejecutar una VPN sencilla utilizando Docker.

## Pre-requisitos

- Docker instalado en tu máquina.
- Acceso a una terminal o línea de comandos.

## Construir la Imagen Docker

Primero, construye la imagen Docker para el servidor VPN:

`docker build -t subnetx-openvpn -f docker/subnetx.Dockerfile .`

Este comando construye una imagen Docker llamada `subnetx-openvpn` utilizando el Dockerfile especificado en `docker/subnetx.Dockerfile`.

## Ejecutar el Contenedor VPN

Con la imagen construida, puedes iniciar el contenedor:

```bash
docker run --name subnetx-openvpn -d --rm --cap-add=NET_ADMIN \
    -p 1194:1194/udp \
    --device=/dev/net/tun:/dev/net/tun \
    -v ./client:/etc/openvpn/client \
    subnetx-openvpn
```

Este comando ejecuta el contenedor en modo detenido (`-d`), lo que significa que el contenedor se ejecutará en segundo plano. El argumento `--rm` indica que el contenedor se eliminará automáticamente cuando se detenga. Se otorgan capacidades de administrador de red (`NET_ADMIN`) y se monta el dispositivo TUN/TAP necesario para la VPN.

## Configurar el Servicio VPN

Para configurar el servicio VPN dentro del contenedor con todos los certificados y claves necesarios, se debe de ejecutar en primer lugar
el siguiente comando:

`docker exec -it subnetx-openvpn subnetx setup`

Este comando utiliza `docker exec` para ejecutar el script `subnetx` dentro del contenedor `subnetx-openvpn`.

### Control del servidor VPN

Una vez listo el contenedor, se puede iniciar el servicio VPN mediante el siguiente comando:

`docker exec -it subnetx-openvpn subnetx start`

En el caso de que se inicie de forma satisfactoria, aparecerán unos mensajes indicando que el servicio VPN se ha iniciado correctamente y el estado de la interfaz TUN.

Por otro lado, en el caso de que se desee parar el servicio, simplemente hay que ejecutar este otro comando:

`docker exec -it subnetx-openvpn subnetx stop`

En este caso, se busca el PID del proceso OpenVPN y se utiliza `kill` para detenerlo completamente.

## Generar Clientes VPN

Una vez que se ha iniciado el servicio VPN, se puede generar los clientes VPN necesarios ejecutando el siguiente comando:

`docker exec -it subnetx-openvpn subnetx client new <client name>`

Dichos clientes, aparecerán en la carpeta `/etc/openvpn/client` dentro del contenedor los cuales se encuentran conectados con la carpeta host `client`. De esta forma, se pueden generar tantos clientes VPN como se desee y distribuirlos de manera sencilla.

## Detener y Eliminar el Contenedor

Para eliminar el contenedor, simplemente hay que ejecutar:

`docker rm -f subnetx-openvpn`

De esta forma se elimina el contenedor y se libera el espacio en disco además de dar de baja todos los cliente VPN creados.

## Notas Adicionales

- El servidor y el cliente debem de operar en redes distintas. No se puede establecer el túnel correctamente si ambos dispositivos se encuentran en la red 192.168.1.1 por ejemplo.
