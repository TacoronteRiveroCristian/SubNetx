#!/bin/bash
set -e

# Función para verificar si las dependencias están correctamente instaladas
check_dependencies() {
  echo "🔍 Verificando dependencias..."

  # Verificar si node_modules existe
  if [ ! -d "/app/node_modules" ]; then
    echo "❌ Directorio node_modules no encontrado"
    return 1
  fi

  # Verificar si prisma está instalado y disponible
  if [ ! -f "/app/node_modules/.prisma/client/index.js" ] || [ ! -f "/app/node_modules/.bin/prisma" ]; then
    echo "❌ Prisma no está correctamente instalado"
    return 1
  fi

  # Verificar si next está instalado y disponible
  if [ ! -f "/app/node_modules/.bin/next" ]; then
    echo "❌ Next.js no está correctamente instalado"
    return 1
  fi

  # Todas las verificaciones pasaron
  echo "✅ Dependencias verificadas correctamente"
  return 0
}

# Función para instalar dependencias
install_dependencies() {
  echo "📦 Instalando dependencias..."

  # Asegurar permisos correctos
  chown -R node:node /app

  # Instalar dependencias
  npm install --omit=optional

  # Generar cliente Prisma
  npx prisma generate

  echo "✅ Dependencias instaladas correctamente"
}

# Verificar dependencias y reinstalar si es necesario
if ! check_dependencies; then
  echo "🔄 Reinstalando dependencias..."
  rm -rf /app/node_modules/* || true
  install_dependencies
fi

# Ajustar permisos
echo "🔒 Ajustando permisos..."
chown -R node:node /app/node_modules
chmod -R 755 /app/node_modules

# Ejecutar comando
echo "🚀 Ejecutando: $@"
exec "$@"
