#!/bin/bash
# Description: Removes an OpenVPN client by revoking its certificate and deleting all its files.
# Uses environment variables defined in the Dockerfile to maintain consistency.

# Validate that a client name has been provided
if [ -z "$1" ]; then # If no client name is provided
    echo "ERROR: You must specify the name of the client to delete."
    echo "Usage: $0 <client_name>"
    exit 1 # Exit with error
fi

CLIENT_NAME="$1" # Name of the client to delete

echo "INFO: Revoking certificate and deleting client: $CLIENT_NAME"

# Verify if the client exists
if [ ! -f "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" ]; then # If certificate does not exist
    echo "ERROR: Client $CLIENT_NAME does not exist or its certificate was not found."
    exit 1 # Exit with error
fi

# Change to the EasyRSA directory
cd "$EASYRSA_DIR" || {
    echo "ERROR: Could not change to directory $EASYRSA_DIR"
    exit 1
}

# Revoke client certificate
echo "INFO: Revoking client certificate..."
if ./easyrsa --batch revoke "$CLIENT_NAME"; then
    echo "INFO: Certificate for client $CLIENT_NAME revoked successfully."
else
    echo "WARNING: Error revoking certificate for client $CLIENT_NAME."
fi

# Generate new CRL
echo "INFO: Generating updated Certificate Revocation List (CRL)..."
if ./easyrsa gen-crl; then
    echo "INFO: CRL generated successfully."

    # Copy CRL to OpenVPN directory
    cp -f "$EASYRSA_DIR/pki/crl.pem" "$OPENVPN_DIR" || {
        echo "WARNING: Could not copy CRL to $OPENVPN_DIR"
    }
else
    echo "WARNING: Error generating CRL."
fi

# Remove client config file from CCD if it exists
if [ -f "$CCD_DIR/$CLIENT_NAME" ]; then
    echo "INFO: Removing client-specific config from CCD..."
    rm -f "$CCD_DIR/$CLIENT_NAME"
    echo "INFO: Client-specific config removed."
fi

# Remove client .ovpn file if it exists
CLIENT_OVPN_DIR="$CLIENTS_DIR/$CLIENT_NAME"
if [ -d "$CLIENT_OVPN_DIR" ]; then
    echo "INFO: Removing client configuration directory..."
    rm -rf "$CLIENT_OVPN_DIR"
    echo "INFO: Client configuration directory removed."
fi

echo "SUCCESS: Client $CLIENT_NAME has been deleted successfully."
exit 0
