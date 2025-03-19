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
    SERVER_CONF_DIR="/etc/openvpn/server"

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
    net-tools && \
    rm -rf /var/lib/apt/lists/*

# Crear estructura de directorios para OpenVPN
RUN mkdir -p ${CERTS_DIR} ${CCD_DIR} ${CLIENTS_DIR} ${LOGS_DIR} ${SERVER_CONF_DIR} && \
    chmod -R 755 ${OPENVPN_DIR} && \
    touch ${LOGS_DIR}/openvpn.log ${LOGS_DIR}/status.log && \
    chmod 644 ${LOGS_DIR}/openvpn.log ${LOGS_DIR}/status.log

# Copiar fichero de configuracion de red para OpenVPN
COPY docker/config/openvpn/sysctl.conf /etc/sysctl.conf

# Copiar estrcutura de ficheros
COPY app/bin/subnetx /usr/local/bin/subnetx
COPY app/config/ /app/config/
COPY app/scripts/ /app/scripts/

# Dar permisos iniciales para evitar problemas de acceso durante la configuracion
RUN chmod +x /usr/local/bin/subnetx /app/scripts/*.sh

# Comando por defecto para mantener el contenedor en ejecución
CMD ["sleep", "infinity"]
