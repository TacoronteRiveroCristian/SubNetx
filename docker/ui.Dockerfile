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

# Copy all application files
COPY ui/ .

# Install dependencies
RUN npm install --omit=optional

# Create fix-permissions script
RUN echo '#!/bin/bash\n\
    chown -R node:node /app/node_modules\n\
    chmod -R 755 /app/node_modules\n\
    exec "$@"' > /usr/local/bin/fix-permissions.sh && \
    chmod +x /usr/local/bin/fix-permissions.sh

# Create startup script
RUN echo '#!/bin/bash\n\
    # Initialize database\n\
    npm run db:setup\n\
    # Start the application\n\
    exec npm run dev' > /usr/local/bin/start.sh && \
    chmod +x /usr/local/bin/start.sh

# Set entrypoint to fix permissions before running the command
ENTRYPOINT ["/usr/local/bin/fix-permissions.sh"]

# Default command
CMD ["/usr/local/bin/start.sh"]
