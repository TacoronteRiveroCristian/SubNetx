#!/bin/bash
# Descripcion: Detiene el servicio de OpenVPN y limpia las reglas de iptables.

# Función para manejar errores
handle_error() {
    echo "❌ Error: $1"
    echo "❌ No se pudo detener OpenVPN correctamente."
    exit 1
}

echo "🛑 Deteniendo OpenVPN..."

# Verificar si el archivo PID existe
if [ -f "${OPENVPN_DIR}/openvpn.pid" ]; then
    # Leer el PID del archivo
    PID=$(cat "${OPENVPN_DIR}/openvpn.pid")

    # Verificar si el proceso existe
    if kill -0 "$PID" 2>/dev/null; then
        echo "📝 Deteniendo proceso OpenVPN (PID: $PID)..."
        if ! kill "$PID"; then
            handle_error "No se pudo detener el proceso con kill normal"
        fi

        # Esperar a que el proceso termine
        for i in {1..10}; do
            if ! kill -0 "$PID" 2>/dev/null; then
                echo "✅ Proceso OpenVPN detenido correctamente."
                break
            fi
            sleep 1
        done

        # Si el proceso sigue activo, usar kill -9
        if kill -0 "$PID" 2>/dev/null; then
            echo "⚠️ Forzando detención del proceso..."
            if ! kill -9 "$PID"; then
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
if pgrep -f "openvpn.*server.conf" > /dev/null; then
    echo "📝 Deteniendo procesos OpenVPN restantes..."
    if ! pkill -f "openvpn.*server.conf"; then
        handle_error "No se pudo detener los procesos OpenVPN restantes"
    fi
    echo "✅ Procesos OpenVPN restantes detenidos."
fi

# Verificar si la interfaz TUN está activa
if ip link show "${TUN_DEVICE}" >/dev/null 2>&1; then
    echo "🔌 Desactivando interfaz ${TUN_DEVICE}..."
    if ! ip link set "${TUN_DEVICE}" down; then
        handle_error "No se pudo desactivar la interfaz ${TUN_DEVICE}"
    fi
    echo "✅ Interfaz ${TUN_DEVICE} desactivada."
fi

# Limpiar reglas de iptables
echo "🧹 Limpiando reglas de iptables..."
if ! iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null; then
    echo "ℹ️ No se encontró regla MASQUERADE para eth0"
fi
if ! iptables -t nat -D POSTROUTING -o lo -j MASQUERADE 2>/dev/null; then
    echo "ℹ️ No se encontró regla MASQUERADE para lo"
fi

# Eliminar archivo PID si existe
if [ -f "${OPENVPN_DIR}/openvpn.pid" ]; then
    if ! rm "${OPENVPN_DIR}/openvpn.pid"; then
        handle_error "No se pudo eliminar el archivo PID"
    fi
    echo "🗑️ Archivo PID eliminado."
fi

echo "✅ OpenVPN detenido correctamente."
