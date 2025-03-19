#!/bin/bash

# Directorio raiz
OPENVPN_DIR="/etc/openvpn"

# Certificados Easy-RSA
EASYRSA_DIR="${OPENVPN_DIR}/easy-rsa"
EASYRSA_VAR="${EASYRSA_DIR}/vars"
_EASYRSA_VAR="/app/config/openvpn/vars"

# Parametros de la red VPN
VPN_NETWORK="10.8.0.0"
VPN_NETMASK="255.255.255.0"

# Otros parametros de configuracion
OPENVPN_PID_FILE="${OPENVPN_DIR}/openvpn.pid"
PUBLIC_IP="labcrist.duckdns.org"
OPENVPN_PORT="1194"
OPENVPN_PROTO="udp"
TUN_DEVICE="tun0"
