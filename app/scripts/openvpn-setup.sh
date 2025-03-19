#!/bin/bash
# Descripcion: Configura OpenVPN, genera certificados, habilita el reenvio de paquetes y configura NAT.

# Función para manejar errores
handle_error() {
    echo "❌ Error: $1"
    echo "❌ La configuración no se completó correctamente."
    exit 1
}

# ---------------------------
# Validar variables de entorno requeridas
# ---------------------------
required_vars=(
    "VPN_NETWORK"
    "VPN_NETMASK"
    "OPENVPN_PORT"
    "OPENVPN_PROTO"
    "TUN_DEVICE"
    "PUBLIC_IP"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Faltan las siguientes variables de entorno:"
    printf '%s\n' "${missing_vars[@]}"
    echo "Por favor, consulte la ayuda con --help para más información."
    /app/scripts/openvpn-help.sh
    exit 1
fi

# ---------------------------
# Crear archivo de configuración
# ---------------------------
CONFIG="/app/config/openvpn/config.sh"

# Crear el archivo de configuración con las variables de entorno
cat > "$CONFIG" << EOF
#!/bin/bash

# Directorio raiz
OPENVPN_DIR="/etc/openvpn"

# Certificados Easy-RSA
EASYRSA_DIR="\${OPENVPN_DIR}/easy-rsa"
EASYRSA_VAR="\${EASYRSA_DIR}/vars"
_EASYRSA_VAR="/app/config/openvpn/vars"

# Parametros de la red VPN
VPN_NETWORK="${VPN_NETWORK}"
VPN_NETMASK="${VPN_NETMASK}"

# Otros parametros de configuracion
OPENVPN_PID_FILE="\${OPENVPN_DIR}/openvpn.pid"
PUBLIC_IP="${PUBLIC_IP}"
OPENVPN_PORT="${OPENVPN_PORT}"
OPENVPN_PROTO="${OPENVPN_PROTO}"
TUN_DEVICE="${TUN_DEVICE}"
EOF

if [ ! -f "$CONFIG" ]; then
    handle_error "Error al generar el archivo de configuración"
fi

echo "✔ Archivo de configuracion generado en $CONFIG"

# ---------------------------
# Generar server.conf
# ---------------------------
SERVER_TEMPLATE="/app/config/openvpn/server.conf.template"
SERVER_CONF="/etc/openvpn/server/server.conf"

# Verificar que el template existe
if [ ! -f "$SERVER_TEMPLATE" ]; then
    handle_error "No se encontró el template de server.conf: $SERVER_TEMPLATE"
fi

# Utilizar sed para reemplazar los placeholders con las variables de entorno
if ! sed -e "s/{{PORT}}/${OPENVPN_PORT}/g" \
    -e "s/{{PROTO}}/${OPENVPN_PROTO}/g" \
    -e "s/{{TUN}}/${TUN_DEVICE}/g" \
    -e "s/{{NETWORK}}/${VPN_NETWORK}/g" \
    -e "s/{{NETMASK}}/${VPN_NETMASK}/g" \
    "$SERVER_TEMPLATE" > "$SERVER_CONF"; then
    handle_error "Error al generar el archivo server.conf"
fi

echo "✔ Archivo server.conf generado en $SERVER_CONF"

# ---------------------------
# Continuar con el resto de la configuracion
# ---------------------------
echo "🛠️ Configurando OpenVPN..."

# Crear directorio de clientes si no existe
if [ ! -d "$OPENVPN_DIR/ccd" ]; then
    echo "📂 Creando directorio de clientes..."
    if ! mkdir -p "$OPENVPN_DIR/ccd"; then
        handle_error "No se pudo crear el directorio de clientes"
    fi
else
    echo "✅ Directorio de clientes ya existe."
fi

# Crear directorio de Easy-RSA si no existe
if [ ! -d "$EASYRSA_DIR" ]; then
    echo "📂 Creando directorio Easy-RSA..."
    if ! make-cadir "$EASYRSA_DIR"; then
        handle_error "No se pudo inicializar Easy-RSA"
    fi
    if ! chmod -R 755 "$EASYRSA_DIR"; then
        handle_error "No se pudieron establecer los permisos en el directorio Easy-RSA"
    fi
else
    echo "✅ Directorio Easy-RSA ya existe."
fi

# Moverse al directorio Easy-RSA
if ! cd "$EASYRSA_DIR"; then
    handle_error "No se pudo acceder al directorio Easy-RSA: $EASYRSA_DIR"
fi

# Inicializar la PKI si no existe
if [ ! -d "$EASYRSA_DIR/pki" ]; then
    echo "🔑 Inicializando PKI..."
    if ! ./easyrsa --batch init-pki; then
        handle_error "Error al inicializar PKI"
    fi
fi

# Crear la CA si no existe
if [ ! -f "$OPENVPN_DIR/ca.crt" ]; then
    echo "🔏 Generando Autoridad de Certificación (CA)..."
    if ! ./easyrsa --batch build-ca nopass; then
        handle_error "Error al generar la CA"
    fi
    if ! cp pki/ca.crt "$OPENVPN_DIR/"; then
        handle_error "Error al copiar el certificado CA"
    fi
fi

# Crear clave y certificado del servidor si no existen
if [ ! -f "$OPENVPN_DIR/server.crt" ]; then
    echo "🔐 Generando clave y certificado del servidor..."
    if ! ./easyrsa --batch gen-req server nopass; then
        handle_error "Error al generar la clave del servidor"
    fi
    if ! echo "yes" | ./easyrsa --batch sign-req server server; then
        handle_error "Error al firmar el certificado del servidor"
    fi
    if ! cp pki/private/server.key "$OPENVPN_DIR/"; then
        handle_error "Error al copiar la clave del servidor"
    fi
    if ! cp pki/issued/server.crt "$OPENVPN_DIR/"; then
        handle_error "Error al copiar el certificado del servidor"
    fi
fi

# Generar Diffie-Hellman si no existe
if [ ! -f "$OPENVPN_DIR/dh.pem" ]; then
    echo "🔀 Generando Diffie-Hellman..."
    if ! ./easyrsa gen-dh; then
        handle_error "Error al generar los parámetros Diffie-Hellman"
    fi
    if ! cp pki/dh.pem "$OPENVPN_DIR/"; then
        handle_error "Error al copiar los parámetros Diffie-Hellman"
    fi
fi

# Generar clave TLS si no existe
if [ ! -f "$OPENVPN_DIR/ta.key" ]; then
    echo "🔑 Generando clave TLS..."
    if ! openvpn --genkey secret "$OPENVPN_DIR/ta.key"; then
        handle_error "Error al generar la clave TLS"
    fi
fi

# Aplicar los cambios en sysctl sin necesidad de reiniciar
if ! sysctl -p; then
    handle_error "Error al aplicar la configuración de sysctl"
fi

echo "📡 Configurando iptables para enrutar tráfico de la VPN..."
# Modificar tablas de enrutamiento
if ! iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE; then
    handle_error "Error al configurar iptables para eth0"
fi
if ! iptables -t nat -A POSTROUTING -o lo -j MASQUERADE; then
    handle_error "Error al configurar iptables para lo"
fi

# Verificar reglas de iptables
echo "📜 Reglas de iptables aplicadas:"
if ! iptables -t nat -L -n -v; then
    handle_error "Error al verificar las reglas de iptables"
fi

echo "✅ Configuración de OpenVPN completada correctamente."
