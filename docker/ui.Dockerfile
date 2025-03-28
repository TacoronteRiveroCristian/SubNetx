# Use Node.js 20 LTS as base image
FROM node:20-slim

# Install necessary build tools and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    lsof \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy package files
COPY ui/package*.json ./

# Install dependencies
RUN npm install --omit=optional

# Copy the rest of the application
COPY ui/ .

# Create fix-permissions script
RUN echo '#!/bin/bash\n\
chown -R node:node /app/node_modules\n\
chmod -R 755 /app/node_modules\n\
exec "$@"' > /usr/local/bin/fix-permissions.sh && \
    chmod +x /usr/local/bin/fix-permissions.sh

# Set entrypoint to fix permissions before running the command
ENTRYPOINT ["/usr/local/bin/fix-permissions.sh"]

# Default command
CMD ["npm", "run", "dev"]
