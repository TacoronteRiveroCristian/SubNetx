# Use Node.js 20 LTS as base image
FROM node:20-slim

# Install necessary build tools and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    lsof \
    procps \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Configure sudo without password
RUN echo "ALL ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create app directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
COPY prisma ./prisma/

# Copy the entrypoint script
COPY scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Install dependencies only if not using volume mount
# This will be overridden by the entrypoint script when using volume mounts
RUN npm install --omit=optional && \
    npx prisma generate

# Copy the rest of the application
COPY . .

# Create startup script
RUN echo '#!/bin/bash\n\
    # Initialize database\n\
    npm run db:setup\n\
    # Start the application\n\
    exec npm run dev' > /usr/local/bin/start.sh && \
    chmod +x /usr/local/bin/start.sh

# Set entrypoint to the new script
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["/usr/local/bin/start.sh"]
