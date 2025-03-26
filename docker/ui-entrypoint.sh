#!/bin/bash
set -e

echo "Starting UI container with user: $(id -u):$(id -g)"

# Asegurar que los directorios tienen los permisos correctos
mkdir -p /workspace/ui/node_modules
chown -R node:node /workspace/ui

# Verificar si necesitamos instalar dependencias
if [ ! -d "/workspace/ui/node_modules/react" ]; then
  echo "Installing dependencies..."
  sudo -u node npm install
fi

# Ejecutar el comando como usuario node
exec sudo -E -u node "$@"
