# Dockerfile optimizado para SubnetX con VPN
FROM ubuntu:22.04

# Evitar interacciones durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

# Definir variables de entorno base
ENV OPENVPN_DIR="/etc/openvpn"
ENV EASYRSA_DIR="/etc/openvpn/easy-rsa"

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

# Copiar fichero de configuracion de red para OpenVPN
COPY docker/config/openvpn/sysctl.conf /etc/sysctl.conf

# Copiar estrcutura de ficheros
COPY app/bin/subnetx /usr/local/bin/subnetx
COPY app/config/ /app/config/
COPY app/scripts/ /app/scripts/

# Dar permisos iniciales para evitar problemas de acceso durante la configuracion
RUN chmod +x /usr/local/bin/subnetx

# Comando por defecto para mantener el contenedor en ejecución
CMD ["sleep", "infinity"]
