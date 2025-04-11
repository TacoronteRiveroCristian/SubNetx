#!/bin/bash
# Description: Script to stop OpenVPN and remove all certificates and clients.
# This script allows for completely resetting the OpenVPN configuration,
# removing all certificates, keys, and client configurations.
# Author: SubNetx Team
# Version: 1.0.0

# Function to handle errors
handle_error() {
    echo "ERROR: $1"
    echo "Process failed: The cleanup process did not complete successfully."
    exit 1
}

echo "INFO: Starting complete OpenVPN cleanup process..."

# Check if OpenVPN is running before attempting to stop it
vpn_status=$(/app/scripts/openvpn/core/openvpn-status.sh)
if [[ "$vpn_status" == *"status: running"* ]]; then
    # Only attempt to stop if running
    echo "INFO: Stopping OpenVPN service..."
    if ! /app/scripts/openvpn/core/openvpn-stop.sh; then
        handle_error "Failed to stop OpenVPN server"
    fi
    echo "INFO: OpenVPN service stopped successfully."
else
    echo "INFO: OpenVPN is not running, continuing with cleanup..."
fi

# Verify required environment variables
required_vars=(
    "OPENVPN_DIR"
    "CERTS_DIR"
    "EASYRSA_DIR"
    "CLIENTS_DIR"
    "CCD_DIR"
    "SERVER_CONF_DIR"
)

missing_vars=() # Initialize array for missing variables

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then # Check if variable is empty
        missing_vars+=("$var") # Add missing variable to array
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then # If there are missing variables
    echo "ERROR: The following environment variables are missing:"
    printf '%s\n' "${missing_vars[@]}" # Print each missing variable
    exit 1 # Exit with error
fi

# Remove all client certificates and keys
echo "INFO: Removing client certificates and keys..."

# Get client list
CLIENT_LIST=$(/app/scripts/openvpn/client/openvpn-client-list.sh)

# Check if there are any clients to remove
if [ -n "$CLIENT_LIST" ] && [ "$CLIENT_LIST" != "No OpenVPN clients configured." ]; then
    echo "   INFO: Found clients to remove."
    while IFS= read -r client; do
        echo "   INFO: Removing client: $client"
        if ! /app/scripts/openvpn/client/openvpn-client-delete.sh "$client"; then
            echo "   WARNING: Error removing client $client, continuing process..."
        fi
    done <<< "$CLIENT_LIST"
    echo "   INFO: All clients have been removed."
else
    echo "   INFO: No clients found to remove."
fi

# Remove clients directory
echo "INFO: Removing clients directory..."
if [ -d "$CLIENTS_DIR" ]; then
    rm -rf "$CLIENTS_DIR"/*
    echo "   INFO: Clients directory cleaned: $CLIENTS_DIR"
fi

# Remove CCD (Client Config Directory)
echo "INFO: Removing client configuration directory (CCD)..."
if [ -d "$CCD_DIR" ]; then
    rm -rf "$CCD_DIR"/*
    echo "   INFO: CCD directory cleaned: $CCD_DIR"
fi

# Remove server certificates and keys
echo "INFO: Removing server certificates and keys..."
if [ -d "$CERTS_DIR" ]; then
    # Preserve directory but remove content
    rm -rf "$CERTS_DIR"/* 2>/dev/null
    echo "   INFO: Server certificates and keys removed: $CERTS_DIR"
fi

# Remove PKI (Public Key Infrastructure)
echo "INFO: Removing PKI structure..."
if [ -d "$EASYRSA_DIR/pki" ]; then
    rm -rf "$EASYRSA_DIR/pki"
    echo "   INFO: PKI structure removed: $EASYRSA_DIR/pki"
fi

# Create certificate directory if it doesn't exist
mkdir -p "$CERTS_DIR"
mkdir -p "$CERTS_DIR/clients"
mkdir -p "$CLIENTS_DIR"
mkdir -p "$CCD_DIR"

# Adjust permissions
chmod 755 "$CERTS_DIR" "$CERTS_DIR/clients" "$CLIENTS_DIR" "$CCD_DIR"

echo "INFO: Cleaning server configuration..."
# Remove server configuration file
if [ -f "$SERVER_CONF_DIR/server.conf" ]; then
    rm -f "$SERVER_CONF_DIR/server.conf"
    echo "   INFO: Server configuration removed: $SERVER_CONF_DIR/server.conf"
fi

# Remove JSON configuration file
if [ -f "$OPENVPN_DIR/vpn_config.json" ]; then
    rm -f "$OPENVPN_DIR/vpn_config.json"
    echo "   INFO: JSON configuration file removed: $OPENVPN_DIR/vpn_config.json"
fi

echo "SUCCESS: OpenVPN cleanup completed successfully."
echo "INFO: You can now run openvpn-setup.sh to reconfigure OpenVPN."
echo "INFO: All certificates, keys, and client configurations have been removed."

exit 0
