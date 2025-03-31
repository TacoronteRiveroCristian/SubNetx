#!/bin/bash
# Descripcion: Configura OpenVPN, genera certificados, habilita el reenvio de paquetes y configura NAT.
# Acepta parametros mediante flags para mayor flexibilidad en su uso.

# Variables para almacenar los parametros
VPN_NETWORK="" # Direccion de red para la VPN
VPN_NETMASK="" # Mascara de red para la VPN
OPENVPN_PORT="" # Puerto para el servicio OpenVPN
OPENVPN_PROTO="" # Protocolo (udp/tcp)
TUN_DEVICE="" # Dispositivo TUN a utilizar
PUBLIC_IP="" # IP publica o nombre de dominio

# Funcion para manejar errores
handle_error() {
    echo "❌ Error: $1" # Muestra mensaje de error
    echo "❌ La configuracion no se completo correctamente." # Indica fallo en la configuracion
    exit 1 # Termina con codigo de error
}

# Funcion para mostrar ayuda
show_help() {
    echo "Uso: openvpn-setup.sh [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --red DIRECCION     Direccion de red VPN (ej. 10.8.0.0)"
    echo "  --mask MASCARA     Mascara de red VPN (ej. 255.255.255.0)"
    echo "  --port PUERTO      Puerto para OpenVPN (1-65535)"
    echo "  --proto PROTOCOLO  Protocolo (udp/tcp)"
    echo "  --tun DISPOSITIVO  Dispositivo TUN (ej. tun0)"
    echo "  --ip IP            IP publica o nombre de dominio"
    echo "  --help             Muestra esta ayuda"
    echo ""
    echo "Ejemplo:"
    echo "  openvpn-setup.sh --red 10.8.0.0 --mask 255.255.255.0 --port 1194 --proto udp --tun tun0 --ip miservidor.duckdns.org"
    exit 0
}

# Parsear argumentos
while [[ "$#" -gt 0 ]]; do # Para cada argumento en la linea de comandos
    case "$1" in
        --red) # Si el argumento es --red
            VPN_NETWORK="$2" # Asigna el siguiente argumento como direccion de red
            shift 2 # Avanza dos posiciones
            ;;
        --mask) # Si el argumento es --mask
            VPN_NETMASK="$2" # Asigna el siguiente argumento como mascara de red
            shift 2 # Avanza dos posiciones
            ;;
        --port) # Si el argumento es --port
            OPENVPN_PORT="$2" # Asigna el siguiente argumento como puerto
            shift 2 # Avanza dos posiciones
            ;;
        --proto) # Si el argumento es --proto
            OPENVPN_PROTO="$2" # Asigna el siguiente argumento como protocolo
            shift 2 # Avanza dos posiciones
            ;;
        --tun) # Si el argumento es --tun
            TUN_DEVICE="$2" # Asigna el siguiente argumento como dispositivo TUN
            shift 2 # Avanza dos posiciones
            ;;
        --ip) # Si el argumento es --ip
            PUBLIC_IP="$2" # Asigna el siguiente argumento como IP publica
            shift 2 # Avanza dos posiciones
            ;;
        --help) # Si el argumento es --help
            show_help # Muestra la ayuda
            ;;
        *) # Si es cualquier otro argumento
            echo "❌ Error: Opcion desconocida $1" # Muestra error
            echo "Por favor, consulte la ayuda con --help para mas informacion."
            /app/scripts/utils/openvpn-help.sh # Muestra ayuda
            exit 1 # Termina con error
            ;;
    esac
done

# Validar parametros
missing_params=() # Inicializa array para parametros faltantes

if [ -z "$VPN_NETWORK" ]; then # Si falta la direccion de red
    missing_params+=("--red") # Añade a la lista de faltantes
fi
if [ -z "$VPN_NETMASK" ]; then # Si falta la mascara de red
    missing_params+=("--mask") # Añade a la lista de faltantes
fi
if [ -z "$OPENVPN_PORT" ]; then # Si falta el puerto
    missing_params+=("--port") # Añade a la lista de faltantes
fi
if [ -z "$OPENVPN_PROTO" ]; then # Si falta el protocolo
    missing_params+=("--proto") # Añade a la lista de faltantes
fi
if [ -z "$TUN_DEVICE" ]; then # Si falta el dispositivo TUN
    missing_params+=("--tun") # Añade a la lista de faltantes
fi
if [ -z "$PUBLIC_IP" ]; then # Si falta la IP publica
    missing_params+=("--ip") # Añade a la lista de faltantes
fi

if [ ${#missing_params[@]} -ne 0 ]; then # Si hay parametros faltantes
    echo "❌ Faltan los siguientes parametros:"
    printf '  %s\n' "${missing_params[@]}" # Imprime cada parametro faltante
    echo "Por favor, consulte la ayuda con --help para mas informacion."
    /app/scripts/utils/openvpn-help.sh # Muestra ayuda
    exit 1 # Termina con error
fi

# Validar que las rutas necesarias esten definidas como variables de entorno
required_path_vars=(
    "OPENVPN_DIR"
    "CERTS_DIR"
    "SERVER_CONF_DIR"
    "EASYRSA_DIR"
    "LOGS_DIR"
)

missing_path_vars=() # Inicializa array para variables de ruta faltantes

for var in "${required_path_vars[@]}"; do
    if [ -z "${!var}" ]; then # Verifica si la variable esta vacia
        missing_path_vars+=("$var") # Anade variable faltante al array
    fi
done

if [ ${#missing_path_vars[@]} -ne 0 ]; then # Si hay variables de ruta faltantes
    echo "❌ Faltan las siguientes variables de entorno para rutas:"
    printf '%s\n' "${missing_path_vars[@]}" # Imprime cada variable faltante
    handle_error "Estas variables de ruta deben estar definidas en el Dockerfile o en el entorno"
fi

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
SERVER_TEMPLATE="/app/config/server.conf.template" # Ruta al template

# Verificar que el template existe
if [ ! -f "$SERVER_TEMPLATE" ]; then # Verifica si existe el archivo template
    handle_error "No se encontro el template de server.conf: $SERVER_TEMPLATE"
fi

# Crear directorio para la configuracion del servidor si no existe
mkdir -p "$SERVER_CONF_DIR" # Crea el directorio para la configuracion

# Utilizar sed para reemplazar los placeholders con los parametros proporcionados
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
