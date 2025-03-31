#!/bin/bash
# openvpn-status.sh - Script para verificar el estado del servidor OpenVPN
# Descripción: Verifica si el servidor OpenVPN está en ejecución, su tiempo de actividad
# y cuántos clientes están conectados actualmente.
# Autor: SubNetx Team
# Versión: 1.0.0

# Verificar si existe el archivo PID
if [ -f "${OPENVPN_PID_FILE}" ]; then
    # Leer el PID del archivo
    PID=$(cat "${OPENVPN_PID_FILE}")

    # Verificar si el proceso está en ejecución
    if ps -p "${PID}" > /dev/null; then
        # OpenVPN está en ejecución
        # Obtener tiempo de actividad en segundos
        START_TIME=$(ps -o lstart= -p "${PID}")
        START_SECONDS=$(date -d "${START_TIME}" +%s)
        CURRENT_SECONDS=$(date +%s)
        UPTIME=$((CURRENT_SECONDS - START_SECONDS))

        # Contar clientes conectados usando el archivo de estado
        if [ -f "${LOGS_DIR}/status.log" ]; then
            # Contar líneas que contienen "ROUTING TABLE" (indica clientes conectados)
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
        # El PID existe pero el proceso no está en ejecución
        echo "status: stopped"
        echo "El archivo PID existe pero el proceso no está en ejecución"
        # Limpiar el archivo PID obsoleto
        rm -f "${OPENVPN_PID_FILE}"
        exit 0
    fi
else
    # No existe archivo PID
    # Comprobar si de todos modos hay un proceso OpenVPN en ejecución
    if pgrep -f "openvpn --config" > /dev/null; then
        # Hay un proceso pero sin archivo PID
        PID=$(pgrep -f "openvpn --config")
        echo "status: running"
        echo "Server is running with PID ${PID} (no PID file)"

        # Crear el archivo PID
        echo "${PID}" > "${OPENVPN_PID_FILE}"
        exit 0
    else
        # No hay proceso ni archivo PID
        echo "status: stopped"
        echo "OpenVPN no está en ejecución"
        exit 0
    fi
fi
