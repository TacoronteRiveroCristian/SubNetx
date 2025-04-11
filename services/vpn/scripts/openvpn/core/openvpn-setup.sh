#!/bin/bash
# Description: Configures OpenVPN, generates certificates, enables packet forwarding and configures NAT.
# The paths are defined as environment variables in the Dockerfile for greater consistency.

# Function to handle errors
handle_error() {
    echo "Error: $1" # Shows error message
    echo "Error: The configuration was not completed correctly." # Indicates configuration failure
    exit 1 # Terminates with error code
}

# Function to show help
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --red <ip>        VPN Network (e.g.: 10.10.10.0)"
    echo "  --mask <mask>     Network mask (e.g.: 255.255.255.0)"
    echo "  --port <port>     OpenVPN Port (e.g.: 1194)"
    echo "  --proto <proto>   Protocol (udp/tcp)"
    echo "  --tun <device>    TUN Device (e.g.: tun0)"
    echo "  --ip <ip>         Public IP or domain"
    echo "  --help           Show this help"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --red)
            VPN_NETWORK="$2"
            shift 2
            ;;
        --mask)
            VPN_NETMASK="$2"
            shift 2
            ;;
        --port)
            OPENVPN_PORT="$2"
            shift 2
            ;;
        --proto)
            OPENVPN_PROTO="$2"
            shift 2
            ;;
        --tun)
            TUN_DEVICE="$2"
            shift 2
            ;;
        --ip)
            PUBLIC_IP="$2"
            shift 2
            ;;
        --help)
            show_help
            ;;
        *)
            echo "Error: Unknown option: $1"
            show_help
            ;;
    esac
done

# ---------------------------
# Validate required environment variables
# ---------------------------
required_vars=(
    "VPN_NETWORK"
    "VPN_NETMASK"
    "OPENVPN_PORT"
    "OPENVPN_PROTO"
    "TUN_DEVICE"
    "PUBLIC_IP"
    "OPENVPN_DIR"
    "CERTS_DIR"
    "SERVER_CONF_DIR"
    "EASYRSA_DIR"
    "LOGS_DIR"
)

missing_vars=() # Initialize array for missing variables

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then # Check if the variable is empty
        missing_vars+=("$var") # Add missing variable to the array
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then # If there are missing variables
    echo "Error: The following environment variables are missing:"
    printf '%s\n' "${missing_vars[@]}" # Print each missing variable
    echo "Please check the help with --help for more information."
    /app/scripts/utils/openvpn-help.sh # Show help
    exit 1 # Exit with error
fi

# Create OpenVPN directory if it doesn't exist
mkdir -p "$OPENVPN_DIR"

# Create JSON configuration file
echo "Creating configuration file..."
cat > "$OPENVPN_DIR/vpn_config.json" << EOF
{
    "vpn_network": "$VPN_NETWORK",
    "vpn_netmask": "$VPN_NETMASK",
    "openvpn_port": $OPENVPN_PORT,
    "openvpn_proto": "$OPENVPN_PROTO",
    "tun_device": "$TUN_DEVICE",
    "public_ip": "$PUBLIC_IP"
}
EOF

# Verify that the file was created correctly
if [ ! -f "$OPENVPN_DIR/vpn_config.json" ]; then
    handle_error "Could not create JSON configuration file"
fi

# Set read permissions for everyone
chmod 644 "$OPENVPN_DIR/vpn_config.json"
echo "Configuration file created in $OPENVPN_DIR/vpn_config.json"

# ---------------------------
# Prepare logs directory
# ---------------------------
# Ensure logs directory exists and has correct permissions
echo "Preparing logs directory..."
mkdir -p "$LOGS_DIR" # Create logs directory if it doesn't exist
touch "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Create log files if they don't exist
chmod 644 "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Set read permissions for everyone
chown root:root "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Set root ownership

# ---------------------------
# Generate server.conf
# ---------------------------
SERVER_CONF="${SERVER_CONF_DIR}/server.conf" # Path to server configuration file
SERVER_TEMPLATE="/app/config/openvpn/server.conf.template" # Path to template

# Verify that the template exists
if [ ! -f "$SERVER_TEMPLATE" ]; then # Check if the template file exists
    handle_error "Server.conf template not found: $SERVER_TEMPLATE"
fi

# Create directory for server configuration if it doesn't exist
mkdir -p "$SERVER_CONF_DIR" # Create directory for configuration

# Use sed to replace placeholders with environment variables
if ! sed -e "s/{{PORT}}/${OPENVPN_PORT}/g" \
    -e "s/{{PROTO}}/${OPENVPN_PROTO}/g" \
    -e "s/{{TUN}}/${TUN_DEVICE}/g" \
    -e "s/{{NETWORK}}/${VPN_NETWORK}/g" \
    -e "s/{{NETMASK}}/${VPN_NETMASK}/g" \
    -e "s|{{LOGS_DIR}}|${LOGS_DIR}|g" \
    "$SERVER_TEMPLATE" > "$SERVER_CONF"; then # Replace variables in the template
    handle_error "Error generating server.conf file"
fi

echo "Server.conf file generated in $SERVER_CONF"

# ---------------------------
# Initialize Easy-RSA if necessary
# ---------------------------
if [ ! -d "$EASYRSA_DIR" ]; then # Check if Easy-RSA directory exists
    echo "Creating and initializing Easy-RSA directory..."
    if ! make-cadir "$EASYRSA_DIR"; then # Initialize Easy-RSA
        handle_error "Could not initialize Easy-RSA"
    fi
    if ! chmod -R 755 "$EASYRSA_DIR"; then # Set permissions
        handle_error "Could not set permissions on Easy-RSA directory"
    fi
