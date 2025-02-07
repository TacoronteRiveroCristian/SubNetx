#!/bin/bash
# Descripcion: Configura OpenVPN, genera certificados, habilita el reenvío de paquetes y configura NAT.

echo "🛠️ Configurando OpenVPN..."

# Definir rutas
DIR_OPENVPN="/etc/openvpn"
DIR_EASYRSA="${DIR_OPENVPN}/easy-rsa"

# Crear directorio de Easy-RSA si no existe
if [ ! -d "$DIR_EASYRSA" ]; then
    echo "📂 Creando directorio Easy-RSA..."
    sudo make-cadir "$DIR_EASYRSA"
    sudo chmod -R 755 "$DIR_EASYRSA"
else
    echo "✅ Directorio Easy-RSA ya existe."
fi

# Moverse al directorio Easy-RSA
cd "$DIR_EASYRSA" || { echo "❌ Error: No se pudo acceder a $DIR_EASYRSA"; exit 1; }

# Inicializar la PKI si no existe
if [ ! -d "$DIR_EASYRSA/pki" ]; then
    echo "🔑 Inicializando PKI..."
    sudo ./easyrsa --batch init-pki
fi

# Crear la CA si no existe
if [ ! -f "$DIR_OPENVPN/ca.crt" ]; then
    echo "🔏 Generando Autoridad de Certificación (CA)..."
    sudo ./easyrsa --batch build-ca nopass
    sudo cp pki/ca.crt "$DIR_OPENVPN/"
fi

# Crear clave y certificado del servidor si no existen
if [ ! -f "$DIR_OPENVPN/server.crt" ]; then
    echo "🔐 Generando clave y certificado del servidor..."
    sudo ./easyrsa --batch gen-req server nopass
    echo "yes" | sudo ./easyrsa --batch sign-req server server
    sudo cp pki/private/server.key "$DIR_OPENVPN/"
    sudo cp pki/issued/server.crt "$DIR_OPENVPN/"
fi

# Generar Diffie-Hellman si no existe
if [ ! -f "$DIR_OPENVPN/dh.pem" ]; then
    echo "🔀 Generando Diffie-Hellman..."
    sudo ./easyrsa gen-dh
    sudo cp pki/dh.pem "$DIR_OPENVPN/"
fi

# Generar clave TLS si no existe
if [ ! -f "$DIR_OPENVPN/ta.key" ]; then
    echo "🔑 Generando clave TLS..."
    sudo openvpn --genkey secret "$DIR_OPENVPN/ta.key"
fi

# Aplicar los cambios en sysctl sin necesidad de reiniciar
sudo sysctl -p

echo "📡 Configurando iptables para enrutar tráfico de la VPN..."
# Modificar tablas de enrutamiento
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -t nat -A POSTROUTING -o lo -j MASQUERADE

# Verificar reglas de iptables
echo "📜 Reglas de iptables aplicadas:"
sudo iptables -t nat -L -n -v

echo "✅ Configuración de OpenVPN completada correctamente."
