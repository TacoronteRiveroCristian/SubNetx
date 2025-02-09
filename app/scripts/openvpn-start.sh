#!/bin/bash
# Descripcion: Inicia OpenVPN en segundo plano, guarda su PID y verifica la conexion.

echo "🛠️ Iniciando OpenVPN en segundo plano..."

# Iniciar OpenVPN en segundo plano con `--daemon`
openvpn --config "${OPENVPN_DIR}/server/server.conf" --daemon

# Esperar 2 segundos para que OpenVPN cree el proceso
sleep 2

# Obtener el PID del proceso OpenVPN
PID=$(pgrep -f "openvpn --config ${OPENVPN_DIR}/server/server.conf")

if [ -z "$PID" ]; then
    echo "❌ Error: OpenVPN no se esta ejecutando."
    exit 1
fi

# Guardar el PID
echo "$PID" | tee "${OPENVPN_PID_FILE}" > /dev/null

echo "✅ OpenVPN iniciado correctamente en segundo plano (PID: $PID)."

# Esperar unos segundos para asegurar que OpenVPN establezca la red
sleep 3

# Verificar si la interfaz TUN esta activa
if ip a show "${TUN_DEVICE}" > /dev/null 2>&1; then
    echo "🔍 Estado de la interfaz TUN:"
    ip a show "${TUN_DEVICE}"

    # Extraer los primeros tres octetos y agregar ".1"
    VPN_GATEWAY="${VPN_NETWORK%.*}.1"

    # Ejecutar un ping a la IP de la VPN para verificar conectividad
    echo "📡 Probando conexion con la VPN en ${VPN_GATEWAY}..."
    if ping -c 1 "${VPN_GATEWAY}" > /dev/null 2>&1; then
        echo "🚀 OpenVPN esta activo y funcionando correctamente."
    else
        echo "⚠️ OpenVPN esta corriendo, pero la conexion a ${VPN_GATEWAY} fallo."
    fi

else
    echo "❌ Error: La interfaz ${TUN_DEVICE} no se creo. Verifica los logs en ${OPENVPN_LOG}"
    exit 1
fi
