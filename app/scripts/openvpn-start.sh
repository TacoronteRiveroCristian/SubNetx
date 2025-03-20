#!/bin/bash
# Descripcion: Inicia OpenVPN en segundo plano, guarda su PID y verifica la conexion.
# Usa las variables de entorno definidas en el Dockerfile para mantener coherencia.

echo "🛠️ Iniciando OpenVPN en segundo plano..."

# Asegurar que el directorio de logs existe y tiene los permisos correctos
echo "📁 Verificando directorio de logs..."
mkdir -p "$LOGS_DIR" # Crea directorio de logs si no existe
touch "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Crea archivos de log si no existen
chmod 644 "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Establece permisos de lectura para todos
chown root:root "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Establece propietario root

# Verificar que los certificados existen en el directorio correcto
for cert in ca.crt server.crt server.key dh.pem ta.key; do # Itera por cada certificado necesario
    if [ ! -f "$CERTS_DIR/$cert" ]; then # Si no existe el certificado
        echo "❌ Error: No se encontro el archivo $cert en $CERTS_DIR"
        echo "Por favor, ejecute primero el script de configuracion: openvpn-setup.sh"
        exit 1 # Termina con error
    fi
done

# Verificar si server.conf existe
if [ ! -f "${SERVER_CONF_DIR}/server.conf" ]; then # Si no existe el archivo de configuracion
    echo "❌ Error: No se encontro el archivo de configuracion del servidor"
    echo "Por favor, ejecute primero el script de configuracion: openvpn-setup.sh"
    exit 1 # Termina con error
fi

# Iniciar OpenVPN en segundo plano con `--daemon`
openvpn --config "${SERVER_CONF_DIR}/server.conf" --daemon # Inicia OpenVPN en segundo plano

# Esperar 2 segundos para que OpenVPN cree el proceso
sleep 2 # Pausa para dar tiempo a que OpenVPN inicie

# Obtener el PID del proceso OpenVPN
PID=$(pgrep -f "openvpn --config ${SERVER_CONF_DIR}/server.conf") # Obtiene el ID del proceso

if [ -z "$PID" ]; then # Si no se encontro el PID
    echo "❌ Error: OpenVPN no se esta ejecutando."
    echo "Revise los logs en ${LOGS_DIR}/openvpn.log para mas informacion."
    exit 1 # Termina con error
fi

# Guardar el PID
echo "$PID" > "${OPENVPN_PID_FILE}" # Guarda el PID en un archivo

echo "✅ OpenVPN iniciado correctamente en segundo plano (PID: $PID)."

# Esperar unos segundos para asegurar que OpenVPN establezca la red
sleep 3 # Pausa para dar tiempo a que se establezca la interfaz de red

# Verificar si la interfaz TUN esta activa
if ip a show "${TUN_DEVICE}" > /dev/null 2>&1; then # Si existe la interfaz TUN
    echo "🔍 Estado de la interfaz TUN:"
    ip a show "${TUN_DEVICE}" # Muestra informacion de la interfaz

    # Extraer los primeros tres octetos y agregar ".1"
    VPN_GATEWAY="${VPN_NETWORK%.*}.1" # Calcula la direccion IP de la puerta de enlace

    # Ejecutar un ping a la IP de la VPN para verificar conectividad
    echo "📡 Probando conexion con la VPN en ${VPN_GATEWAY}..."
    if ping -c 1 "${VPN_GATEWAY}" > /dev/null 2>&1; then # Envia un ping a la puerta de enlace
        echo "🚀 OpenVPN esta activo y funcionando correctamente."
    else
        echo "⚠️ OpenVPN esta corriendo, pero la conexion a ${VPN_GATEWAY} fallo."
    fi

else
    echo "❌ Error: La interfaz ${TUN_DEVICE} no se creo."
    echo "Revise los logs en ${LOGS_DIR}/openvpn.log para mas informacion."
    exit 1 # Termina con error
fi

# Corregir permisos de logs despues de iniciar el servicio
echo "🔒 Ajustando permisos de archivos de log..."
sleep 2 # Espera para asegurar que OpenVPN haya creado/actualizado los logs
chmod 644 "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Establece permisos de lectura para todos
