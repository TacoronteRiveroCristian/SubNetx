#!/bin/bash
# Descripcion: Genera un certificado y configuracion para un nuevo cliente OpenVPN con IP fija.
# Usa las variables de entorno definidas en el Dockerfile para mantener coherencia.

# Verificar si existe el archivo de configuración
if [ ! -f "$OPENVPN_DIR/vpn_config.json" ]; then
    echo "❌ Error: No se encontró el archivo de configuración en $OPENVPN_DIR/vpn_config.json"
    echo "Ejecute primero openvpn-setup.sh para generar la configuración."
    exit 1
fi

# Cargar configuración desde el archivo JSON
echo "📄 Cargando configuración desde $OPENVPN_DIR/vpn_config.json"
VPN_NETWORK=$(jq -r '.vpn_network' "$OPENVPN_DIR/vpn_config.json")
VPN_NETMASK=$(jq -r '.vpn_netmask' "$OPENVPN_DIR/vpn_config.json")
OPENVPN_PORT=$(jq -r '.openvpn_port' "$OPENVPN_DIR/vpn_config.json")
OPENVPN_PROTO=$(jq -r '.openvpn_proto' "$OPENVPN_DIR/vpn_config.json")
TUN_DEVICE=$(jq -r '.tun_device' "$OPENVPN_DIR/vpn_config.json")
PUBLIC_IP=$(jq -r '.public_ip' "$OPENVPN_DIR/vpn_config.json")

# Verificar que se cargaron todas las variables necesarias
if [ -z "$VPN_NETWORK" ] || [ -z "$VPN_NETMASK" ] || [ -z "$OPENVPN_PORT" ] || \
   [ -z "$OPENVPN_PROTO" ] || [ -z "$TUN_DEVICE" ] || [ -z "$PUBLIC_IP" ]; then
    echo "❌ Error: El archivo de configuración no contiene todas las variables necesarias"
    exit 1
fi

CLIENT_NAME="" # Nombre del cliente
CLIENT_IP="" # IP fija asignada al cliente

# Parsear argumentos
while [[ "$#" -gt 0 ]]; do # Para cada argumento en la linea de comandos
    case "$1" in
        --name) # Si el argumento es --name
            CLIENT_NAME="$2" # Asigna el siguiente argumento como nombre del cliente
            shift 2 # Avanza dos posiciones
            ;;
        --ip) # Si el argumento es --ip
            CLIENT_IP="$2" # Asigna el siguiente argumento como IP del cliente
            shift 2 # Avanza dos posiciones
            ;;
        *) # Si es cualquier otro argumento
            echo "❌ Error: Opcion desconocida $1" # Muestra error
            /app/scripts/utils/openvpn-help.sh # Muestra ayuda
            exit 1 # Termina con error
            ;;
    esac
done

# Validar parametros
if [[ -z "$CLIENT_NAME" || -z "$CLIENT_IP" ]]; then # Si falta nombre o IP
    echo "❌ Error: Debes especificar un nombre y una IP para el cliente."
    /app/scripts/utils/openvpn-help.sh # Muestra ayuda
    exit 1 # Termina con error
fi

echo "🔑 Creando certificado y clave para el cliente: $CLIENT_NAME"

# Verificar si existen los certificados necesarios del servidor
if [ ! -f "$CERTS_DIR/ca.crt" ] || [ ! -f "$CERTS_DIR/ta.key" ]; then # Si faltan certificados del servidor
    echo "❌ Error: No se encontraron los certificados necesarios del servidor."
    echo "Ejecute primero openvpn-setup.sh para generar los certificados del servidor."
    exit 1 # Termina con error
fi

# Moverse al directorio Easy-RSA
cd "$EASYRSA_DIR" || { echo "❌ Error: No se pudo acceder a $EASYRSA_DIR"; exit 1; }

# Construir el certificado del cliente
./easyrsa --batch build-client-full "$CLIENT_NAME" nopass # Genera certificado sin contrasena

