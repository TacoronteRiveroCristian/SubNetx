#!/bin/bash
# Descripcion: Elimina un cliente OpenVPN, revocando su certificado y eliminando todos sus archivos.
# Usa las variables de entorno definidas en el Dockerfile para mantener coherencia.

# Validar que se ha proporcionado un nombre de cliente
if [ -z "$1" ]; then # Si no se proporciona el nombre del cliente
    echo "❌ Error: Debes especificar el nombre del cliente a eliminar."
    echo "Uso: $0 <nombre_cliente>"
    exit 1 # Termina con error
fi

CLIENT_NAME="$1" # Nombre del cliente a eliminar

echo "🔒 Revocando certificado y eliminando cliente: $CLIENT_NAME"

# Verificar si el cliente existe
if [ ! -f "$EASYRSA_DIR/pki/issued/$CLIENT_NAME.crt" ]; then # Si no existe el certificado
    echo "❌ Error: El cliente $CLIENT_NAME no existe o su certificado no fue encontrado."
    exit 1 # Termina con error
fi

# Revocar el certificado del cliente
cd "$EASYRSA_DIR" || { # Cambia al directorio Easy-RSA
    echo "❌ Error: No se pudo acceder al directorio $EASYRSA_DIR"
    exit 1 # Termina con error
}

echo "🔐 Revocando certificado..."
if ! ./easyrsa --batch revoke "$CLIENT_NAME"; then # Revoca el certificado
    echo "⚠️ Advertencia: Error al revocar el certificado. Continuando con la eliminacion de archivos."
fi

# Generar una nueva CRL (Certificate Revocation List)
echo "🔄 Actualizando lista de certificados revocados (CRL)..."
if ! ./easyrsa gen-crl; then # Genera la CRL
    echo "⚠️ Advertencia: Error al generar la CRL. Continuando con la eliminacion de archivos."
else
    # Copiar la CRL al directorio de certificados
    cp -f "$EASYRSA_DIR/pki/crl.pem" "$CERTS_DIR/" # Copia la CRL al directorio de certificados
    echo "✅ CRL actualizada correctamente."
fi

# Eliminar archivos del cliente
echo "🗑️ Eliminando archivos del cliente..."

# Eliminar configuracion especifica del cliente (CCD)
if [ -f "$CCD_DIR/$CLIENT_NAME" ]; then # Si existe el archivo CCD
    rm -f "$CCD_DIR/$CLIENT_NAME" # Elimina el archivo CCD
    echo "✅ Configuracion CCD eliminada."
fi

# Eliminar archivo .ovpn
if [ -f "$CLIENTS_DIR/$CLIENT_NAME.ovpn" ]; then # Si existe el archivo de configuracion
    rm -f "$CLIENTS_DIR/$CLIENT_NAME.ovpn" # Elimina el archivo de configuracion
    echo "✅ Archivo de configuracion .ovpn eliminado."
fi

# Eliminar directorio del cliente en el directorio centralizado
if [ -d "$CERTS_DIR/clients/$CLIENT_NAME" ]; then # Si existe el directorio del cliente
    rm -rf "$CERTS_DIR/clients/$CLIENT_NAME" # Elimina el directorio del cliente
    echo "✅ Directorio de certificados del cliente eliminado de: $CERTS_DIR/clients/$CLIENT_NAME"
fi

echo "✅ Cliente $CLIENT_NAME eliminado correctamente."
echo "📝 Nota: Si el servidor OpenVPN estaba en ejecucion, debera reiniciarlo para aplicar los cambios de revocacion."
