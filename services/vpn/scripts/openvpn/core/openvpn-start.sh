#!/bin/bash
# Description: Starts OpenVPN in the background, saves its PID and verifies the connection.
# Uses environment variables defined in the Dockerfile for consistency.

# Function to read JSON configuration file
read_config() {
    local config_file="$OPENVPN_DIR/vpn_config.json"

    if [ ! -f "$config_file" ]; then
        echo "Warning: JSON configuration file not found. Using environment variables..."
        return 1
    fi

    # Read variables from JSON
    export VPN_NETWORK=$(jq -r '.vpn_network' "$config_file")
    export VPN_NETMASK=$(jq -r '.vpn_netmask' "$config_file")
    export OPENVPN_PORT=$(jq -r '.openvpn_port' "$config_file")
    export OPENVPN_PROTO=$(jq -r '.openvpn_proto' "$config_file")
    export TUN_DEVICE=$(jq -r '.tun_device' "$config_file")
    export PUBLIC_IP=$(jq -r '.public_ip' "$config_file")

    echo "Configuration read from JSON file"
}

# Read configuration from JSON
read_config

echo "Starting OpenVPN in the background..."

# Ensure logs directory exists and has correct permissions
echo "Verifying logs directory..."
mkdir -p "$LOGS_DIR" # Create logs directory if it doesn't exist
touch "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Create log files if they don't exist
chmod 644 "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Set read permissions for everyone
chown root:root "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Set root ownership

# Verify that certificates exist in the correct directory
for cert in ca.crt server.crt server.key dh.pem ta.key; do # Iterate through each required certificate
    if [ ! -f "$CERTS_DIR/$cert" ]; then # If certificate doesn't exist
        echo "Error: File $cert not found in $CERTS_DIR"
        echo "Please run the configuration script first: openvpn-setup.sh"
        exit 1 # Exit with error
    fi
done

# Check if server.conf exists
if [ ! -f "${SERVER_CONF_DIR}/server.conf" ]; then # If configuration file doesn't exist
    echo "Error: Server configuration file not found"
    echo "Please run the configuration script first: openvpn-setup.sh"
    exit 1 # Exit with error
fi

# Start OpenVPN in the background with `--daemon`
openvpn --config "${SERVER_CONF_DIR}/server.conf" --daemon # Start OpenVPN in the background

# Wait 2 seconds for OpenVPN to create the process
sleep 2 # Pause to give OpenVPN time to start

# Get OpenVPN process PID
PID=$(pgrep -f "openvpn --config ${SERVER_CONF_DIR}/server.conf") # Get process ID

if [ -z "$PID" ]; then # If PID not found
    echo "Error: OpenVPN is not running."
    echo "Check the logs in ${LOGS_DIR}/openvpn.log for more information."
    exit 1 # Exit with error
fi

# Save the PID
echo "$PID" > "${OPENVPN_PID_FILE}" # Save PID to a file

echo "OpenVPN started successfully in the background (PID: $PID)."

# Wait a few seconds to ensure OpenVPN establishes the network
sleep 3 # Pause to give time for the network interface to be established

# Check if TUN interface is active
if ip a show "${TUN_DEVICE}" > /dev/null 2>&1; then # If TUN interface exists
    echo "TUN interface status:"
    ip a show "${TUN_DEVICE}" # Show interface information

    # Extract the first three octets and add ".1"
    VPN_GATEWAY="${VPN_NETWORK%.*}.1" # Calculate gateway IP address

    # Ping VPN IP to verify connectivity
    echo "Testing VPN connection to ${VPN_GATEWAY}..."
    if ping -c 1 "${VPN_GATEWAY}" > /dev/null 2>&1; then # Send ping to gateway
        echo "OpenVPN is active and working correctly."
    else
        echo "Warning: OpenVPN is running, but connection to ${VPN_GATEWAY} failed."
    fi

else
    echo "Error: Interface ${TUN_DEVICE} was not created."
    echo "Check the logs in ${LOGS_DIR}/openvpn.log for more information."
    exit 1 # Exit with error
fi

# Fix log permissions after starting the service
echo "Adjusting log file permissions..."
sleep 2 # Wait to ensure OpenVPN has created/updated logs
chmod 644 "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Set read permissions for everyone
