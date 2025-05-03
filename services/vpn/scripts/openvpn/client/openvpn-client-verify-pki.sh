#!/bin/bash
# Description: Verifies that the PKI infrastructure is properly initialized before attempting client creation.
# This script checks for the presence of necessary files and directories before allowing client creation.

# Exit on error
set -e

# Load environment variables if not already set
if [ -z "$EASYRSA_DIR" ] || [ -z "$CERTS_DIR" ] || [ -z "$OPENVPN_DIR" ]; then
    echo "Error: Environment variables not set. Cannot verify PKI infrastructure."
    exit 1
fi

# Function to check if server has been set up
verify_setup() {
    # Check config file
    if [ ! -f "$OPENVPN_DIR/vpn_config.json" ]; then
        echo "Error: Server configuration file not found at $OPENVPN_DIR/vpn_config.json"
        echo "Run openvpn-setup.sh first to configure the server."
        return 1
    fi

    # Check PKI directory
    if [ ! -d "$EASYRSA_DIR/pki" ]; then
        echo "Error: PKI directory not found at $EASYRSA_DIR/pki"
        echo "Run openvpn-setup.sh first to initialize the PKI."
        return 1
    fi

    # Check for serial file
    if [ ! -f "$EASYRSA_DIR/pki/serial" ]; then
        echo "Error: Serial file not found at $EASYRSA_DIR/pki/serial"
        echo "Run openvpn-setup.sh first to initialize the PKI."
        return 1
    fi

    # Check for CA certificate
    if [ ! -f "$CERTS_DIR/ca.crt" ]; then
        echo "Error: CA certificate not found at $CERTS_DIR/ca.crt"
        echo "Run openvpn-setup.sh first to generate CA certificate."
        return 1
    fi

    # Check for server certificate
    if [ ! -f "$CERTS_DIR/server.crt" ]; then
        echo "Error: Server certificate not found at $CERTS_DIR/server.crt"
        echo "Run openvpn-setup.sh first to generate server certificate."
        return 1
    fi

    # Check for server key
    if [ ! -f "$CERTS_DIR/server.key" ]; then
        echo "Error: Server key not found at $CERTS_DIR/server.key"
        echo "Run openvpn-setup.sh first to generate server key."
        return 1
    fi

    # Check for DH parameters
    if [ ! -f "$CERTS_DIR/dh.pem" ]; then
        echo "Error: DH parameters not found at $CERTS_DIR/dh.pem"
        echo "Run openvpn-setup.sh first to generate DH parameters."
        return 1
    fi

    # Check for TLS key
    if [ ! -f "$CERTS_DIR/ta.key" ]; then
        echo "Error: TLS auth key not found at $CERTS_DIR/ta.key"
        echo "Run openvpn-setup.sh first to generate TLS auth key."
        return 1
    fi

    # If we made it here, all checks passed
    return 0
}

# Function to check if server is running
verify_server_running() {
    # Check if openvpn process is running
    if ! pgrep -x "openvpn" > /dev/null; then
        echo "Warning: OpenVPN server is not running."
        echo "Run openvpn-start.sh to start the server."
        return 1
    fi

    return 0
}

# Main verification logic
main() {
    echo "Verifying PKI infrastructure..."

    # Check if server has been set up
    if ! verify_setup; then
        return 1
    fi

    echo "PKI infrastructure is properly initialized."

    # Check if server is running
    if ! verify_server_running; then
        echo "Note: Server is not running, but PKI is correctly initialized."
        echo "You can proceed with client creation, but server should be started for clients to connect."
        return 0
    fi

    echo "OpenVPN server is running and PKI is properly initialized."
    echo "You can safely proceed with client creation."
    return 0
}

# Run verification
main "$@"
exit $?