else
    echo "Easy-RSA directory already exists."
fi

# Copy vars if available
EASYRSA_VARS_TEMPLATE="/app/config/vars"
if [ -f "$EASYRSA_VARS_TEMPLATE" ]; then # If vars template file exists
    cp "$EASYRSA_VARS_TEMPLATE" "$EASYRSA_DIR/vars" # Copy vars file
    echo "Vars file copied to $EASYRSA_DIR/vars"
fi

# ---------------------------
# Generate certificates and keys
# ---------------------------
echo "Configuring OpenVPN..."

# Move to Easy-RSA directory
cd "$EASYRSA_DIR" || { # Change to Easy-RSA directory
    handle_error "Could not access Easy-RSA directory: $EASYRSA_DIR"
}

# Initialize PKI if it doesn't exist
if [ ! -d "$EASYRSA_DIR/pki" ]; then # Check if PKI exists
    echo "Initializing PKI..."
    if ! ./easyrsa --batch init-pki; then # Initialize PKI
        handle_error "Error initializing PKI"
    fi
fi

# Create CA if it doesn't exist
if [ ! -f "$CERTS_DIR/ca.crt" ]; then # Check if CA certificate exists
    echo "Generating Certificate Authority (CA)..."
    if ! ./easyrsa --batch build-ca nopass; then # Generate CA without password
        handle_error "Error generating CA"
    fi
    if ! cp pki/ca.crt "$CERTS_DIR/"; then # Copy CA certificate to certificates directory
        handle_error "Error copying CA certificate"
    fi
fi

# Create server key and certificate if they don't exist
if [ ! -f "$CERTS_DIR/server.crt" ]; then # Check if server certificate exists
    echo "Generating server key and certificate..."
    if ! ./easyrsa --batch gen-req server nopass; then # Generate certificate request without password
        handle_error "Error generating server key"
    fi
    if ! echo "yes" | ./easyrsa --batch sign-req server server; then # Sign certificate request
        handle_error "Error signing server certificate"
    fi
    if ! cp pki/private/server.key "$CERTS_DIR/"; then # Copy private key to certificates directory
        handle_error "Error copying server key"
    fi
    if ! cp pki/issued/server.crt "$CERTS_DIR/"; then # Copy certificate to certificates directory
        handle_error "Error copying server certificate"
    fi
fi

# Generate Diffie-Hellman if it doesn't exist
if [ ! -f "$CERTS_DIR/dh.pem" ]; then # Check if Diffie-Hellman parameters exist
    echo "Generating Diffie-Hellman..."
    if ! ./easyrsa gen-dh; then # Generate Diffie-Hellman parameters
        handle_error "Error generating Diffie-Hellman parameters"
    fi
    if ! cp pki/dh.pem "$CERTS_DIR/"; then # Copy parameters to certificates directory
        handle_error "Error copying Diffie-Hellman parameters"
    fi
fi

# Generate TLS key if it doesn't exist
if [ ! -f "$CERTS_DIR/ta.key" ]; then # Check if TLS key exists
    echo "Generating TLS key..."
    if ! openvpn --genkey secret "$CERTS_DIR/ta.key"; then # Generate TLS key
        handle_error "Error generating TLS key"
    fi
fi

# Set correct permissions for certificates
chmod 600 "$CERTS_DIR/server.key" # Set restrictive permission for server key
chmod 644 "$CERTS_DIR/ca.crt" "$CERTS_DIR/server.crt" "$CERTS_DIR/dh.pem" # Set read permissions for certificates
chmod 600 "$CERTS_DIR/ta.key" # Set restrictive permission for TLS key

# Create README file in certificates directory
cat > "$CERTS_DIR/README.txt" << EOF
# OpenVPN Certificates Directory

Este directorio contiene todos los certificados y claves necesarios para OpenVPN.
Al montar este directorio como un volumen Docker, se mantiene la persistencia
de los certificados y claves incluso si el contenedor se elimina y recrea.

Contenido:
- ca.crt: Certificado de la Autoridad Certificadora
- server.crt: Certificado del servidor
- server.key: Clave privada del servidor
- dh.pem: Parametros Diffie-Hellman
- ta.key: Clave TLS Auth
- clients/: Directorio con certificados y configuraciones de clientes

Fecha de creacion: $(date)
EOF

# Apply sysctl changes without needing to restart
echo "Configuring packet forwarding..."
if ! sysctl -w net.ipv4.ip_forward=1; then # Enable packet forwarding
    handle_error "Error enabling packet forwarding"
fi
if ! sysctl -p; then # Apply sysctl configuration
    handle_error "Error applying sysctl configuration"
fi

echo "Configuring iptables to route VPN traffic..."
# Modify routing tables
if ! iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE; then # Configure NAT for eth0
    handle_error "Error configuring iptables for eth0"
fi
if ! iptables -t nat -A POSTROUTING -o lo -j MASQUERADE; then # Configure NAT for loopback
    handle_error "Error configuring iptables for lo"
fi

# Verify iptables rules
echo "Applied iptables rules:"
if ! iptables -t nat -L -n -v; then # Show applied NAT rules
    handle_error "Error verifying iptables rules"
fi

echo "OpenVPN configuration completed successfully."
echo "All certificates and keys stored in $CERTS_DIR"
echo "To mount this directory as a Docker volume, add the following line to your docker-compose.yml:"
echo "   volumes:"
echo "     - ./certs:/etc/openvpn/certs"