# Verificar si los archivos se crearon correctamente
if [ ! -f "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" ] || [ ! -f "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key" ]; then # Si no existen los archivos
    echo "❌ Error: No se generaron correctamente los archivos del cliente."
    exit 1 # Termina con error
fi

# Copiar certificados del cliente al directorio centralizado
echo "📂 Copiando certificados del cliente a la ubicacion centralizada..."
mkdir -p "$CERTS_DIR/clients/$CLIENT_NAME" # Crea directorio especifico para el cliente
cp "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" "$CERTS_DIR/clients/$CLIENT_NAME/" # Copia certificado
cp "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key" "$CERTS_DIR/clients/$CLIENT_NAME/" # Copia clave privada

echo "✅ Certificado y clave generados para $CLIENT_NAME."

# Crear el archivo de configuracion del cliente en el servidor (CCD)
CCD_FILE="$CCD_DIR/$CLIENT_NAME" # Ruta al archivo de configuracion del cliente
echo "📄 Asignando IP fija al cliente en: $CCD_FILE"

mkdir -p "$CCD_DIR" # Asegura que existe el directorio
echo "ifconfig-push $CLIENT_IP $VPN_NETMASK" | tee "$CCD_FILE" > /dev/null # Crea el archivo CCD con la IP fija

# Asegurar que existe el directorio de clientes
mkdir -p "$CLIENTS_DIR" # Crea directorio para archivos de configuracion de clientes

# Crear el perfil de configuracion del cliente (.ovpn con todo embebido)
CLIENT_CONFIG="$CLIENTS_DIR/$CLIENT_NAME.ovpn" # Ruta al archivo de configuracion
CLIENT_CONFIG_COPY="$CERTS_DIR/clients/$CLIENT_NAME/$CLIENT_NAME.ovpn" # Copia en el directorio centralizado

echo "📄 Creando archivo de configuracion del cliente: $CLIENT_CONFIG"

cat > "$CLIENT_CONFIG" <<EOF
client
dev $TUN_DEVICE
proto $OPENVPN_PROTO
remote $PUBLIC_IP $OPENVPN_PORT
resolv-retry infinite
nobind
user nobody
group nogroup
persist-key
persist-tun
remote-cert-tls server
data-ciphers AES-256-GCM:AES-128-GCM:AES-256-CBC
auth SHA256
verb 3
key-direction 1
EOF

# Incluir certificados en el archivo .ovpn embebido
{
    echo "<ca>"
    cat "$CERTS_DIR/ca.crt" # Usa el certificado CA del directorio centralizado
    echo "</ca>"

    echo "<cert>"
    cat "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt"
    echo "</cert>"

    echo "<key>"
    cat "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key"
    echo "</key>"

    echo "<tls-auth>"
    cat "$CERTS_DIR/ta.key" # Usa la clave TLS del directorio centralizado
    echo "</tls-auth>"
} >> "$CLIENT_CONFIG"

# Crear una copia del archivo de configuracion en el directorio centralizado
cp "$CLIENT_CONFIG" "$CLIENT_CONFIG_COPY" # Copia el archivo de configuracion

# Establecer permisos correctos
chmod 600 "$CERTS_DIR/clients/$CLIENT_NAME/$CLIENT_NAME.key" "$CERTS_DIR/ta.key"
chmod 644 "$CERTS_DIR/clients/$CLIENT_NAME/$CLIENT_NAME.crt" "$CERTS_DIR/ca.crt" "$CLIENT_CONFIG" "$CLIENT_CONFIG_COPY"

echo "✅ Cliente creado correctamente con IP fija: $CLIENT_IP"
echo "📄 Archivo .ovpn (todo embebido): $CLIENT_CONFIG"
echo "📄 Copia de seguridad en: $CLIENT_CONFIG_COPY"
echo "🔐 Todos los certificados y archivos del cliente se han guardado en: $CERTS_DIR/clients/$CLIENT_NAME"
