#!/bin/bash

# Directorio raiz
export OPENVPN_DIR="/etc/openvpn"

# Servidor OpenVPN
export SERVER_DIR="/etc/openvpn"
export _SERVER_CONF="$BASE_DIR/app/config/openvpn/server.conf"
export SERVER_CONF="${SERVER_DIR}/server.conf"

# Certificados Easy-RSA
export EASYRSA_DIR="/etc/openvpn/easy-rsa"
export _EASYRSA_VAR="$BASE_DIR/app/config/openvpn/vars"
export EASYRSA_VAR="${EASYRSA_DIR}/vars"

# Parametros de la red VPN
export VPN_NETWORK="10.8.0.0"
export VPN_NETMASK="255.255.255.0"

# Otros parametros de configuracion
export OPENVPN_PORT=1194
export OPENVPN_PROTO="udp"
export TUN_DEVICE="tun0"
