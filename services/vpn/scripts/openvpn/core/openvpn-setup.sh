#!/bin/bash
# Descripcion: Configura OpenVPN, genera certificados, habilita el reenvio de paquetes y configura NAT.
# Las rutas estan definidas como variables de entorno en el Dockerfile para mayor coherencia.

# Funcion para manejar errores
handle_error() {
    echo "❌ Error: $1" # Muestra mensaje de error
    echo "❌ La configuracion no se completo correctamente." # Indica fallo en la configuracion
    exit 1 # Termina con codigo de error
}

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [opciones]"
    echo "Opciones:"
    echo "  --red <ip>        Red VPN (ej: 10.10.10.0)"
    echo "  --mask <mask>     Máscara de red (ej: 255.255.255.0)"
    echo "  --port <port>     Puerto OpenVPN (ej: 1194)"
    echo "  --proto <proto>   Protocolo (udp/tcp)"
    echo "  --tun <device>    Dispositivo TUN (ej: tun0)"
    echo "  --ip <ip>         IP pública o dominio"
    echo "  --help           Mostrar esta ayuda"
    exit 0
}

# Parsear argumentos de línea de comandos
while [[ $# -gt 0 ]]; do
    case $1 in
        --red)
            VPN_NETWORK="$2"
            shift 2
            ;;
        --mask)
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
        --help)
            show_help
            ;;
        *)
            echo "❌ Opción desconocida: $1"
            show_help
            ;;
    esac
done

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
    "OPENVPN_DIR"
    "CERTS_DIR"
    "SERVER_CONF_DIR"
    "EASYRSA_DIR"
    "LOGS_DIR"
)

missing_vars=() # Inicializa array para variables faltantes

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then # Verifica si la variable esta vacia
        missing_vars+=("$var") # Anade variable faltante al array
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then # Si hay variables faltantes
    echo "❌ Faltan las siguientes variables de entorno:"
    printf '%s\n' "${missing_vars[@]}" # Imprime cada variable faltante
    echo "Por favor, consulte la ayuda con --help para mas informacion."
    /app/scripts/utils/openvpn-help.sh # Muestra ayuda
    exit 1 # Termina con error
fi

# Crear directorio OpenVPN si no existe
mkdir -p "$OPENVPN_DIR"

# Crear archivo de configuración JSON
echo "📄 Creando archivo de configuración..."
cat > "$OPENVPN_DIR/vpn_config.json" << EOF
{
    "vpn_network": "$VPN_NETWORK",
    "vpn_netmask": "$VPN_NETMASK",
    "openvpn_port": $OPENVPN_PORT,
    "openvpn_proto": "$OPENVPN_PROTO",
    "tun_device": "$TUN_DEVICE",
    "public_ip": "$PUBLIC_IP"
}
EOF

# Verificar que el archivo se creó correctamente
if [ ! -f "$OPENVPN_DIR/vpn_config.json" ]; then
    handle_error "No se pudo crear el archivo de configuración JSON"
fi

# Establecer permisos de lectura para todos
chmod 644 "$OPENVPN_DIR/vpn_config.json"
echo "✅ Archivo de configuración creado en $OPENVPN_DIR/vpn_config.json"

# ---------------------------
# Preparar directorio de logs
# ---------------------------
# Asegurar que el directorio de logs existe y tiene los permisos correctos
echo "📁 Preparando directorio de logs..."
mkdir -p "$LOGS_DIR" # Crea directorio de logs si no existe
touch "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Crea archivos de log si no existen
chmod 644 "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Establece permisos de lectura para todos
chown root:root "$LOGS_DIR/openvpn.log" "$LOGS_DIR/status.log" # Establece propietario root

# ---------------------------
# Generar server.conf
# ---------------------------
SERVER_CONF="${SERVER_CONF_DIR}/server.conf" # Ruta al archivo de configuracion del servidor
SERVER_TEMPLATE="/app/config/openvpn/server.conf.template" # Ruta al template

