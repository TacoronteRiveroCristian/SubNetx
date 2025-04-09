#!/bin/bash
# Descripción: Script para detener OpenVPN y eliminar todos los certificados y clientes.
# Este script permite reiniciar completamente la configuración de OpenVPN,
# eliminando todos los certificados, claves y configuraciones de clientes.
# Autor: SubNetx Team
# Versión: 1.0.0

# Función para manejar errores
handle_error() {
    echo "❌ Error: $1" # Muestra mensaje de error
    echo "❌ El proceso de reset no se completó correctamente." # Indica fallo en el reset
    exit 1 # Termina con código de error
}

echo "🔄 Iniciando proceso de reset de OpenVPN..."

# Detener el servidor OpenVPN si está en ejecución
echo "🛑 Deteniendo OpenVPN..."
if ! /app/scripts/openvpn/core/openvpn-stop.sh; then # Llama al script de detención
    handle_error "No se pudo detener el servidor OpenVPN"
fi
echo "✅ OpenVPN detenido correctamente."

# Verificar variables de entorno requeridas
required_vars=(
    "OPENVPN_DIR"
    "CERTS_DIR"
    "EASYRSA_DIR"
    "CLIENTS_DIR"
    "CCD_DIR"
    "SERVER_CONF_DIR"
)

missing_vars=() # Inicializa array para variables faltantes

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then # Verifica si la variable está vacía
        missing_vars+=("$var") # Añade variable faltante al array
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then # Si hay variables faltantes
    echo "❌ Faltan las siguientes variables de entorno:"
    printf '%s\n' "${missing_vars[@]}" # Imprime cada variable faltante
    exit 1 # Termina con error
fi

# Eliminar todos los certificados y claves de clientes
echo "🗑️ Eliminando certificados y claves de clientes..."

# Obtener lista de clientes
CLIENT_LIST=$(/app/scripts/client/openvpn-client-list.sh)

# Si hay clientes, eliminarlos uno por uno
if [ -n "$CLIENT_LIST" ]; then
    while IFS= read -r client; do
        echo "   🔥 Eliminando cliente: $client"
        if ! /app/scripts/client/openvpn-client-delete.sh "$client"; then
            echo "   ⚠️ Advertencia: Error al eliminar cliente $client, continuando con el proceso..."
        fi
    done <<< "$CLIENT_LIST"
    echo "   ✅ Todos los clientes han sido eliminados."
else
    echo "   ℹ️ No se encontraron clientes para eliminar."
fi

# Eliminar directorio de clientes
echo "🗑️ Eliminando directorio de clientes..."
if [ -d "$CLIENTS_DIR" ]; then
    rm -rf "$CLIENTS_DIR"/*
    echo "   ✅ Directorio de clientes limpiado: $CLIENTS_DIR"
fi

# Eliminar directorio CCD (Client Config Directory)
echo "🗑️ Eliminando directorio de configuración de clientes (CCD)..."
if [ -d "$CCD_DIR" ]; then
    rm -rf "$CCD_DIR"/*
    echo "   ✅ Directorio CCD limpiado: $CCD_DIR"
fi

# Eliminar certificados y claves del servidor
echo "🗑️ Eliminando certificados y claves del servidor..."
if [ -d "$CERTS_DIR" ]; then
    # Preservar el directorio pero eliminar contenido
    rm -rf "$CERTS_DIR"/* 2>/dev/null
    echo "   ✅ Certificados y claves del servidor eliminados: $CERTS_DIR"
fi

# Eliminar la PKI (Public Key Infrastructure)
echo "🗑️ Eliminando estructura PKI..."
if [ -d "$EASYRSA_DIR/pki" ]; then
    rm -rf "$EASYRSA_DIR/pki"
    echo "   ✅ Estructura PKI eliminada: $EASYRSA_DIR/pki"
fi

# Crear directorio para certificados si no existe
mkdir -p "$CERTS_DIR"
mkdir -p "$CERTS_DIR/clients"
mkdir -p "$CLIENTS_DIR"
mkdir -p "$CCD_DIR"

# Ajustar permisos
chmod 755 "$CERTS_DIR" "$CERTS_DIR/clients" "$CLIENTS_DIR" "$CCD_DIR"

echo "🧹 Limpiando configuración del servidor..."
# Eliminar archivo de configuración del servidor
if [ -f "$SERVER_CONF_DIR/server.conf" ]; then
    rm -f "$SERVER_CONF_DIR/server.conf"
    echo "   ✅ Configuración del servidor eliminada: $SERVER_CONF_DIR/server.conf"
fi

# Eliminar archivo de configuración JSON
if [ -f "$OPENVPN_DIR/vpn_config.json" ]; then
    rm -f "$OPENVPN_DIR/vpn_config.json"
    echo "   ✅ Archivo de configuración JSON eliminado: $OPENVPN_DIR/vpn_config.json"
fi

echo "✅ Reset de OpenVPN completado con éxito."
echo "📝 Ahora puede ejecutar openvpn-setup.sh para configurar OpenVPN nuevamente."
echo "🔒 Todos los certificados, claves y configuraciones de clientes han sido eliminados."

exit 0
