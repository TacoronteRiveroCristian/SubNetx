#!/bin/bash
cat <<EOF
Uso: $(basename "$0") {setup|start|stop|client {new|delete} [opciones]}

Comandos:
  setup         Configura OpenVPN y genera certificados.
  start         Inicia el servicio OpenVPN.
  stop          Detiene el servicio OpenVPN.
  client new    Crea un nuevo cliente (requiere --name y --ip).
  client delete Elimina un cliente.

Variables de entorno requeridas para setup:
  VPN_NETWORK      - Red VPN (ej: 10.8.0.0)
  VPN_NETMASK      - Mascara de red VPN (ej: 255.255.255.0)
  OPENVPN_PORT     - Puerto OpenVPN (ej: 1194)
  OPENVPN_PROTO    - Protocolo (udp/tcp)
  TUN_DEVICE       - Dispositivo TUN (ej: tun0)
  PUBLIC_IP        - IP publica del servidor

Rutas importantes:
  Certificados     - /etc/openvpn/certs
  Configuraciones  - /etc/openvpn/ccd
  Logs             - /var/log/openvpn
  Clientes         - /etc/openvpn/clients

Para montar volumenes en Docker:
  volumes:
    - ./certs:/etc/openvpn/certs
    - ./logs:/var/log/openvpn
    - ./clients:/etc/openvpn/clients

Ejemplo de configuracion en .env:
  VPN_NETWORK=10.8.0.0
  VPN_NETMASK=255.255.255.0
  OPENVPN_PORT=1194
  OPENVPN_PROTO=udp
  TUN_DEVICE=tun0
  PUBLIC_IP=ejemplo.com
EOF
