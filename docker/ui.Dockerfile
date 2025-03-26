# Usar una imagen base de Node.js
FROM node:20-slim

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y \
    git \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Actualizar npm a la última versión
RUN npm install -g npm@latest

# Establecer el directorio de trabajo
WORKDIR /workspace/ui

# Copiar el script de entrypoint
COPY docker/ui-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Dar permisos al usuario node para escribir en el directorio de trabajo
RUN mkdir -p /workspace/ui/node_modules && \
    chown -R node:node /workspace/ui && \
    echo "node ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/node

# Exponer el puerto de desarrollo
EXPOSE 3000

# Configurar el entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Comando predeterminado
CMD ["npm", "run", "dev"]
