#!/bin/bash
# Descripcion: Genera un certificado y configuracion para un nuevo cliente OpenVPN con IP fija.

CLIENT_NAME=""
CLIENT_IP=""

# Parsear argumentos
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --name)
            CLIENT_NAME="$2"
            shift 2
            ;;
        --ip)
            CLIENT_IP="$2"
            shift 2
            ;;
        *)
            echo "❌ Error: Opcion desconocida $1"
            /app/scripts/openvpn-help.sh
            exit 1
            ;;
    esac
done

# Validar parametros
if [[ -z "$CLIENT_NAME" || -z "$CLIENT_IP" ]]; then
    echo "❌ Error: Debes especificar un nombre y una IP para el cliente."
    /app/scripts/openvpn-help.sh
    exit 1
fi

echo "🔑 Creando certificado y clave para el cliente: $CLIENT_NAME"

# Moverse al directorio de Easy-RSA
cd "$EASYRSA_DIR" || { echo "❌ Error: No se pudo acceder a $EASYRSA_DIR"; exit 1; }

# Construir el certificado del cliente
./easyrsa --batch build-client-full "$CLIENT_NAME" nopass

# Verificar si los archivos se crearon correctamente
if [ ! -f "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" ] || [ ! -f "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key" ]; then
    echo "❌ Error: No se generaron correctamente los archivos del cliente."
    exit 1
fi

echo "✅ Certificado y clave generados para $CLIENT_NAME."

# Crear el archivo de configuracion del cliente en el servidor (CCD)
CCD_FILE="/etc/openvpn/ccd/$CLIENT_NAME"
echo "📄 Asignando IP fija al cliente en: $CCD_FILE"

mkdir -p /etc/openvpn/ccd
echo "ifconfig-push $CLIENT_IP $VPN_NETMASK" | tee "$CCD_FILE" > /dev/null

# Crear el perfil de configuracion del cliente (.ovpn con todo embebido)
CLIENT_CONFIG="$OPENVPN_DIR/client/$CLIENT_NAME.ovpn"

echo "📄 Creando archivo de configuracion del cliente: $CLIENT_CONFIG"

cat > "$CLIENT_CONFIG" <<EOF
client
dev tun
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
    cat "$EASYRSA_DIR/pki/ca.crt"
    echo "</ca>"

    echo "<cert>"
    cat "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt"
    echo "</cert>"

    echo "<key>"
    cat "$EASYRSA_DIR/pki/private/$CLIENT_NAME.key"
    echo "</key>"

    echo "<tls-auth>"
    cat "$OPENVPN_DIR/ta.key"
    echo "</tls-auth>"
} >> "$CLIENT_CONFIG"

echo "✅ Cliente creado correctamente con IP fija: $CLIENT_IP"
echo "📄 Archivo .ovpn (todo embebido): $CLIENT_CONFIG"
