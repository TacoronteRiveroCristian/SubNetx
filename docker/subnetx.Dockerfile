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

# Establecer el directorio de trabajo
WORKDIR /workspaces/SubNetX

# Comando por defecto para mantener el contenedor en ejecución
CMD ["sleep", "infinity"]

# Ejecutar como usuario "subnetx"
USER subnetx
