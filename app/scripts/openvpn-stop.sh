#!/bin/bash
# Descripcion: Detiene el servicio de OpenVPN y limpia las reglas de iptables.
# Usa las variables de entorno definidas en el Dockerfile para mantener coherencia.

# Función para manejar errores
handle_error() {
    echo "❌ Error: $1" # Muestra mensaje de error
    echo "❌ No se pudo detener OpenVPN correctamente." # Indica fallo en la detención
    exit 1 # Termina con código de error
}

echo "🛑 Deteniendo OpenVPN..."

# Antes de detener el servicio, guardar una copia de los logs con timestamp
# para mantener un historial de sesiones anteriores
if [ -f "${LOGS_DIR}/openvpn.log" ]; then # Si existe el archivo de log
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S") # Genera timestamp
    echo "📄 Guardando copia de logs con timestamp: $TIMESTAMP"
    cp "${LOGS_DIR}/openvpn.log" "${LOGS_DIR}/openvpn_${TIMESTAMP}.log" # Copia con timestamp
    cp "${LOGS_DIR}/status.log" "${LOGS_DIR}/status_${TIMESTAMP}.log" 2>/dev/null # Copia con timestamp
    # Ajustar permisos de las copias
    chmod 644 "${LOGS_DIR}/openvpn_${TIMESTAMP}.log" "${LOGS_DIR}/status_${TIMESTAMP}.log" 2>/dev/null
fi

# Verificar si el archivo PID existe
if [ -f "${OPENVPN_PID_FILE}" ]; then # Usa la variable de entorno definida en el Dockerfile
    # Leer el PID del archivo
    PID=$(cat "${OPENVPN_PID_FILE}") # Obtiene el PID del archivo

    # Verificar si el proceso existe
    if kill -0 "$PID" 2>/dev/null; then # Comprueba si el proceso está en ejecución
        echo "📝 Deteniendo proceso OpenVPN (PID: $PID)..."
        if ! kill "$PID"; then # Intenta detener el proceso
            handle_error "No se pudo detener el proceso con kill normal"
        fi

        # Esperar a que el proceso termine
        for i in {1..10}; do # Espera hasta 10 segundos
            if ! kill -0 "$PID" 2>/dev/null; then # Verifica si el proceso ya terminó
                echo "✅ Proceso OpenVPN detenido correctamente."
                break # Sale del bucle si el proceso terminó
            fi
            sleep 1 # Espera 1 segundo antes de verificar de nuevo
        done

        # Si el proceso sigue activo, usar kill -9
        if kill -0 "$PID" 2>/dev/null; then # Si el proceso aún sigue en ejecución
            echo "⚠️ Forzando detención del proceso..."
            if ! kill -9 "$PID"; then # Fuerza la terminación del proceso
                handle_error "No se pudo detener el proceso con kill -9"
            fi
            echo "✅ Proceso OpenVPN forzado a detenerse."
        fi
    else
        echo "⚠️ El proceso OpenVPN ya no está en ejecución."
    fi
else
    echo "⚠️ No se encontró el archivo PID de OpenVPN."
fi

# Detener cualquier proceso OpenVPN que pueda estar corriendo
echo "🔍 Verificando procesos OpenVPN restantes..."
if pgrep -f "openvpn.*server.conf" > /dev/null; then # Busca procesos OpenVPN en ejecución
    echo "📝 Deteniendo procesos OpenVPN restantes..."
    if ! pkill -f "openvpn.*server.conf"; then # Termina todos los procesos OpenVPN
        handle_error "No se pudo detener los procesos OpenVPN restantes"
    fi
    echo "✅ Procesos OpenVPN restantes detenidos."
fi

# Verificar si la interfaz TUN está activa
if ip link show "${TUN_DEVICE}" >/dev/null 2>&1; then # Verifica si la interfaz TUN existe
    echo "🔌 Desactivando interfaz ${TUN_DEVICE}..."
    if ! ip link set "${TUN_DEVICE}" down; then # Desactiva la interfaz TUN
        handle_error "No se pudo desactivar la interfaz ${TUN_DEVICE}"
    fi
    echo "✅ Interfaz ${TUN_DEVICE} desactivada."
fi

# Limpiar reglas de iptables
echo "🧹 Limpiando reglas de iptables..."
if ! iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null; then # Elimina regla NAT para eth0
    echo "ℹ️ No se encontró regla MASQUERADE para eth0"
fi
if ! iptables -t nat -D POSTROUTING -o lo -j MASQUERADE 2>/dev/null; then # Elimina regla NAT para loopback
    echo "ℹ️ No se encontró regla MASQUERADE para lo"
fi

# Eliminar archivo PID si existe
if [ -f "${OPENVPN_PID_FILE}" ]; then # Usa la variable de entorno definida en el Dockerfile
    if ! rm "${OPENVPN_PID_FILE}"; then # Elimina el archivo PID
        handle_error "No se pudo eliminar el archivo PID"
    fi
    echo "🗑️ Archivo PID eliminado."
fi

echo "✅ OpenVPN detenido correctamente."
echo "📝 Los logs de esta sesión se han guardado con timestamp para referencia futura."
