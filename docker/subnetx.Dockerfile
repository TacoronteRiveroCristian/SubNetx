# Dockerfile optimizado para SubnetX con VPN
FROM ubuntu:22.04

# Evitar interacciones durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Definir todas las variables de entorno y paths fijos
ENV OPENVPN_DIR="/etc/openvpn" \
    EASYRSA_DIR="/etc/openvpn/easy-rsa" \
    CERTS_DIR="/etc/openvpn/certs" \
    CCD_DIR="/etc/openvpn/ccd" \
    CLIENTS_DIR="/etc/openvpn/clients" \
    LOGS_DIR="/var/log/openvpn" \
    OPENVPN_PID_FILE="/etc/openvpn/openvpn.pid" \
    SERVER_CONF_DIR="/etc/openvpn/server" \
    WORK_DIR="/app" \
    PYTHONPATH="/app"

# Actualizar e instalar paquetes necesarios sin recomendaciones extras
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openvpn \
    easy-rsa \
    expect \
    iptables \
    socat \
    curl \
    sudo \
    nano \
    git \
    iputils-ping \
    whiptail \
    net-tools \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    wget \
    bash-completion \
    lsb-release && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python para metrics
COPY vpn/metrics/requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Crear estructura de directorios para OpenVPN
RUN mkdir -p ${CERTS_DIR} ${CCD_DIR} ${CLIENTS_DIR} ${LOGS_DIR} ${SERVER_CONF_DIR} && \
    chmod -R 755 ${OPENVPN_DIR} && \
    touch ${LOGS_DIR}/openvpn.log ${LOGS_DIR}/status.log && \
    chmod 644 ${LOGS_DIR}/openvpn.log ${LOGS_DIR}/status.log

# Copiar estructura de archivos
COPY vpn/openvpn/src/subnetx /usr/local/bin/subnetx
COPY vpn/openvpn/config /app/config/
COPY vpn/openvpn/src/*.sh /app/scripts/

# Mover fichero de configuracion de red para OpenVPN
RUN mv /app/config/sysctl.conf /etc/sysctl.conf

# Dar permisos iniciales para evitar problemas de acceso durante la configuracion
RUN chmod +x /usr/local/bin/subnetx /app/scripts/*.sh

# Comando por defecto para mantener el contenedor en ejecución
CMD ["sleep", "infinity"]
