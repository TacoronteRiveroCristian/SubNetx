#!/bin/bash

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Configurando entorno de desarrollo para SubNetx VPN...${NC}"

# Instalar dependencias del sistema
echo -e "${GREEN}Instalando dependencias del sistema...${NC}"
apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    git

# Instalar dependencias de Python
echo -e "${GREEN}Instalando dependencias de Python...${NC}"
pip install --upgrade pip
pip install -e /app

# Configurar pre-commit hooks si existen
if [ -f "/app/.git/hooks/pre-commit" ]; then
    echo -e "${GREEN}Configurando pre-commit hooks...${NC}"
    chmod +x /app/.git/hooks/pre-commit
fi

# Crear directorios necesarios si no existen
echo -e "${GREEN}Creando directorios necesarios...${NC}"
mkdir -p /app/logs
mkdir -p /app/config

# Establecer permisos
echo -e "${GREEN}Estableciendo permisos...${NC}"
chown -R root:root /app

echo -e "${GREEN}¡Entorno de desarrollo configurado correctamente!${NC}"
echo -e "${YELLOW}Nota: El directorio de trabajo está en /app${NC}"

