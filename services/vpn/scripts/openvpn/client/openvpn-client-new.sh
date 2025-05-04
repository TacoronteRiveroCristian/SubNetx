#!/bin/bash
# Description: Generates a certificate and configuration for a new OpenVPN client with a fixed IP.
# Uses environment variables defined in the Dockerfile for consistency.

# First, verify that PKI infrastructure is properly initialized
if ! /app/scripts/openvpn/client/openvpn-client-verify-pki.sh; then
    echo "Error: PKI verification failed. Cannot create client."
    echo "Please run openvpn-setup.sh first and ensure the server is properly configured."
    exit 1
fi

# Check if configuration file exists (redundant but kept for backward compatibility)
if [ ! -f "$OPENVPN_DIR/vpn_config.json" ]; then
    echo "Error: Configuration file not found at $OPENVPN_DIR/vpn_config.json"
    echo "Run openvpn-setup.sh first to generate the configuration."
    exit 1
fi

# Load configuration from JSON file
echo "Loading configuration from $OPENVPN_DIR/vpn_config.json"
VPN_NETWORK=$(jq -r '.vpn_network' "$OPENVPN_DIR/vpn_config.json")
VPN_NETMASK=$(jq -r '.vpn_netmask' "$OPENVPN_DIR/vpn_config.json")
OPENVPN_PORT=$(jq -r '.openvpn_port' "$OPENVPN_DIR/vpn_config.json")
OPENVPN_PROTO=$(jq -r '.openvpn_proto' "$OPENVPN_DIR/vpn_config.json")
TUN_DEVICE=$(jq -r '.tun_device' "$OPENVPN_DIR/vpn_config.json")
PUBLIC_IP=$(jq -r '.public_ip' "$OPENVPN_DIR/vpn_config.json")

# Verificar explícitamente el valor de PUBLIC_IP
if [ "$PUBLIC_IP" = "localhost" ] || [ "$PUBLIC_IP" = "127.0.0.1" ]; then
    echo "ADVERTENCIA: La IP pública en el archivo de configuración es localhost o 127.0.0.1"
    echo "Intentando obtener la IP pública automáticamente..."

    # Intentar obtener la IP pública automáticamente
    AUTO_IP=$(curl -s https://api.ipify.org || wget -qO- https://api.ipify.org)

    if [ -n "$AUTO_IP" ] && [ "$AUTO_IP" != "localhost" ] && [ "$AUTO_IP" != "127.0.0.1" ]; then
        echo "Se obtuvo la IP pública automáticamente: $AUTO_IP"
        PUBLIC_IP="$AUTO_IP"
        # Actualizar el archivo JSON con la IP correcta
        TMP_JSON=$(mktemp)
        jq --arg ip "$PUBLIC_IP" '.public_ip = $ip' "$OPENVPN_DIR/vpn_config.json" > "$TMP_JSON" && mv "$TMP_JSON" "$OPENVPN_DIR/vpn_config.json"
        echo "Archivo de configuración actualizado con la IP pública: $PUBLIC_IP"
    else
        echo "No se pudo obtener la IP pública automáticamente."
        echo "Por favor, proporcione una IP pública válida al ejecutar openvpn-setup.sh"
    fi
fi

# Debug: mostrar el valor de PUBLIC_IP
echo "DEBUG: Valor final de PUBLIC_IP: $PUBLIC_IP"

# Verify that all required variables were loaded
if [ -z "$VPN_NETWORK" ] || [ -z "$VPN_NETMASK" ] || [ -z "$OPENVPN_PORT" ] || \
   [ -z "$OPENVPN_PROTO" ] || [ -z "$TUN_DEVICE" ] || [ -z "$PUBLIC_IP" ]; then
    echo "Error: The configuration file does not contain all the necessary variables"
    exit 1
fi

CLIENT_NAME="" # Client name
CLIENT_IP="" # Fixed IP assigned to the client

# Parse arguments
while [[ "$#" -gt 0 ]]; do # For each argument in the command line
    case "$1" in
        --name) # If the argument is --name
            CLIENT_NAME="$2" # Assign the next argument as client name
            shift 2 # Advance two positions
            ;;
        --ip) # If the argument is --ip
            CLIENT_IP="$2" # Assign the next argument as client IP
            shift 2 # Advance two positions
            ;;
        *) # If it's any other argument
            echo "Error: Unknown option $1" # Show error
            /app/scripts/utils/openvpn-help.sh # Show help
            exit 1 # Exit with error
            ;;
    esac
done

# Validate parameters
if [[ -z "$CLIENT_NAME" || -z "$CLIENT_IP" ]]; then # If name or IP is missing
    echo "Error: You must specify a name and an IP for the client."
    /app/scripts/utils/openvpn-help.sh # Show help
    exit 1 # Exit with error
