#!/bin/bash
# Descripcion: Genera un certificado y configuración para un nuevo cliente OpenVPN.

source "/app/config/openvpn/config.sh"

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

# Crear el perfil de configuración del cliente (.ovpn con todo embebido)
CLIENT_CONFIG="/etc/openvpn/client/$CLIENT_NAME.ovpn"

echo "📄 Creando archivo de configuración del cliente: $CLIENT_CONFIG"

cat > "$CLIENT_CONFIG" <<EOF
client
dev tun
proto $OPENVPN_PROTO
remote labcrist.duckdns.org $OPENVPN_PORT
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
    sudo cat "$EASYRSA_DIR/pki/ca.crt"
    echo "</ca>"

    echo "<cert>"
    sudo cat "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt"
    echo "</cert>"

    echo "<key>"
    sudo cat "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key"
    echo "</key>"

    echo "<tls-auth>"
    sudo cat "/etc/openvpn/ta.key"
    echo "</tls-auth>"
} >> "$CLIENT_CONFIG"

# Cambiar permisos para que el usuario pueda acceder a los archivos
sudo chown -R subnetx:subnetx "$CLIENT_CONFIG_DIR"

echo "✅ Cliente creado correctamente."
echo "📄 Archivo .ovpn (todo embebido): $CLIENT_CONFIG"
