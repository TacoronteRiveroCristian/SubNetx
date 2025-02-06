#!/bin/bash
# Descripcion: Configura OpenVPN copiando la configuracion y generando certificados si es necesario.

echo "Configurando OpenVPN..."

# Crear el directorio de configuracion de OpenVPN si no existe
sudo mkdir -p "$OPENVPN_DIR"

# Copiar el archivo de configuracion del servidor
echo "Actualizando $_SERVER_CONF.conf a $SERVER_CONF..."
sudo cp "$BASE_DIR/app/config/openvpn/server.conf" "$SERVER_CONF"

# Crear directorio de Easy-RSA si no existe
if [ ! -d "$EASYRSA_DIR" ]; then
    echo "Creando directorio para Easy-RSA..."
    sudo make-cadir "$EASYRSA_DIR"
    sudo chmod -R 755 "$EASYRSA_DIR"
fi

echo "Actualizando configuracion $_EASYRSA_VAR a $EASYRSA_VAR"
# Eliminar fichero vars para reemplazarlo por el nuevo
if [ -d "EASYRSA_VAR" ]; then
    sudo rm "$EASYRSA_VAR"
fi
sudo cp "$_EASYRSA_VAR" "$EASYRSA_VAR"

cd "$EASYRSA_DIR" || exit 1

# Inicializar la PKI si no existe
if [ ! -d "$EASYRSA_DIR/pki" ]; then
    echo "Inicializando PKI..."
    sudo ./easyrsa init-pki
fi

# Crear la CA si no existe
if [ ! -f "$OPENVPN_DIR/ca.crt" ]; then
    echo "Generando CA..."
    sudo ./easyrsa --batch build-ca nopass
    sudo cp pki/ca.crt "$OPENVPN_DIR/"
fi

# Crear clave y certificado del servidor si no existen
if [ ! -f "$OPENVPN_DIR/server.crt" ]; then
    echo "Generando clave y certificado del servidor..."
    sudo ./easyrsa gen-req server nopass
    sudo ./easyrsa sign-req server server <<EOF
yes
EOF
    sudo cp pki/private/server.key "$OPENVPN_DIR/"
    sudo cp pki/issued/server.crt "$OPENVPN_DIR/"
fi

# Generar Diffie-Hellman si no existe
if [ ! -f "$OPENVPN_DIR/dh.pem" ]; then
    echo "Generando Diffie-Hellman..."
    sudo ./easyrsa gen-dh
    sudo cp pki/dh.pem "$OPENVPN_DIR/"
fi

# Generar clave TLS si no existe
if [ ! -f "$OPENVPN_DIR/ta.key" ]; then
    echo "Generando clave TLS..."
    sudo openvpn --genkey secret "$OPENVPN_DIR/ta.key"
fi

echo "Configuracion de OpenVPN completada."