# Verificar que el template existe
if [ ! -f "$SERVER_TEMPLATE" ]; then # Verifica si existe el archivo template
    handle_error "No se encontro el template de server.conf: $SERVER_TEMPLATE"
fi

# Crear directorio para la configuracion del servidor si no existe
mkdir -p "$SERVER_CONF_DIR" # Crea el directorio para la configuracion

# Utilizar sed para reemplazar los placeholders con las variables de entorno
if ! sed -e "s/{{PORT}}/${OPENVPN_PORT}/g" \
    -e "s/{{PROTO}}/${OPENVPN_PROTO}/g" \
    -e "s/{{TUN}}/${TUN_DEVICE}/g" \
    -e "s/{{NETWORK}}/${VPN_NETWORK}/g" \
    -e "s/{{NETMASK}}/${VPN_NETMASK}/g" \
    -e "s|{{LOGS_DIR}}|${LOGS_DIR}|g" \
    "$SERVER_TEMPLATE" > "$SERVER_CONF"; then # Reemplaza variables en el template
    handle_error "Error al generar el archivo server.conf"
fi

echo "✅ Archivo server.conf generado en $SERVER_CONF"

# ---------------------------
# Inicializar Easy-RSA si es necesario
# ---------------------------
if [ ! -d "$EASYRSA_DIR" ]; then # Verifica si existe el directorio Easy-RSA
    echo "📂 Creando e inicializando directorio Easy-RSA..."
    if ! make-cadir "$EASYRSA_DIR"; then # Inicializa Easy-RSA
        handle_error "No se pudo inicializar Easy-RSA"
    fi
    if ! chmod -R 755 "$EASYRSA_DIR"; then # Establece permisos
        handle_error "No se pudieron establecer los permisos en el directorio Easy-RSA"
    fi
else
    echo "✅ Directorio Easy-RSA ya existe."
fi

# Copiar vars si esta disponible
EASYRSA_VARS_TEMPLATE="/app/config/vars"
if [ -f "$EASYRSA_VARS_TEMPLATE" ]; then # Si existe el archivo vars template
    cp "$EASYRSA_VARS_TEMPLATE" "$EASYRSA_DIR/vars" # Copia el archivo vars
    echo "✅ Archivo vars copiado a $EASYRSA_DIR/vars"
fi

# ---------------------------
# Generar certificados y claves
# ---------------------------
echo "🛠️ Configurando OpenVPN..."

# Moverse al directorio Easy-RSA
cd "$EASYRSA_DIR" || { # Cambia al directorio Easy-RSA
    handle_error "No se pudo acceder al directorio Easy-RSA: $EASYRSA_DIR"
}

# Inicializar la PKI si no existe
if [ ! -d "$EASYRSA_DIR/pki" ]; then # Verifica si existe la PKI
    echo "🔑 Inicializando PKI..."
    if ! ./easyrsa --batch init-pki; then # Inicializa PKI
        handle_error "Error al inicializar PKI"
    fi
fi

# Crear la CA si no existe
if [ ! -f "$CERTS_DIR/ca.crt" ]; then # Verifica si existe el certificado CA
    echo "🔏 Generando Autoridad de Certificacion (CA)..."
    if ! ./easyrsa --batch build-ca nopass; then # Genera CA sin contrasena
        handle_error "Error al generar la CA"
    fi
    if ! cp pki/ca.crt "$CERTS_DIR/"; then # Copia el certificado CA al directorio de certificados
        handle_error "Error al copiar el certificado CA"
    fi
fi

# Crear clave y certificado del servidor si no existen
if [ ! -f "$CERTS_DIR/server.crt" ]; then # Verifica si existe el certificado del servidor
    echo "🔐 Generando clave y certificado del servidor..."
    if ! ./easyrsa --batch gen-req server nopass; then # Genera solicitud de certificado sin contrasena
        handle_error "Error al generar la clave del servidor"
    fi
    if ! echo "yes" | ./easyrsa --batch sign-req server server; then # Firma la solicitud de certificado
        handle_error "Error al firmar el certificado del servidor"
    fi
    if ! cp pki/private/server.key "$CERTS_DIR/"; then # Copia la clave privada al directorio de certificados
        handle_error "Error al copiar la clave del servidor"
    fi
    if ! cp pki/issued/server.crt "$CERTS_DIR/"; then # Copia el certificado al directorio de certificados
        handle_error "Error al copiar el certificado del servidor"
    fi
