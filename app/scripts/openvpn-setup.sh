#!/bin/bash
# Descripcion: Configura OpenVPN, genera certificados, habilita el reenvio de paquetes y configura NAT.

# ---------------------------
# Recoger los parametros
# ---------------------------
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --network)
            VPN_NETWORK="$2"
            shift 2
            ;;
        --netmask)
            VPN_NETMASK="$2"
            shift 2
            ;;
        --port)
            OPENVPN_PORT="$2"
            shift 2
            ;;
        --proto)
            OPENVPN_PROTO="$2"
            shift 2
            ;;
        --tun)
            TUN_DEVICE="$2"
            shift 2
            ;;
        --ip)
            PUBLIC_IP="$2"
            shift 2
            ;;
        *)
            echo "❌ Opción desconocida: $1"
            /app/scripts/openvpn-help.sh
            exit 1
            ;;
    esac
done

# Mostrar los parametros recibidos
echo "Parametros recibidos:"
echo "VPN_NETWORK: $VPN_NETWORK"
echo "VPN_NETMASK: $VPN_NETMASK"
echo "OPENVPN_PORT: $OPENVPN_PORT"
echo "OPENVPN_PROTO: $OPENVPN_PROTO"
echo "TUN_DEVICE: $TUN_DEVICE"
echo "PUBLIC_IP: $PUBLIC_IP"

# ---------------------------
# Sustituir los marcadores en la plantilla
# ---------------------------
TEMPLATE="/app/config/openvpn/config.sh.template"
CONFIG="/app/config/openvpn/config.sh"

if [ ! -f "$TEMPLATE" ]; then
    echo "❌ No se encontro el archivo de plantilla: $TEMPLATE"
    exit 1
fi

# Utilizamos sed para reemplazar los marcadores con los valores recogidos
sed -e "s/{{NETWORK}}/${VPN_NETWORK}/g" \
    -e "s/{{NETMASK}}/${VPN_NETMASK}/g" \
    -e "s/{{PUBLIC_IP}}/${PUBLIC_IP}/g" \
    -e "s/{{PORT}}/${OPENVPN_PORT}/g" \
    -e "s/{{PROTO}}/${OPENVPN_PROTO}/g" \
    -e "s/{{TUN}}/${TUN_DEVICE}/g" \
    "$TEMPLATE" > "$CONFIG"

echo "✔ Archivo de configuracion generado en $CONFIG"

# Definir rutas del template y del archivo final de server.conf
SERVER_TEMPLATE="/app/config/openvpn/server.conf.template"
SERVER_CONF="/etc/openvpn/server/server.conf"

# Verificar que el template existe
if [ ! -f "$SERVER_TEMPLATE" ]; then
    echo "❌ No se encontró el template de server.conf: $SERVER_TEMPLATE"
    exit 1
fi

# Utilizar sed para reemplazar los placeholders con los parámetros recogidos
sed -e "s/{{PORT}}/${OPENVPN_PORT}/g" \
    -e "s/{{PROTO}}/${OPENVPN_PROTO}/g" \
    -e "s/{{TUN}}/${TUN_DEVICE}/g" \
    -e "s/{{NETWORK}}/${VPN_NETWORK}/g" \
    -e "s/{{NETMASK}}/${VPN_NETMASK}/g" \
    "$SERVER_TEMPLATE" > "$SERVER_CONF"

echo "✔ Archivo server.conf generado en $SERVER_CONF"

source "$CONFIG"

# ---------------------------
# Continuar con el resto de la configuracion
# ---------------------------
echo "🛠️ Configurando OpenVPN..."

# Crear directorio de clientes si no existe
if [ ! -d "$OPENVPN_DIR/ccd" ]; then
    echo "📂 Creando directorio de clientes..."
    mkdir -p "$OPENVPN_DIR/ccd"
else
    echo "✅ Directorio de clientes ya existe."
fi

# Crear directorio de Easy-RSA si no existe
if [ ! -d "$EASYRSA_DIR" ]; then
    echo "📂 Creando directorio Easy-RSA..."
    make-cadir "$EASYRSA_DIR"
    chmod -R 755 "$EASYRSA_DIR"
else
    echo "✅ Directorio Easy-RSA ya existe."
fi

# Moverse al directorio Easy-RSA
cd "$EASYRSA_DIR" || { echo "❌ Error: No se pudo acceder a $EASYRSA_DIR"; exit 1; }

# Inicializar la PKI si no existe
if [ ! -d "$EASYRSA_DIR/pki" ]; then
    echo "🔑 Inicializando PKI..."
    ./easyrsa --batch init-pki
fi

# Crear la CA si no existe
if [ ! -f "$OPENVPN_DIR/ca.crt" ]; then
    echo "🔏 Generando Autoridad de Certificación (CA)..."
    ./easyrsa --batch build-ca nopass
    cp pki/ca.crt "$OPENVPN_DIR/"
fi

# Crear clave y certificado del servidor si no existen
if [ ! -f "$OPENVPN_DIR/server.crt" ]; then
    echo "🔐 Generando clave y certificado del servidor..."
    ./easyrsa --batch gen-req server nopass
    echo "yes" | ./easyrsa --batch sign-req server server
    cp pki/private/server.key "$OPENVPN_DIR/"
    cp pki/issued/server.crt "$OPENVPN_DIR/"
fi

# Generar Diffie-Hellman si no existe
if [ ! -f "$OPENVPN_DIR/dh.pem" ]; then
    echo "🔀 Generando Diffie-Hellman..."
    ./easyrsa gen-dh
    cp pki/dh.pem "$OPENVPN_DIR/"
fi

# Generar clave TLS si no existe
if [ ! -f "$OPENVPN_DIR/ta.key" ]; then
    echo "🔑 Generando clave TLS..."
    openvpn --genkey secret "$OPENVPN_DIR/ta.key"
fi

# Aplicar los cambios en sysctl sin necesidad de reiniciar
sysctl -p

echo "📡 Configurando iptables para enrutar tráfico de la VPN..."
# Modificar tablas de enrutamiento
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -t nat -A POSTROUTING -o lo -j MASQUERADE

# Verificar reglas de iptables
echo "📜 Reglas de iptables aplicadas:"
iptables -t nat -L -n -v

echo "✅ Configuración de OpenVPN completada correctamente."
