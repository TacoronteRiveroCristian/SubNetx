#!/bin/bash
# openvpn-client-list.sh - Script para listar clientes OpenVPN
# Descripción: Lista todos los clientes OpenVPN configurados en el sistema
# examinando los archivos de configuración y certificados.
# Autor: SubNetx Team
# Versión: 1.0.0

# Verificar que las variables de entorno estén definidas
if [ -z "${CLIENTS_DIR}" ] || [ -z "${EASYRSA_DIR}" ]; then
    echo "Error: Variables de entorno CLIENTS_DIR o EASYRSA_DIR no definidas."
    exit 1
fi

# Método 1: Listar clientes a partir de archivos .ovpn
if [ -d "${CLIENTS_DIR}" ]; then
    OVPN_CLIENTS=$(find "${CLIENTS_DIR}" -name "*.ovpn" 2>/dev/null | sed 's/.*\///' | sed 's/\.ovpn$//')
fi

# Método 2: Listar clientes a partir de archivos en CCD (Cliente Config Directory)
if [ -d "${CCD_DIR}" ]; then
    CCD_CLIENTS=$(find "${CCD_DIR}" -type f 2>/dev/null | sed 's/.*\///')
fi

# Método 3: Listar clientes a partir de certificados emitidos
if [ -d "${EASYRSA_DIR}/pki/issued" ]; then
    CERT_CLIENTS=$(find "${EASYRSA_DIR}/pki/issued" -name "*.crt" 2>/dev/null | grep -v "server.crt" | sed 's/.*\///' | sed 's/\.crt$//')
fi

# Combinar todas las fuentes y eliminar duplicados
ALL_CLIENTS=$(echo -e "${OVPN_CLIENTS}\n${CCD_CLIENTS}\n${CERT_CLIENTS}" | sort | uniq | grep -v "^$")

# Si no hay clientes, mostrar mensaje informativo
if [ -z "${ALL_CLIENTS}" ]; then
    echo "No hay clientes OpenVPN configurados."
    exit 0
fi

# Mostrar la lista de clientes
echo "${ALL_CLIENTS}"
exit 0
