# .devcontainer/Dockerfile
FROM node:20

# Create app directory
WORKDIR /app

# Install global tools (optional)
RUN npm install -g npm

# Copy files separately to optimize cache
COPY ui/package.json ./
COPY ui/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy rest of the app
COPY ui/ .

# Expose port
EXPOSE 3200

# Default command
CMD ["npm", "run", "dev"]
