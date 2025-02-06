#!/bin/bash
# Descripcion: Inicia OpenVPN en segundo plano, guarda su PID y verifica la conexión.

source "$BASE_DIR/app/config/openvpn/config.sh"

echo "🛠️ Iniciando OpenVPN en segundo plano..."

# Iniciar OpenVPN en segundo plano con `--daemon`
sudo openvpn --config "$SERVER_CONF" --daemon

# Esperar 2 segundos para que OpenVPN cree el proceso
sleep 2

# Obtener el PID del proceso OpenVPN
PID=$(pgrep -f "openvpn --config $SERVER_CONF")

if [ -z "$PID" ]; then
    echo "❌ Error: OpenVPN no se está ejecutando."
    exit 1
fi

# Guardar el PID
echo "$PID" | sudo tee /var/run/openvpn.pid > /dev/null

echo "✅ OpenVPN iniciado correctamente en segundo plano (PID: $PID)."

# Esperar unos segundos para asegurar que OpenVPN establezca la red
sleep 3

# Verificar si la interfaz TUN está activa
if ip a show tun0 > /dev/null 2>&1; then
    echo "🔍 Estado de la interfaz TUN:"
    ip a show tun0

    # Ejecutar un ping a la IP de la VPN para verificar conectividad
    echo "📡 Probando conexión con la VPN..."
    if ping -c 1 10.8.0.1 > /dev/null 2>&1; then
        echo "🚀 OpenVPN está activo y funcionando correctamente."
    else
        echo "⚠️ OpenVPN está corriendo, pero la conexión a 10.8.0.1 falló."
    fi
else
    echo "❌ Error: La interfaz tun0 no se creó. Verifica los logs en /var/log/openvpn.log"
    exit 1
fi
