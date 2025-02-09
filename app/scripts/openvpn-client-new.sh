#!/bin/bash
# Descripción: Genera un certificado y configuración para un nuevo cliente OpenVPN con IP fija.

CLIENT_NAME=""
CLIENT_IP=""

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 --name <CLIENT_NAME> --ip <CLIENT_IP>"
    echo "Ejemplo: $0 --name myclient1 --ip 10.8.0.10"
    exit 1
}

# Parsear argumentos
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --name) CLIENT_NAME="$2"; shift 2 ;;
        --ip) CLIENT_IP="$2"; shift 2 ;;
        *) echo "❌ Error: Opción desconocida $1"; show_help ;;
    esac
done

# Validar parámetros
if [[ -z "$CLIENT_NAME" || -z "$CLIENT_IP" ]]; then
    echo "❌ Error: Debes especificar un nombre y una IP para el cliente."
    show_help
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

# Crear el archivo de configuración del cliente en el servidor (CCD)
CCD_FILE="/etc/openvpn/ccd/$CLIENT_NAME"
echo "📄 Asignando IP fija al cliente en: $CCD_FILE"

mkdir -p /etc/openvpn/ccd
echo "ifconfig-push $CLIENT_IP 255.255.255.0" | tee "$CCD_FILE" > /dev/null

# Crear el perfil de configuración del cliente (.ovpn con todo embebido)
CLIENT_CONFIG="$OPENVPN_DIR/client/$CLIENT_NAME.ovpn"

echo "📄 Creando archivo de configuración del cliente: $CLIENT_CONFIG"

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

# Cambiar permisos para que el usuario pueda acceder a los archivos
chown -R subnetx:subnetx "$CLIENT_CONFIG"

echo "✅ Cliente creado correctamente con IP fija: $CLIENT_IP"
echo "📄 Archivo .ovpn (todo embebido): $CLIENT_CONFIG"
