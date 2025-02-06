#!/bin/bash
# Descripcion: Detiene OpenVPN de forma segura y limpia la red.

echo "🛑 Deteniendo OpenVPN..."

# Verificar si el archivo de PID existe
if [ -f "/var/run/openvpn.pid" ]; then
    PID=$(cat /var/run/openvpn.pid)

    # Intentar matar el proceso con SIGTERM
    sudo kill "$PID"
    sleep 2

    # Verificar si sigue corriendo y forzar la terminación si es necesario
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️ El proceso sigue corriendo, forzando con SIGKILL..."
        sudo kill -9 "$PID"
        sleep 2
    fi

    # Verificar si OpenVPN sigue corriendo (puede haber quedado huérfano)
    if pgrep -f "openvpn --config" > /dev/null 2>&1; then
        echo "⚠️ OpenVPN sigue corriendo como proceso huérfano, intentando detenerlo..."
        sudo pkill -f "openvpn --config"
        sleep 2
    fi

    # Verificar nuevamente si OpenVPN fue detenido
    if pgrep -f "openvpn --config" > /dev/null 2>&1; then
        echo "❌ Error: No se pudo detener OpenVPN."
        exit 1
    fi

    echo "✅ OpenVPN detenido correctamente."
    sudo rm -f /var/run/openvpn.pid
else
    echo "⚠️ No se encontró el PID de OpenVPN. Puede que ya esté detenido."
fi

# Eliminar la interfaz TUN si sigue activa
if ip link show tun0 > /dev/null 2>&1; then
    echo "🧹 Eliminando interfaz tun0..."
    sudo ip link delete tun0
    sleep 2
fi

# Verificar que ya no hay ping a la VPN
echo "📡 Verificando que la conexión VPN ya no responde..."
if ping -c 1 10.8.0.1 > /dev/null 2>&1; then
    echo "❌ La VPN sigue activa. Algo salió mal."
    exit 1
else
    echo "✅ OpenVPN ha sido detenido completamente. No hay conexión VPN activa."
fi

echo "🚀 OpenVPN ha sido apagado correctamente y la red ha sido limpiada."