fi

# Generar Diffie-Hellman si no existe
if [ ! -f "$CERTS_DIR/dh.pem" ]; then # Verifica si existen los parametros Diffie-Hellman
    echo "🔀 Generando Diffie-Hellman..."
    if ! ./easyrsa gen-dh; then # Genera parametros Diffie-Hellman
        handle_error "Error al generar los parametros Diffie-Hellman"
    fi
    if ! cp pki/dh.pem "$CERTS_DIR/"; then # Copia los parametros al directorio de certificados
        handle_error "Error al copiar los parametros Diffie-Hellman"
    fi
fi

# Generar clave TLS si no existe
if [ ! -f "$CERTS_DIR/ta.key" ]; then # Verifica si existe la clave TLS
    echo "🔑 Generando clave TLS..."
    if ! openvpn --genkey secret "$CERTS_DIR/ta.key"; then # Genera clave TLS
        handle_error "Error al generar la clave TLS"
    fi
fi

# Establecer permisos correctos para los certificados
chmod 600 "$CERTS_DIR/server.key" # Establece permiso restrictivo para la clave del servidor
chmod 644 "$CERTS_DIR/ca.crt" "$CERTS_DIR/server.crt" "$CERTS_DIR/dh.pem" # Establece permisos de lectura para certificados
chmod 600 "$CERTS_DIR/ta.key" # Establece permiso restrictivo para la clave TLS

# Crear archivo README en el directorio de certificados
cat > "$CERTS_DIR/README.txt" << EOF
# OpenVPN Certificates Directory

Este directorio contiene todos los certificados y claves necesarios para OpenVPN.
Al montar este directorio como un volumen Docker, se mantiene la persistencia
de los certificados y claves incluso si el contenedor se elimina y recrea.

Contenido:
- ca.crt: Certificado de la Autoridad Certificadora
- server.crt: Certificado del servidor
- server.key: Clave privada del servidor
- dh.pem: Parametros Diffie-Hellman
- ta.key: Clave TLS Auth
- clients/: Directorio con certificados y configuraciones de clientes

Fecha de creacion: $(date)
EOF

# Aplicar los cambios en sysctl sin necesidad de reiniciar
echo "📡 Configurando reenvio de paquetes..."
if ! sysctl -w net.ipv4.ip_forward=1; then # Habilita el reenvio de paquetes
    handle_error "Error al habilitar el reenvio de paquetes"
fi
if ! sysctl -p; then # Aplica configuracion de sysctl
    handle_error "Error al aplicar la configuracion de sysctl"
fi

echo "📡 Configurando iptables para enrutar trafico de la VPN..."
# Modificar tablas de enrutamiento
if ! iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE; then # Configura NAT para eth0
    handle_error "Error al configurar iptables para eth0"
fi
if ! iptables -t nat -A POSTROUTING -o lo -j MASQUERADE; then # Configura NAT para loopback
    handle_error "Error al configurar iptables para lo"
fi

# Verificar reglas de iptables
echo "📜 Reglas de iptables aplicadas:"
if ! iptables -t nat -L -n -v; then # Muestra reglas de NAT aplicadas
    handle_error "Error al verificar las reglas de iptables"
fi

echo "✅ Configuracion de OpenVPN completada correctamente."
echo "🔒 Todos los certificados y claves se han almacenado en $CERTS_DIR"
echo "📝 Para montar este directorio como volumen Docker, anada la siguiente linea a su docker-compose.yml:"
echo "   volumes:"
echo "     - ./certs:/etc/openvpn/certs"
echo "     - ./logs:/var/log/openvpn"
