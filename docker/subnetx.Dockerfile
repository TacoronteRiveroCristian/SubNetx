# Dockerfile optimizado para SubnetX con VPN
FROM ubuntu:22.04

# Evitar interacciones durante la instalación
ENV DEBIAN_FRONTEND=noninteractive

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

# Exponer el puerto UDP por defecto para OpenVPN
EXPOSE 1194/udp

# Crear el usuario "subnetx", asignarle la contraseña y otorgarle permisos sudo.
RUN useradd -m subnetx && \
    echo "subnetx:subnetx" | chpasswd && \
    usermod -aG sudo subnetx && \
    echo "subnetx ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
    # echo "subnetx ALL=(ALL) ALL" >> /etc/sudoers

# Copiar los ficheros de configuracion para el servidor OpenVPN
COPY docker/config/openvpn/server.conf /etc/openvpn/server/server.conf
COPY docker/config/openvpn/sysctl.conf /etc/sysctl.conf

# Copiar estrcutura de ficheros
COPY app/bin/subnetx /usr/local/bin/subnetx
COPY app/config/ /app/config/
COPY app/scripts/ /app/scripts/

# Dar permisos iniciales para evitar problemas de acceso durante la configuracion
RUN chown -R subnetx:subnetx /app
RUN chmod +x /usr/local/bin/subnetx

# Comando por defecto para mantener el contenedor en ejecución
CMD ["sleep", "infinity"]

# Ejecutar como usuario "subnetx"
USER subnetx
