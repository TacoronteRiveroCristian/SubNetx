#!/bin/bash
# Descripcion: Detiene OpenVPN de forma segura y limpia la red.

echo "🛑 Deteniendo OpenVPN..."

# Verificar si el archivo de PID existe
if [ -f $OPENVPN_PID_FILE ]; then
    PID=$(cat $OPENVPN_PID_FILE)

    # Intentar matar el proceso con SIGTERM
    sudo kill "$PID"
    sleep 2

    # Verificar si sigue corriendo y forzar la terminacion si es necesario
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "⚠️ El proceso sigue corriendo, forzando con SIGKILL..."
        sudo kill -9 "$PID"
        sleep 2
    fi

    # Verificar si OpenVPN sigue corriendo (puede haber quedado huerfano)
    if pgrep -f "openvpn --config" > /dev/null 2>&1; then
        echo "⚠️ OpenVPN sigue corriendo como proceso huerfano, intentando detenerlo..."
        sudo pkill -f "openvpn --config"
        sleep 2
    fi

    # Verificar nuevamente si OpenVPN fue detenido
    if pgrep -f "openvpn --config" > /dev/null 2>&1; then
        echo "❌ Error: No se pudo detener OpenVPN."
        exit 1
    fi

    echo "✅ OpenVPN detenido correctamente."
    sudo rm -f $OPENVPN_PID_FILE
else
    echo "⚠️ No se encontro el PID de OpenVPN. Puede que ya este detenido."
fi

# Eliminar la interfaz TUN si sigue activa
if ip link show $TUN_DEVICE > /dev/null 2>&1; then
    echo "🧹 Eliminando interfaz $TUN_DEVICE..."
    sudo ip link delete $TUN_DEVICE
    sleep 2
fi

# Verificar que ya no hay ping a la VPN
echo "📡 Verificando que la conexion VPN ya no responde..."
if ping -c 1 $VPN_NETWORK.1 > /dev/null 2>&1; then
    echo "❌ La VPN sigue activa. Algo salio mal."
    exit 1
else
    echo "✅ OpenVPN ha sido detenido completamente. No hay conexion VPN activa."
fi

echo "🚀 OpenVPN ha sido apagado correctamente y la red ha sido limpiada."
