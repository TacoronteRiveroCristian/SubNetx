#!/bin/bash
# Descripcion: Genera un certificado y configuración para un nuevo cliente OpenVPN.

source "$BASE_DIR/app/config/openvpn/config.sh"

CLIENT_NAME="$1"

if [ -z "$CLIENT_NAME" ]; then
    echo "❌ Error: Debes especificar un nombre para el cliente."
    exit 1
fi

echo "🔑 Creando certificado y clave para el cliente: $CLIENT_NAME"

# Moverse al directorio de Easy-RSA
cd "$EASYRSA_DIR" || { echo "❌ Error: No se pudo acceder a $EASYRSA_DIR"; exit 1; }

# Construir el certificado del cliente
sudo ./easyrsa --batch build-client-full "$CLIENT_NAME" nopass

# Verificar si los archivos se crearon correctamente
if [ ! -f "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" ] || [ ! -f "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key" ]; then
    echo "❌ Error: No se generaron correctamente los archivos del cliente."
    exit 1
fi

echo "✅ Certificado y clave generados para $CLIENT_NAME."

# Crear el directorio de configuraciones de cliente si no existe
CLIENT_CONFIG_DIR="$BASE_DIR/app/config/openvpn/client-configs"
mkdir -p "$CLIENT_CONFIG_DIR"

# Crear el perfil de configuración del cliente
CLIENT_CONFIG="$CLIENT_CONFIG_DIR/$CLIENT_NAME.ovpn"

echo "📄 Creando archivo de configuración del cliente: $CLIENT_CONFIG"

cat > "$CLIENT_CONFIG" <<EOF
client
dev tun
proto $OPENVPN_PROTO
remote $(hostname -I | awk '{print $1}') $OPENVPN_PORT
resolv-retry infinite
nobind
persist-key
persist-tun
ca [inline]
cert [inline]
key [inline]
tls-auth [inline] 1
cipher AES-256-CBC
auth SHA256
comp-lzo
verb 3
EOF

# Incluir certificados en el archivo .ovpn
echo "<ca>" >> "$CLIENT_CONFIG"
sudo cat "$EASYRSA_DIR/pki/ca.crt" >> "$CLIENT_CONFIG"
echo "</ca>" >> "$CLIENT_CONFIG"

echo "<cert>" >> "$CLIENT_CONFIG"
sudo cat "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" >> "$CLIENT_CONFIG"
echo "</cert>" >> "$CLIENT_CONFIG"

echo "<key>" >> "$CLIENT_CONFIG"
sudo cat "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key" >> "$CLIENT_CONFIG"
echo "</key>" >> "$CLIENT_CONFIG"

echo "<tls-auth>" >> "$CLIENT_CONFIG"
sudo cat "$SERVER_DIR/ta.key" >> "$CLIENT_CONFIG"
echo "</tls-auth>" >> "$CLIENT_CONFIG"

# Cambiar permisos para que el usuario pueda descargarlo
sudo chown subnetx:subnetx "$CLIENT_CONFIG"

echo "✅ Cliente creado correctamente. Configuración guardada en: $CLIENT_CONFIG"
