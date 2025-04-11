#!/bin/bash
# openvpn-client-list-json.sh - Script to list OpenVPN clients in JSON format with metadata
# Description: Lists all OpenVPN clients configured in the system with additional metadata
# like IP address and creation date in a JSON format.
# Author: SubNetx Team
# Version: 1.0.0

# Verify that environment variables are defined
if [ -z "${CLIENTS_DIR}" ] || [ -z "${EASYRSA_DIR}" ]; then
    echo "{\"error\": \"Environment variables CLIENTS_DIR or EASYRSA_DIR not defined.\"}"
    exit 1
fi

# Start JSON object
echo "{"
echo "  \"clients\": {"

FIRST_CLIENT=true

# Method 1: List clients from .ovpn files and CCD files to get information
if [ -d "${CLIENTS_DIR}" ] && [ -d "${CCD_DIR}" ]; then
    OVPN_CLIENTS=$(find "${CLIENTS_DIR}" -name "*.ovpn" 2>/dev/null | sed 's/.*\///' | sed 's/\.ovpn$//')

    for client in $OVPN_CLIENTS; do
        # Skip empty client names
        if [ -z "$client" ]; then
            continue
        fi

        # Get client IP from the CCD file
        IP_ADDRESS=""
        if [ -f "${CCD_DIR}/${client}" ]; then
            IP_ADDRESS=$(grep -oP 'ifconfig-push \K[0-9.]+' "${CCD_DIR}/${client}")
        fi

        # Get creation date from the certificate file or ovpn file
        CREATION_DATE=""
        if [ -f "${CERTS_DIR}/clients/${client}/${client}.crt" ]; then
            CREATION_DATE=$(stat -c %y "${CERTS_DIR}/clients/${client}/${client}.crt" | cut -d '.' -f1)
        elif [ -f "${CLIENTS_DIR}/${client}.ovpn" ]; then
            CREATION_DATE=$(stat -c %y "${CLIENTS_DIR}/${client}.ovpn" | cut -d '.' -f1)
        fi

        # Add comma for all but the first client
        if [ "$FIRST_CLIENT" = false ]; then
            echo "    ,"
        else
            FIRST_CLIENT=false
        fi

        # Output client information as JSON
        echo "    \"${client}\": {"
        echo "      \"ip_address\": \"${IP_ADDRESS}\","
        echo "      \"creation_date\": \"${CREATION_DATE}\""
        echo -n "    }"
    done
fi

# Close JSON object
echo ""
echo "  }"
echo "}"
exit 0
