#!/bin/bash
# Descripcion: Configura OpenVPN, genera certificados, habilita el reenvío de paquetes y configura NAT.

echo "🛠️ Configurando OpenVPN..."

# Crear directorio de clientes si no existe
if [ ! -d "$OPENVPN_DIR/ccd" ]; then
    echo "📂 Creando directorio de clientes..."
    mkdir -p "$OPENVPN_DIR/ccd"
else
    echo "✅ Directorio de clientes ya existe."
fi

# Crear directorio de Easy-RSA si no existe
if [ ! -d "$EASYRSA_DIR" ]; then
    echo "📂 Creando directorio Easy-RSA..."
    make-cadir "$EASYRSA_DIR"
    chmod -R 755 "$EASYRSA_DIR"
else
    echo "✅ Directorio Easy-RSA ya existe."
fi

# Moverse al directorio Easy-RSA
cd "$EASYRSA_DIR" || { echo "❌ Error: No se pudo acceder a $EASYRSA_DIR"; exit 1; }

# Inicializar la PKI si no existe
if [ ! -d "$EASYRSA_DIR/pki" ]; then
    echo "🔑 Inicializando PKI..."
    ./easyrsa --batch init-pki
fi

# Crear la CA si no existe
if [ ! -f "$OPENVPN_DIR/ca.crt" ]; then
    echo "🔏 Generando Autoridad de Certificación (CA)..."
    ./easyrsa --batch build-ca nopass
    cp pki/ca.crt "$OPENVPN_DIR/"
fi

# Crear clave y certificado del servidor si no existen
if [ ! -f "$OPENVPN_DIR/server.crt" ]; then
    echo "🔐 Generando clave y certificado del servidor..."
    ./easyrsa --batch gen-req server nopass
    echo "yes" | ./easyrsa --batch sign-req server server
    cp pki/private/server.key "$OPENVPN_DIR/"
    cp pki/issued/server.crt "$OPENVPN_DIR/"
fi

# Generar Diffie-Hellman si no existe
if [ ! -f "$OPENVPN_DIR/dh.pem" ]; then
    echo "🔀 Generando Diffie-Hellman..."
    ./easyrsa gen-dh
    cp pki/dh.pem "$OPENVPN_DIR/"
fi

# Generar clave TLS si no existe
if [ ! -f "$OPENVPN_DIR/ta.key" ]; then
    echo "🔑 Generando clave TLS..."
    openvpn --genkey secret "$OPENVPN_DIR/ta.key"
fi

# Aplicar los cambios en sysctl sin necesidad de reiniciar
sysctl -p

echo "📡 Configurando iptables para enrutar tráfico de la VPN..."
# Modificar tablas de enrutamiento
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -t nat -A POSTROUTING -o lo -j MASQUERADE

# Verificar reglas de iptables
echo "📜 Reglas de iptables aplicadas:"
iptables -t nat -L -n -v

echo "✅ Configuración de OpenVPN completada correctamente."
