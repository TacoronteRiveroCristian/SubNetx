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
    lsb-release \
    supervisor \
    jq && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python para metrics
COPY services/vpn/requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Establecer directorio de trabajo
WORKDIR /app

# Crear estructura de directorios para OpenVPN
RUN mkdir -p ${CERTS_DIR} ${CCD_DIR} ${CLIENTS_DIR} ${LOGS_DIR} ${SERVER_CONF_DIR} && \
    chmod -R 755 ${OPENVPN_DIR} && \
    touch ${LOGS_DIR}/openvpn.log ${LOGS_DIR}/status.log && \
    chmod 644 ${LOGS_DIR}/openvpn.log ${LOGS_DIR}/status.log

# Crear estructura de directorios para scripts
RUN mkdir -p /app/scripts/{metrics,openvpn}

# Copiar estructura de archivos
COPY services/vpn/ /app/
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Dar permisos iniciales para evitar problemas de acceso durante la configuracion
RUN chmod -R 755 /app/scripts && \
    chmod -R 755 /app/config

# Crear directorio de logs
RUN mkdir -p /var/log

# Establecer punto de entrada a supervisor
ENTRYPOINT ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
