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

`docker run --name subnetx-openvpn -d --rm --cap-add=NET_ADMIN -p 1194:1194/udp --device=/dev/net/tun:/dev/net/tun subnetx-openvpn`

Este comando ejecuta el contenedor en modo detenido (`-d`), lo que significa que el contenedor se ejecutará en segundo plano. El argumento `--rm` indica que el contenedor se eliminará automáticamente cuando se detenga. Se otorgan capacidades de administrador de red (`NET_ADMIN`) y se monta el dispositivo TUN/TAP necesario para la VPN.

## Configurar el Servicio VPN

Para iniciar el servicio VPN dentro del contenedor, ejecuta:

`docker exec -it subnetx-openvpn sudo init-vpn.sh`

Este comando utiliza `docker exec` para ejecutar el script `init-vpn.sh` dentro del contenedor `subnetx-openvpn`. Al ser un script com permisos de root, hay que introducirle la contraseña; esto se logra gracias a que el comando docker se ejecuta de forma interfactiva mediante el flag `-it`.

### Control del servidor VPN

Una vez listo el contenedor, se puede iniciar el servicio VPN mediante el siguiente comando:

`docker exec -it subnetx-openvpn sudo start-vpn.sh`

Del mismo modo que se ejecutó el script `start.sh` en la sección anterior, en este caso lo que se ha hecho es iniciar el servidor OpenVPN con las características preconfiguradas. Llegados a este punto, el contenedor docker posee un túnel el cuál hace de pasarela entre los clientes y el servidor VPN.

En el caso que se desee parar el servidor VPN, simplemente hay que ejecutar el comando anterior pero llamando al script `stop-vpn.sh`. Este comando lo que hace es buscar el proceso ejecutado anteriormente y finalizarlo, eliminando así el túnel creado anteriormente.

## Detener y Eliminar el Contenedor

Cuando ya no necesites el servicio VPN, puedes detener y eliminar el contenedor:

`docker rm -f subnetx-openvpn`

Este comando fuerza la detención y eliminación del contenedor `subnetx-openvpn`.

## Notas Adicionales

- El servidor y el cliente debem de operar en redes distintas. No se puede establecer el túnel correctamente si ambos dispositivos se encuentran en la red 192.168.1.1 por ejemplo.
