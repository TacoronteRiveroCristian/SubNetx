# UI Development Dockerfile
FROM node:20

# Create app directory
WORKDIR /app

# Install global tools
RUN npm install -g npm

# Copy package files
COPY ui/package*.json ./

# Install dependencies
RUN npm install --omit=optional

# Expose port used by Next.js
EXPOSE 3200

# Default command
CMD ["npm", "run", "dev"]
