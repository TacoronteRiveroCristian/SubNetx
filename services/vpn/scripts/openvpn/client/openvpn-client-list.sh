#!/bin/bash
# openvpn-client-list.sh - Script to list OpenVPN clients
# Description: Lists all OpenVPN clients configured in the system
# by examining configuration files and certificates.
# Author: SubNetx Team
# Version: 1.0.0

# Verify that environment variables are defined
if [ -z "${CLIENTS_DIR}" ] || [ -z "${EASYRSA_DIR}" ]; then
    echo "ERROR: Environment variables CLIENTS_DIR or EASYRSA_DIR not defined."
    exit 1
fi

# Method 1: List clients from .ovpn files
if [ -d "${CLIENTS_DIR}" ]; then
    OVPN_CLIENTS=$(find "${CLIENTS_DIR}" -name "*.ovpn" 2>/dev/null | sed 's/.*\///' | sed 's/\.ovpn$//')
fi

# Method 2: List clients from CCD (Client Config Directory) files
if [ -d "${CCD_DIR}" ]; then
    CCD_CLIENTS=$(find "${CCD_DIR}" -type f 2>/dev/null | sed 's/.*\///')
fi

# Method 3: List clients from issued certificates
if [ -d "${EASYRSA_DIR}/pki/issued" ]; then
    CERT_CLIENTS=$(find "${EASYRSA_DIR}/pki/issued" -name "*.crt" 2>/dev/null | grep -v "server.crt" | sed 's/.*\///' | sed 's/\.crt$//')
fi

# Combine all sources and remove duplicates
ALL_CLIENTS=$(echo -e "${OVPN_CLIENTS}\n${CCD_CLIENTS}\n${CERT_CLIENTS}" | sort | uniq | grep -v "^$")

# If there are no clients, display informative message
if [ -z "${ALL_CLIENTS}" ]; then
    echo "No OpenVPN clients configured."
    exit 0
fi

# Display the client list
echo "${ALL_CLIENTS}"
exit 0
