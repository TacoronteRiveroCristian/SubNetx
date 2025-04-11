#!/bin/bash
# Description: Script to restart the OpenVPN server
# This script stops and restarts the OpenVPN server if it's running.
# Author: SubNetx Team
# Version: 1.0.0

# Function to handle errors
handle_error() {
    echo "ERROR: $1"
    echo "Process failed: The reset process did not complete successfully."
    exit 1
}

echo "INFO: Starting OpenVPN reset process..."

# Check if OpenVPN is running before attempting to restart it
vpn_status=$(/app/scripts/openvpn/core/openvpn-status.sh)
if [[ "$vpn_status" == *"status: running"* ]]; then
    # Only stop and restart if the service is running
    echo "INFO: Stopping OpenVPN service..."
    if ! /app/scripts/openvpn/core/openvpn-stop.sh; then
        handle_error "Failed to stop OpenVPN server"
    fi
    echo "INFO: OpenVPN service stopped successfully."

    echo "INFO: Starting OpenVPN service..."
    if ! /app/scripts/openvpn/core/openvpn-start.sh; then
        handle_error "Failed to start OpenVPN server"
    fi
    echo "INFO: OpenVPN service started successfully."

    echo "SUCCESS: OpenVPN reset completed successfully."
else
    echo "INFO: OpenVPN is not running, no restart necessary."
    echo "INFO: To start the service, run the openvpn-start.sh command."
fi

exit 0