fi

echo "Creating certificate and key for client: $CLIENT_NAME"

# Check if the necessary server certificates exist
if [ ! -f "$CERTS_DIR/ca.crt" ] || [ ! -f "$CERTS_DIR/ta.key" ]; then # If server certificates are missing
    echo "Error: The necessary server certificates were not found."
    echo "Run openvpn-setup.sh first to generate the server certificates."
    exit 1 # Exit with error
fi

# Move to Easy-RSA directory
cd "$EASYRSA_DIR" || { echo "Error: Could not access $EASYRSA_DIR"; exit 1; }

# Build client certificate
./easyrsa --batch build-client-full "$CLIENT_NAME" nopass # Generate certificate without password

# Verify if files were created correctly
if [ ! -f "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" ] || [ ! -f "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key" ]; then # If files don't exist
    echo "Error: Client files were not generated correctly."
    exit 1 # Exit with error
fi

# Copy client certificates to centralized directory
echo "Copying client certificates to centralized location..."
mkdir -p "$CERTS_DIR/clients/$CLIENT_NAME" # Create specific directory for the client
cp "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" "$CERTS_DIR/clients/$CLIENT_NAME/" # Copy certificate
cp "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key" "$CERTS_DIR/clients/$CLIENT_NAME/" # Copy private key

echo "Certificate and key generated for $CLIENT_NAME."

# Create client configuration file on the server (CCD)
CCD_FILE="$CCD_DIR/$CLIENT_NAME" # Path to client configuration file
echo "Assigning fixed IP to client in: $CCD_FILE"

mkdir -p "$CCD_DIR" # Ensure directory exists
echo "ifconfig-push $CLIENT_IP $VPN_NETMASK" | tee "$CCD_FILE" > /dev/null # Create CCD file with fixed IP

# Ensure clients directory exists
mkdir -p "$CLIENTS_DIR" # Create directory for client configuration files

# Create client configuration profile (.ovpn with everything embedded)
CLIENT_CONFIG="$CLIENTS_DIR/$CLIENT_NAME.ovpn" # Path to configuration file
CLIENT_CONFIG_COPY="$CERTS_DIR/clients/$CLIENT_NAME/$CLIENT_NAME.ovpn" # Copy in centralized directory

echo "Creating client configuration file: $CLIENT_CONFIG"
echo "Using PUBLIC_IP: $PUBLIC_IP for the remote server"

# Asegurarse de que PUBLIC_IP no sea localhost antes de crear el archivo
if [ "$PUBLIC_IP" = "localhost" ] || [ "$PUBLIC_IP" = "127.0.0.1" ]; then
    echo "ERROR: La IP pública aún es localhost. No se puede crear un archivo de configuración válido."
    echo "Ejecute openvpn-setup.sh con el parámetro --ip correcto."
    exit 1
fi

cat > "$CLIENT_CONFIG" <<EOF
client
dev $TUN_DEVICE
proto $OPENVPN_PROTO
remote $PUBLIC_IP $OPENVPN_PORT
resolv-retry infinite
nobind
user nobody
group nogroup
persist-key
persist-tun
remote-cert-tls server
data-ciphers AES-256-GCM:AES-128-GCM:AES-256-CBC
auth SHA256
verb 3
key-direction 1
EOF

# Include certificates in the embedded .ovpn file
{
    echo "<ca>"
    cat "$CERTS_DIR/ca.crt" # Use the CA certificate from centralized directory
    echo "</ca>"

    echo "<cert>"
    cat "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt"
    echo "</cert>"

    echo "<key>"
    cat "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key"
    echo "</key>"

    echo "<tls-auth>"
    cat "$CERTS_DIR/ta.key" # Use the TLS key from centralized directory
    echo "</tls-auth>"
} >> "$CLIENT_CONFIG"

# Create a copy of the configuration file in the centralized directory
cp "$CLIENT_CONFIG" "$CLIENT_CONFIG_COPY" # Copy the configuration file

# Set correct permissions
chmod 600 "$CERTS_DIR/clients/$CLIENT_NAME/$CLIENT_NAME.key" "$CERTS_DIR/ta.key"
chmod 644 "$CERTS_DIR/clients/$CLIENT_NAME/$CLIENT_NAME.crt" "$CERTS_DIR/ca.crt" "$CLIENT_CONFIG" "$CLIENT_CONFIG_COPY"

echo "Client created successfully with fixed IP: $CLIENT_IP"
echo "OVPN file (all embedded): $CLIENT_CONFIG"
echo "Backup copy in: $CLIENT_CONFIG_COPY"
echo "Remote server configured as: $PUBLIC_IP:$OPENVPN_PORT"
echo "All certificates and client files have been saved in: $CERTS_DIR/clients/$CLIENT_NAME"
