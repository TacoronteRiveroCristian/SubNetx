#!/bin/bash
# openvpn-status.sh - Script to check the status of the OpenVPN server
# Description: Checks if the OpenVPN server is running, its uptime
# and how many clients are currently connected.
# Author: SubNetx Team
# Version: 1.0.0

# Check if PID file exists
if [ -f "${OPENVPN_PID_FILE}" ]; then
    # Read PID from file
    PID=$(cat "${OPENVPN_PID_FILE}")

    # Check if process is running
    if ps -p "${PID}" > /dev/null; then
        # OpenVPN is running
        # Get uptime in seconds
        START_TIME=$(ps -o lstart= -p "${PID}")
        START_SECONDS=$(date -d "${START_TIME}" +%s)
        CURRENT_SECONDS=$(date +%s)
        UPTIME=$((CURRENT_SECONDS - START_SECONDS))

        # Count connected clients using status file
        if [ -f "${LOGS_DIR}/status.log" ]; then
            # Count lines containing "ROUTING TABLE" (indicates connected clients)
            CLIENTS=$(grep -c "ROUTING TABLE" "${LOGS_DIR}/status.log")
        else
            CLIENTS=0
        fi

        echo "status: running"
        echo "uptime: ${UPTIME}"
        echo "clients: ${CLIENTS}"
        echo "Server is running with PID ${PID}"
        exit 0
    else
        # PID exists but process is not running
        echo "status: stopped"
        echo "PID file exists but the process is not running"
        # Clean up obsolete PID file
        rm -f "${OPENVPN_PID_FILE}"
        exit 0
    fi
else
    # PID file does not exist
    # Check if there is still an OpenVPN process running
    if pgrep -f "openvpn --config" > /dev/null; then
        # There is a process but no PID file
        PID=$(pgrep -f "openvpn --config")
        echo "status: running"
        echo "Server is running with PID ${PID} (no PID file)"

        # Create PID file
        echo "${PID}" > "${OPENVPN_PID_FILE}"
        exit 0
    else
        # No process and no PID file
        echo "status: stopped"
        echo "OpenVPN is not running"
        exit 0
    fi
fi
