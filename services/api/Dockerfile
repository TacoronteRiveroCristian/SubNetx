# Base image with Python 3.12
FROM python:3.12-slim

# Install PostgreSQL client and dependency packages
RUN apt-get update && apt-get install -y \
    iputils-ping \
    procps \
    net-tools \
    lsof \
    postgresql-client \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory in container
WORKDIR /app

# Upgrade pip and install dev dependencies
RUN pip install --upgrade pip && \
    pip install flake8 isort black mypy pylint

# Install dependencies
COPY services/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
CMD ["/bin/bash"]
