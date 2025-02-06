#!/bin/bash
# Descripción: Inicia el servidor OpenVPN y, si no existen, genera automaticamente los certificados necesarios.

# Ruta donde se esperan los certificados y claves
CERT_DIR="/etc/openvpn"

# Ruta temporal para Easy-RSA
EASYRSA_DIR="/etc/openvpn/easy-rsa"

# Verifica si ya existe el certificado de la CA; si no, genera los certificados.
if [ ! -f "$CERT_DIR/ca.crt" ]; then
    echo "No se encontraron certificados, generando la PKI y certificados..."

    # Crea la carpeta para Easy-RSA y copia los archivos base (en Ubuntu se suelen encontrar en /usr/share/easy-rsa)
    mkdir -p "$EASYRSA_DIR"
    cp -r /usr/share/easy-rsa/* "$EASYRSA_DIR"
    cd "$EASYRSA_DIR" || exit 1

    # Inicializa la PKI
    ./easyrsa init-pki

    # Construye la CA sin contraseña de forma no interactiva
    ./easyrsa --batch build-ca nopass

    # Genera la petición (req) del certificado del servidor sin contraseña
    ./easyrsa gen-req server nopass

    # Firma la petición para generar el certificado del servidor
    ./easyrsa sign-req server server <<EOF
yes
EOF

    # Genera los parámetros Diffie-Hellman
    ./easyrsa gen-dh

    # Genera el archivo de clave TLS (ta.key)
    openvpn --genkey --secret "$CERT_DIR/ta.key"

    # Copia los archivos generados a la carpeta de OpenVPN
    cp pki/ca.crt "$CERT_DIR/ca.crt"
    cp pki/issued/server.crt "$CERT_DIR/server.crt"
    cp pki/private/server.key "$CERT_DIR/server.key"
    cp pki/dh.pem "$CERT_DIR/dh.pem"

    echo "Certificados generados y copiados a $CERT_DIR"
else
    echo "Certificados ya existen. Continuando..."
fi

# Finalmente, inicia el servidor OpenVPN con la configuración definida en server.conf
echo "Iniciando OpenVPN..."
sudo openvpn --config "$CERT_DIR/server.conf"
