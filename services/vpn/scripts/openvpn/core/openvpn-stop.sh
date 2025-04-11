#!/bin/bash
# Description: Stops the OpenVPN service and cleans up iptables rules.
# Uses environment variables defined in the Dockerfile for consistency.

# Function to handle errors
handle_error() {
    echo "Error: $1" # Shows error message
    echo "Error: Could not stop OpenVPN correctly." # Indicates stop failure
    exit 1 # Exits with error code
}

echo "Stopping OpenVPN..."

# Before stopping the service, save a copy of logs with timestamp
# to maintain a history of previous sessions
if [ -f "${LOGS_DIR}/openvpn.log" ]; then # If log file exists
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S") # Generate timestamp
    echo "Saving log copy with timestamp: $TIMESTAMP"
    cp "${LOGS_DIR}/openvpn.log" "${LOGS_DIR}/openvpn_${TIMESTAMP}.log" # Copy with timestamp
    cp "${LOGS_DIR}/status.log" "${LOGS_DIR}/status_${TIMESTAMP}.log" 2>/dev/null # Copy with timestamp
    # Adjust copy permissions
    chmod 644 "${LOGS_DIR}/openvpn_${TIMESTAMP}.log" "${LOGS_DIR}/status_${TIMESTAMP}.log" 2>/dev/null
fi

# Check if PID file exists
if [ -f "${OPENVPN_PID_FILE}" ]; then # Use environment variable defined in the Dockerfile
    # Read PID from file
    PID=$(cat "${OPENVPN_PID_FILE}") # Get PID from file

    # Check if process exists
    if kill -0 "$PID" 2>/dev/null; then # Check if process is running
        echo "Stopping OpenVPN process (PID: $PID)..."
        if ! kill "$PID"; then # Try to stop the process
            handle_error "Could not stop the process with normal kill"
        fi

        # Wait for process to terminate
        for i in {1..10}; do # Wait up to 10 seconds
            if ! kill -0 "$PID" 2>/dev/null; then # Check if process has terminated
                echo "OpenVPN process stopped successfully."
                break # Exit loop if process has terminated
            fi
            sleep 1 # Wait 1 second before checking again
        done

        # If process is still active, use kill -9
        if kill -0 "$PID" 2>/dev/null; then # If process is still running
            echo "Warning: Forcing process termination..."
            if ! kill -9 "$PID"; then # Force process termination
                handle_error "Could not stop the process with kill -9"
            fi
            echo "OpenVPN process forced to stop."
        fi
    else
        echo "Warning: OpenVPN process is no longer running."
    fi
else
    echo "Warning: OpenVPN PID file not found."
fi

# Stop any OpenVPN process that might be running
echo "Checking remaining OpenVPN processes..."
if pgrep -f "openvpn.*server.conf" > /dev/null; then # Look for running OpenVPN processes
    echo "Stopping remaining OpenVPN processes..."
    if ! pkill -f "openvpn.*server.conf"; then # Terminate all OpenVPN processes
        handle_error "Could not stop remaining OpenVPN processes"
    fi
    echo "Remaining OpenVPN processes stopped."
fi

# Check if TUN interface is active
if ip link show "${TUN_DEVICE}" >/dev/null 2>&1; then # Check if TUN interface exists
    echo "Deactivating interface ${TUN_DEVICE}..."
    if ! ip link set "${TUN_DEVICE}" down; then # Deactivate TUN interface
        handle_error "Could not deactivate interface ${TUN_DEVICE}"
    fi
    echo "Interface ${TUN_DEVICE} deactivated."
fi

# Clean iptables rules
echo "Cleaning iptables rules..."
if ! iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null; then # Remove NAT rule for eth0
    echo "Info: MASQUERADE rule for eth0 not found"
fi
if ! iptables -t nat -D POSTROUTING -o lo -j MASQUERADE 2>/dev/null; then # Remove NAT rule for loopback
    echo "Info: MASQUERADE rule for lo not found"
fi

# Delete PID file if it exists
if [ -f "${OPENVPN_PID_FILE}" ]; then # Use environment variable defined in the Dockerfile
    if ! rm "${OPENVPN_PID_FILE}"; then # Delete PID file
        handle_error "Could not delete PID file"
    fi
    echo "PID file deleted."
fi

echo "OpenVPN stopped successfully."
echo "Logs from this session have been saved with timestamp for future reference."
